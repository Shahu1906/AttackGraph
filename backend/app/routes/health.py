"""
AttackGraphX — GET /health

Returns the status of all platform dependencies:
  - gateway (always "up" if this responds)
  - analysis (probed via HTTP)
  - redis (probed via PING)

No authentication required — safe for monitoring and uptime checks.
Never exposes secrets or internal credentials.
"""
import structlog
from fastapi import APIRouter

from app.services.analysis_client import analysis_client
from app.services.cache_service import cache_service

log = structlog.get_logger(__name__)
router = APIRouter(tags=["Health"])


@router.get("/health", summary="Platform health check")
async def health_check():
    """
    Report gateway and dependency reachability without requiring authentication.

    The overall status reflects the gateway and analysis service. Redis
    reachability is reported separately in the ``redis`` field.
    """
    analysis_ok = await analysis_client.health_check()
    redis_ok = await cache_service.ping()

    # "recon" maps to analysis service in the frontend's health model
    # (recon/analysis/gateway are the frontend dependency names from mockHealth)
    deps = {
        "recon": "up" if analysis_ok else "down",
        "analysis": "up" if analysis_ok else "down",
        "gateway": "up",
    }

    overall = "healthy" if all(v == "up" for v in deps.values()) else "degraded"

    log.info("Health check", status=overall, deps=deps)

    return {
        "status": overall,
        "dependencies": deps,
        "redis": "up" if redis_ok else "down",
    }
