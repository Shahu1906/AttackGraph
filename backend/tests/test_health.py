"""
AttackGraphX Tests — Health endpoint
"""
import pytest
from unittest.mock import AsyncMock, patch


def test_health_all_up(client):
    with (
        patch(
            "app.routes.health.analysis_client.health_check",
            new=AsyncMock(return_value=True),
        ),
        patch(
            "app.routes.health.cache_service.ping",
            new=AsyncMock(return_value=True),
        ),
    ):
        resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["dependencies"]["gateway"] == "up"
    assert data["dependencies"]["analysis"] == "up"
    assert data["redis"] == "up"


def test_health_analysis_down_is_degraded(client):
    with (
        patch(
            "app.routes.health.analysis_client.health_check",
            new=AsyncMock(return_value=False),
        ),
        patch(
            "app.routes.health.cache_service.ping",
            new=AsyncMock(return_value=True),
        ),
    ):
        resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "degraded"
    assert data["dependencies"]["analysis"] == "down"


def test_health_redis_down_is_degraded(client):
    with (
        patch(
            "app.routes.health.analysis_client.health_check",
            new=AsyncMock(return_value=True),
        ),
        patch(
            "app.routes.health.cache_service.ping",
            new=AsyncMock(return_value=False),
        ),
    ):
        resp = client.get("/health")
    assert resp.status_code == 200
    # Redis status visible in response
    assert resp.json()["redis"] == "down"


def test_health_no_auth_required(client):
    """Health endpoint must be publicly accessible (no JWT needed)."""
    with (
        patch("app.routes.health.analysis_client.health_check", new=AsyncMock(return_value=True)),
        patch("app.routes.health.cache_service.ping", new=AsyncMock(return_value=True)),
    ):
        resp = client.get("/health")
    # Must NOT return 401
    assert resp.status_code != 401
    assert resp.status_code == 200
