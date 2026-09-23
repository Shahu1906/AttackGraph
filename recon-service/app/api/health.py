"""
AttackGraphX Recon Service — Health Endpoint
=============================================

GET /health — Returns service health status including:
  - scanner: Whether nmap is installed and available
  - redis: Whether Redis is reachable
  - last_successful_scan: Timestamp of last scan that completed and published
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.models.scan_models import HealthResponse
from app.publisher.redis_publisher import check_redis_connection
from app.scanner.nmap_runner import is_nmap_available

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service health check",
    description=(
        "Returns the operational status of the Recon Service. "
        "Checks nmap availability and Redis connectivity. "
        "Does NOT initiate a scan."
    ),
)
async def health_check() -> JSONResponse:
    from app.main import _state

    # Check scanner availability (sync, fast — just checks PATH)
    scanner_ok = is_nmap_available()

    # Check Redis connectivity (async PING)
    redis_ok = await check_redis_connection()

    overall_status = "healthy" if (scanner_ok and redis_ok) else "degraded"

    response = HealthResponse(
        status=overall_status,
        scanner="available" if scanner_ok else "unavailable",
        redis="connected" if redis_ok else "disconnected",
        last_successful_scan=_state.get("last_successful_scan"),
    )

    http_status = 200 if overall_status == "healthy" else 503

    logger.info(
        "Health check | status=%s | scanner=%s | redis=%s",
        overall_status,
        response.scanner,
        response.redis,
    )

    return JSONResponse(
        content=response.model_dump(mode="json"),
        status_code=http_status,
    )
