"""
AttackGraphX — What-If & Scan routes

POST /simulate        — Admin only
POST /simulate/reset  — Admin only
GET  /scan/trigger    — Admin only
GET  /scan/status     — Authenticated
"""
from datetime import datetime, timezone
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_current_user, require_admin
from app.schemas.dashboard import SimulateRequest, SimulateResponse, ScanStatusResponse
from app.services.analysis_client import analysis_client, AnalysisServiceError
from app.services.cache_service import cache_service

log = structlog.get_logger(__name__)
router = APIRouter(tags=["What-If & Scan"])


@router.post(
    "/simulate",
    response_model=SimulateResponse,
    summary="Simulate vulnerability fix impact (Admin only)",
)
async def simulate_fix(
    body: SimulateRequest,
    admin: Annotated[dict, Depends(require_admin)] = None,
):
    log.info("Simulate fix requested", user=admin.get("sub"), vulnerability=body.vulnerability_id)
    try:
        result = await analysis_client.simulate_fix(body.vulnerability_id)
        # Cache the simulation result
        await cache_service.set(
            cache_service.simulate_key(body.vulnerability_id),
            result,
        )
        # Ensure required status field is present
        if "status" not in result:
            result["status"] = "live"
        log.info("Simulation complete", vulnerability=body.vulnerability_id)
        return result
    except AnalysisServiceError:
        log.warning("Analysis service unavailable for simulation", vulnerability=body.vulnerability_id)
        # Try cached simulation result
        cached = await cache_service.get(cache_service.simulate_key(body.vulnerability_id))
        if cached:
            cached["status"] = "stale_cache"
            return cached
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "ANALYSIS_SERVICE_UNAVAILABLE",
                "message": "Simulation service is currently unavailable.",
                "status": "unavailable",
            },
        )


@router.post(
    "/simulate/reset",
    summary="Reset all active simulations (Admin only)",
)
async def reset_simulation(
    admin: Annotated[dict, Depends(require_admin)] = None,
):
    log.info("Simulation reset requested", user=admin.get("sub"))
    try:
        result = await analysis_client.reset_simulation()
        if "status" not in result:
            result["status"] = "live"
        if "message" not in result:
            result["message"] = "Simulations reset"
        return result
    except AnalysisServiceError:
        log.warning("Analysis service unavailable for reset")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "ANALYSIS_SERVICE_UNAVAILABLE",
                "message": "Could not reach the analysis service to reset simulations.",
            },
        )


@router.get(
    "/scan/trigger",
    summary="Trigger infrastructure scan (Admin only)",
)
async def trigger_scan(
    admin: Annotated[dict, Depends(require_admin)] = None,
):
    log.info("Scan trigger requested", user=admin.get("sub"))
    try:
        result = await analysis_client.trigger_scan()
        if "message" not in result:
            result["message"] = "Security graph scan triggered successfully. Processing topology updates..."
        return result
    except AnalysisServiceError:
        log.warning("Analysis service unavailable for scan trigger")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "ANALYSIS_SERVICE_UNAVAILABLE",
                "message": "Could not reach the analysis service to trigger a scan.",
            },
        )


@router.get(
    "/scan/status",
    response_model=ScanStatusResponse,
    summary="Get current scan status",
)
async def get_scan_status(
    _user: Annotated[dict, Depends(get_current_user)] = None,
):
    try:
        result = await analysis_client.get_scan_status()
        if "status" not in result:
            result["status"] = "idle"
        if "last_scan" not in result:
            result["last_scan"] = datetime.now(timezone.utc).isoformat()
        return result
    except AnalysisServiceError:
        return ScanStatusResponse(
            status="unavailable",
            last_scan=datetime.now(timezone.utc).isoformat(),
        )
