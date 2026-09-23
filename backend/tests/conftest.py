"""
AttackGraphX Tests — Fixtures and shared test utilities.
Uses FastAPI TestClient with dependency overrides to isolate
the gateway from the real analysis service and Redis.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.auth.dependencies import get_current_user, require_admin
from app.auth.jwt import create_access_token
from app.services.analysis_client import AnalysisServiceError

# -----------------------------------------------------------------------
# Sample data fixtures
# -----------------------------------------------------------------------
SAMPLE_PATHS = [
    {
        "id": "PATH-001",
        "target": "db-01",
        "risk_score": 95,
        "severity": "critical",
        "detectability": "low",
        "hops": [
            {
                "host": "cloud-gateway",
                "ip": "10.0.1.5",
                "vulnerability": "CVE-2023-34362",
                "attack_technique": "T1190",
                "description": "MOVEit Transfer RCE",
            },
            {
                "host": "db-01",
                "ip": "10.0.4.100",
                "vulnerability": "CVE-2023-23397",
                "attack_technique": "T1078",
                "description": "Privilege escalation on DB",
            },
        ],
    },
    {
        "id": "PATH-002",
        "target": "vault-01",
        "risk_score": 75,
        "severity": "high",
        "detectability": "medium",
        "hops": [
            {
                "host": "jump-01",
                "ip": "10.0.1.99",
                "vulnerability": "CVE-2024-3094",
                "attack_technique": "T1021",
                "description": "XZ Utils backdoor",
            },
        ],
    },
]

SAMPLE_PATCHES = [
    {
        "id": "PATCH-001",
        "vulnerability_id": "CVE-2023-34362",
        "host": "cloud-gateway",
        "description": "Apply MOVEit Transfer patch.",
        "paths_closed": 3,
        "risk_reduction": 42,
    },
]

SAMPLE_SIMULATE_RESULT = {
    "before": {"path_count": 12, "avg_risk": 67, "critical_paths": 3},
    "after": {"path_count": 9, "avg_risk": 55, "critical_paths": 1},
    "vulnerability_id": "CVE-2023-34362",
    "status": "live",
}

# -----------------------------------------------------------------------
# Token helpers
# -----------------------------------------------------------------------

def make_token(username: str, role: str) -> str:
    return create_access_token({"sub": username, "role": role})


@pytest.fixture
def admin_token():
    return make_token("admin", "admin")


@pytest.fixture
def analyst_token():
    return make_token("analyst", "analyst")


# -----------------------------------------------------------------------
# Auth dependency overrides
# -----------------------------------------------------------------------

def _override_admin():
    return {"sub": "admin", "role": "admin"}


def _override_analyst():
    return {"sub": "analyst", "role": "analyst"}


# -----------------------------------------------------------------------
# Clients
# -----------------------------------------------------------------------

@pytest.fixture
def client():
    """TestClient with no auth overrides — uses real JWT validation."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def admin_client():
    """TestClient with admin auth overridden — no real JWT needed."""
    app.dependency_overrides[get_current_user] = _override_admin
    app.dependency_overrides[require_admin] = _override_admin
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def analyst_client():
    """TestClient with analyst auth overridden."""
    app.dependency_overrides[get_current_user] = _override_analyst
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
