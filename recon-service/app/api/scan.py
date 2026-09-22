"""
AttackGraphX Recon Service — Scan API Endpoints
================================================

Endpoints:
  POST /scan             - Trigger an on-demand background scan
  GET  /scan/{scan_id}   - Get status of a specific scan
  GET  /scans            - List all scans (most recent first)
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from app.models.scan_models import (
    ScanRequest,
    ScanResponse,
    ScanStatus,
)
from app.scanner.nmap_runner import InvalidTargetError, validate_target

logger = logging.getLogger(__name__)

router = APIRouter(tags=["scan"])

# ─── In-Memory Scan Store ─────────────────────────────────────────────────────
# Simple dict: scan_id → ScanStatus
# Sufficient for project scope. Replace with Redis/DB for production.
_scan_store: dict[str, ScanStatus] = {}


# ─── Internal Pipeline ───────────────────────────────────────────────────────

async def _run_scan_pipeline(scan_id: str, target: str) -> None:
    """
    Full scan pipeline: Nmap → Parse → Normalize → Validate → Publish.

    Runs as a FastAPI BackgroundTask (non-blocking).
    Updates _scan_store throughout for status tracking.
    """
    from app.normalizer.normalizer import normalize
    from app.publisher.redis_publisher import RedisPublishError, publish_scan_result
    from app.scanner.nmap_runner import (
        NmapExecutionError,
        NmapNotFoundError,
        NmapTimeoutError,
        run_nmap,
    )
    from app.scanner.xml_parser import XmlParseError, parse_nmap_xml

    # ── Mark as running ────────────────────────────────────────────────────
    _scan_store[scan_id].status = "running"
    _scan_store[scan_id].started_at = datetime.now(UTC)
    logger.info("Scan pipeline started | scan_id=%s | target=%s", scan_id, target)

    try:
        # STEP 1: Run Nmap
        xml_output = await asyncio.to_thread(run_nmap, target)

        # STEP 2: Parse XML
        parsed_hosts = parse_nmap_xml(xml_output)

        # STEP 3: Normalize → Pydantic ScanResult
        scan_result = normalize(
            parsed_hosts=parsed_hosts,
            target_scope=target,
            scan_id=scan_id,
        )

        # STEP 4: Update status with preliminary counts
        _scan_store[scan_id].hosts_found = len(scan_result.hosts)
        _scan_store[scan_id].services_found = sum(
            len(h.services) for h in scan_result.hosts
        )

        # STEP 5: Publish to Redis
        await publish_scan_result(scan_result)
        _scan_store[scan_id].redis_published = True

        # ── Complete ───────────────────────────────────────────────────────
        _scan_store[scan_id].status = "completed"
        _scan_store[scan_id].completed_at = datetime.now(UTC)

        logger.info(
            "Scan complete | scan_id=%s | hosts=%d | services=%d | redis=published",
            scan_id,
            _scan_store[scan_id].hosts_found,
            _scan_store[scan_id].services_found,
        )

        # Track last successful scan time globally
        from app.main import _state
        _state["last_successful_scan"] = datetime.now(UTC)

    except (NmapNotFoundError, NmapExecutionError, NmapTimeoutError) as exc:
        _scan_store[scan_id].status = "failed"
        _scan_store[scan_id].completed_at = datetime.now(UTC)
        _scan_store[scan_id].error = f"Scanner error: {exc}"
        logger.error("Nmap error | scan_id=%s | error=%s", scan_id, exc)

    except XmlParseError as exc:
        _scan_store[scan_id].status = "failed"
        _scan_store[scan_id].completed_at = datetime.now(UTC)
        _scan_store[scan_id].error = f"XML parse error: {exc}"
        logger.error("XML parse error | scan_id=%s | error=%s", scan_id, exc)

    except RedisPublishError as exc:
        # Scan succeeded but Redis publish failed — log clearly
        _scan_store[scan_id].status = "failed"
        _scan_store[scan_id].completed_at = datetime.now(UTC)
        _scan_store[scan_id].error = f"Redis publish failed: {exc}"
        _scan_store[scan_id].redis_published = False
        logger.error("Redis publish failed | scan_id=%s | error=%s", scan_id, exc)

    except Exception as exc:  # noqa: BLE001
        _scan_store[scan_id].status = "failed"
        _scan_store[scan_id].completed_at = datetime.now(UTC)
        _scan_store[scan_id].error = f"Unexpected error: {type(exc).__name__}: {exc}"
        logger.exception("Unexpected error in scan pipeline | scan_id=%s", scan_id)


def get_scan_store() -> dict[str, ScanStatus]:
    """Expose scan store for health endpoint and tests."""
    return _scan_store


def queue_scan(scan_id: str, target: str, background_tasks: BackgroundTasks) -> None:
    """
    Create a ScanStatus entry and queue the pipeline as a background task.
    Called by POST /scan and the scheduler.
    """
    _scan_store[scan_id] = ScanStatus(
        scan_id=scan_id,
        status="queued",
        target=target,
    )
    background_tasks.add_task(_run_scan_pipeline, scan_id, target)
    logger.info("Scan queued | scan_id=%s | target=%s", scan_id, target)


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post(
    "/scan",
    response_model=ScanResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger an on-demand scan",
    description=(
        "Initiates an Nmap scan of the specified target. "
        "Target must be within the authorized lab CIDR range. "
        "The scan runs asynchronously — poll GET /scan/{scan_id} for status."
    ),
)
async def trigger_scan(
    request: ScanRequest,
    background_tasks: BackgroundTasks,
) -> ScanResponse:
    # ── Validate target ───────────────────────────────────────────────────
    try:
        validate_target(request.target)
    except InvalidTargetError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    # ── Generate scan ID ──────────────────────────────────────────────────
    from app.normalizer.normalizer import generate_scan_id
    scan_id = generate_scan_id()

    # ── Queue background task ─────────────────────────────────────────────
    queue_scan(scan_id, request.target, background_tasks)

    return ScanResponse(
        scan_id=scan_id,
        status="queued",
        message=f"Scan queued for target '{request.target}'. "
                f"Check status at GET /scan/{scan_id}",
    )


@router.get(
    "/scan/{scan_id}",
    response_model=ScanStatus,
    summary="Get scan status",
    description="Retrieve the current status and results summary for a specific scan.",
)
async def get_scan_status(scan_id: str) -> ScanStatus:
    scan = _scan_store.get(scan_id)
    if scan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan '{scan_id}' not found.",
        )
    return scan


@router.get(
    "/scans",
    response_model=list[ScanStatus],
    summary="List all scans",
    description="Return all scan records, most recent first (up to 100).",
)
async def list_scans() -> list[ScanStatus]:
    all_scans = list(_scan_store.values())
    # Sort by started_at descending, None values go last
    all_scans.sort(
        key=lambda s: s.started_at or datetime.min.replace(tzinfo=UTC),
        reverse=True,
    )
    return all_scans[:100]
