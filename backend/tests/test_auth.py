"""
AttackGraphX Tests — Authentication

Tests:
  - Admin login succeeds, returns JWT with correct payload
  - Analyst login succeeds
  - Wrong password → 401
  - Unknown user → 401
  - Missing Authorization header → 401
  - Expired/invalid JWT → 401
"""
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.config import get_settings
from app.main import app

settings = get_settings()
client = TestClient(app)


def test_admin_login_success():
    resp = client.post("/auth/login", json={"username": "admin", "password": "admin123"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    # Decode and verify payload
    payload = jwt.decode(data["access_token"], settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    assert payload["sub"] == "admin"
    assert payload["role"] == "admin"
    assert "exp" in payload


def test_analyst_login_success():
    resp = client.post("/auth/login", json={"username": "analyst", "password": "analyst123"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    payload = jwt.decode(data["access_token"], settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    assert payload["role"] == "analyst"


def test_wrong_password_returns_401():
    resp = client.post("/auth/login", json={"username": "admin", "password": "wrongpassword"})
    assert resp.status_code == 401


def test_unknown_user_returns_401():
    resp = client.post("/auth/login", json={"username": "ghost", "password": "ghost123"})
    assert resp.status_code == 401


def test_missing_auth_header_returns_401():
    resp = client.get("/paths")
    assert resp.status_code == 401


def test_invalid_jwt_returns_401():
    resp = client.get("/paths", headers={"Authorization": "Bearer not.a.valid.token"})
    assert resp.status_code == 401


def test_expired_jwt_returns_401():
    # Create a token that already expired
    expired_token = jwt.encode(
        {
            "sub": "admin",
            "role": "admin",
            "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
        },
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    resp = client.get("/paths", headers={"Authorization": f"Bearer {expired_token}"})
    assert resp.status_code == 401


def test_malformed_bearer_token_returns_401():
    resp = client.get("/paths", headers={"Authorization": "Bearer "})
    assert resp.status_code == 401
