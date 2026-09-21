"""
AttackGraphX Tests — Redis Cache Service
Tests cache write, retrieval, stale-cache fallback, and Redis failure tolerance.
"""
import pytest
from unittest.mock import AsyncMock, patch

from tests.conftest import SAMPLE_PATHS


def test_cache_written_on_live_response(admin_client):
    """Successful analysis response should be written to Redis."""
    mock_set = AsyncMock(return_value=True)
    with (
        patch(
            "app.routes.paths.analysis_client.get_paths",
            new=AsyncMock(return_value=SAMPLE_PATHS),
        ),
        patch("app.routes.paths.cache_service.set", new=mock_set),
    ):
        resp = admin_client.get("/paths")
    assert resp.status_code == 200
    assert resp.json()["status"] == "live"
    # Cache write should have been called once
    mock_set.assert_called_once()
    call_args = mock_set.call_args
    # First positional arg should be the cache key
    assert call_args.args[0].startswith("paths:")


def test_cache_read_on_service_failure(admin_client):
    """When analysis service fails, cached data must be returned with stale_cache."""
    from app.services.analysis_client import AnalysisServiceError
    with (
        patch(
            "app.routes.paths.analysis_client.get_paths",
            new=AsyncMock(side_effect=AnalysisServiceError()),
        ),
        patch(
            "app.routes.paths.cache_service.get",
            new=AsyncMock(return_value=SAMPLE_PATHS),
        ),
    ):
        resp = admin_client.get("/paths")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "stale_cache"
    assert len(data["data"]) == len(SAMPLE_PATHS)


def test_unavailable_when_both_fail(admin_client):
    """When both analysis service and cache fail, return unavailable with empty data."""
    from app.services.analysis_client import AnalysisServiceError
    with (
        patch(
            "app.routes.paths.analysis_client.get_paths",
            new=AsyncMock(side_effect=AnalysisServiceError()),
        ),
        patch(
            "app.routes.paths.cache_service.get",
            new=AsyncMock(return_value=None),
        ),
    ):
        resp = admin_client.get("/paths")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "unavailable"
    assert data["data"] == []


def test_cache_failure_is_non_fatal(admin_client):
    """Redis write failure must not crash the gateway — live data is still returned."""
    with (
        patch(
            "app.routes.paths.analysis_client.get_paths",
            new=AsyncMock(return_value=SAMPLE_PATHS),
        ),
        patch(
            "app.routes.paths.cache_service.set",
            new=AsyncMock(return_value=False),  # Redis failure
        ),
    ):
        resp = admin_client.get("/paths")
    # Status is still live because analysis succeeded
    assert resp.status_code == 200
    assert resp.json()["status"] == "live"
