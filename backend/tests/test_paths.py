"""
AttackGraphX Tests — Paths & Patches with cache fallback behavior
"""
import pytest
from unittest.mock import AsyncMock, patch

from tests.conftest import SAMPLE_PATHS, SAMPLE_PATCHES


# -----------------------------------------------------------------------
# Live paths (analysis service is up, no cache needed)
# -----------------------------------------------------------------------

def test_paths_live(admin_client):
    with (
        patch(
            "app.routes.paths.analysis_client.get_paths",
            new=AsyncMock(return_value=SAMPLE_PATHS),
        ),
        patch("app.routes.paths.cache_service.set", new=AsyncMock(return_value=True)),
    ):
        resp = admin_client.get("/paths")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "live"
    assert isinstance(data["data"], list)
    assert len(data["data"]) == len(SAMPLE_PATHS)


def test_paths_with_target_filter(admin_client):
    with (
        patch(
            "app.routes.paths.analysis_client.get_paths",
            new=AsyncMock(return_value=[SAMPLE_PATHS[0]]),
        ),
        patch("app.routes.paths.cache_service.set", new=AsyncMock(return_value=True)),
    ):
        resp = admin_client.get("/paths?target=db-01")
    assert resp.status_code == 200
    assert resp.json()["status"] == "live"


def test_patches_live(admin_client):
    with (
        patch(
            "app.routes.paths.analysis_client.get_patches",
            new=AsyncMock(return_value=SAMPLE_PATCHES),
        ),
        patch("app.routes.paths.cache_service.set", new=AsyncMock(return_value=True)),
    ):
        resp = admin_client.get("/patches")
    assert resp.status_code == 200
    assert resp.json()["status"] == "live"


# -----------------------------------------------------------------------
# Stale cache fallback (analysis service is down, Redis has data)
# -----------------------------------------------------------------------

def test_paths_stale_cache(admin_client):
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
    assert resp.json()["status"] == "stale_cache"
    assert len(resp.json()["data"]) > 0


# -----------------------------------------------------------------------
# Unavailable (analysis service down AND no cache)
# -----------------------------------------------------------------------

def test_paths_unavailable_no_cache(admin_client):
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


# -----------------------------------------------------------------------
# Unauthorized access
# -----------------------------------------------------------------------

def test_paths_no_token_returns_401():
    from fastapi.testclient import TestClient
    from app.main import app
    c = TestClient(app)
    resp = c.get("/paths")
    assert resp.status_code == 401
