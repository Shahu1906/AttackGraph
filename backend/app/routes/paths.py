"""
AttackGraphX — GET /paths and GET /patches

Implements the resilient data fetching pattern:
  1. Try analysis service → cache → return live
  2. Service unavailable → try Redis → return stale_cache
  3. Both unavailable → return unavailable
"""
from typing import Annotated, Optional

import structlog
from fastapi import APIRouter, Depends, Query

from app.auth.dependencies import get_current_user
from app.services.analysis_client import analysis_client, AnalysisServiceError
from app.services.cache_service import cache_service

log = structlog.get_logger(__name__)
router = APIRouter(tags=["Attack Paths"])


async def _fetch_with_fallback(
    cache_key: str,
    fetch_fn,
    *fetch_args,
) -> dict:
    """
    Shared resilient fetch pattern used by /paths and /patches.
    Returns {"data": [...], "status": "live|stale_cache|unavailable"}
    """
    # 1. Try analysis service
    try:
        data = await fetch_fn(*fetch_args)
        await cache_service.set(cache_key, data)
        log.info("Analysis data fetched live", key=cache_key, count=len(data) if data else 0)
        return {"data": data, "status": "live"}
    except AnalysisServiceError as exc:
        log.warning("Analysis service unavailable, trying cache", key=cache_key, error=str(exc))

    # 2. Try Redis last-known-good
    cached = await cache_service.get(cache_key)
    if cached is not None:
        log.info("Serving stale cache", key=cache_key)
        return {"data": cached, "status": "stale_cache"}

    # 3. Both unavailable
    log.warning("No cached data, returning unavailable", key=cache_key)
    return {"data": [], "status": "unavailable"}


@router.get("/paths", summary="Get attack paths (with Redis fallback)")
async def get_paths(
    target: Optional[str] = Query(default="all", description="Filter by target host"),
    _user: Annotated[dict, Depends(get_current_user)] = None,
):
    cache_key = cache_service.paths_key(target or "all")
    return await _fetch_with_fallback(
        cache_key,
        analysis_client.get_paths,
        target or "all",
    )


@router.get("/patches", summary="Get remediation patches (with Redis fallback)")
async def get_patches(
    _user: Annotated[dict, Depends(get_current_user)] = None,
):
    cache_key = cache_service.patches_key()
    return await _fetch_with_fallback(
        cache_key,
        analysis_client.get_patches,
    )
