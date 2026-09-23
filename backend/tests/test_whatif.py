"""
AttackGraphX Tests — RBAC / What-If / Scan
"""
import pytest
from unittest.mock import AsyncMock, patch

from tests.conftest import SAMPLE_SIMULATE_RESULT


# -----------------------------------------------------------------------
# RBAC: admin can simulate, analyst gets 403
# -----------------------------------------------------------------------

def test_admin_can_simulate(admin_client):
    with (
        patch(
            "app.routes.whatif.analysis_client.simulate_fix",
            new=AsyncMock(return_value=SAMPLE_SIMULATE_RESULT),
        ),
        patch("app.routes.whatif.cache_service.set", new=AsyncMock(return_value=True)),
    ):
        resp = admin_client.post("/simulate", json={"vulnerability_id": "CVE-2023-34362"})
    assert resp.status_code == 200
    data = resp.json()
    assert "before" in data
    assert "after" in data
    assert data["vulnerability_id"] == "CVE-2023-34362"


def test_analyst_cannot_simulate(analyst_client):
    resp = analyst_client.post("/simulate", json={"vulnerability_id": "CVE-2023-34362"})
    assert resp.status_code == 403


def test_no_token_cannot_simulate():
    from fastapi.testclient import TestClient
    from app.main import app
    c = TestClient(app)
    resp = c.post("/simulate", json={"vulnerability_id": "CVE-2023-34362"})
    assert resp.status_code == 401


# -----------------------------------------------------------------------
# Simulate reset
# -----------------------------------------------------------------------

def test_admin_can_reset(admin_client):
    with patch(
        "app.routes.whatif.analysis_client.reset_simulation",
        new=AsyncMock(return_value={"status": "live", "message": "Simulations reset"}),
    ):
        resp = admin_client.post("/simulate/reset")
    assert resp.status_code == 200
    assert resp.json()["status"] == "live"


def test_analyst_cannot_reset(analyst_client):
    resp = analyst_client.post("/simulate/reset")
    assert resp.status_code == 403


# -----------------------------------------------------------------------
# Scan
# -----------------------------------------------------------------------

def test_admin_can_trigger_scan(admin_client):
    with patch(
        "app.routes.whatif.analysis_client.trigger_scan",
        new=AsyncMock(return_value={"message": "Scan triggered"}),
    ):
        resp = admin_client.get("/scan/trigger")
    assert resp.status_code == 200
    assert "message" in resp.json()


def test_analyst_cannot_trigger_scan(analyst_client):
    resp = analyst_client.get("/scan/trigger")
    assert resp.status_code == 403


def test_analyst_can_get_scan_status(analyst_client):
    with patch(
        "app.routes.whatif.analysis_client.get_scan_status",
        new=AsyncMock(return_value={"status": "idle", "last_scan": "2026-09-21T00:00:00Z"}),
    ):
        resp = analyst_client.get("/scan/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "last_scan" in data


# -----------------------------------------------------------------------
# Simulation service unavailable with cache fallback
# -----------------------------------------------------------------------

def test_simulate_service_unavailable_returns_503(admin_client):
    from app.services.analysis_client import AnalysisServiceError
    with (
        patch(
            "app.routes.whatif.analysis_client.simulate_fix",
            new=AsyncMock(side_effect=AnalysisServiceError()),
        ),
        patch(
            "app.routes.whatif.cache_service.get",
            new=AsyncMock(return_value=None),  # No cached result
        ),
    ):
        resp = admin_client.post("/simulate", json={"vulnerability_id": "CVE-2023-34362"})
    assert resp.status_code == 503
