"""
AttackGraphX Tests — PDF and CSV report generation
"""
import pytest
from unittest.mock import AsyncMock, patch

from tests.conftest import SAMPLE_PATHS, SAMPLE_PATCHES


def test_csv_report_download(admin_client):
    with (
        patch(
            "app.routes.reports.analysis_client.get_paths",
            new=AsyncMock(return_value=SAMPLE_PATHS),
        ),
        patch(
            "app.routes.reports.analysis_client.get_patches",
            new=AsyncMock(return_value=SAMPLE_PATCHES),
        ),
    ):
        resp = admin_client.get("/reports/csv")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    content = resp.text
    # Verify expected CSV columns exist in header row
    assert "Path_ID" in content
    assert "Target" in content
    assert "Risk_Score" in content
    assert "Severity" in content
    assert "CVEs" in content
    # Verify actual data rows exist
    assert "PATH-001" in content
    assert "CVE-2023-34362" in content


def test_csv_column_count(admin_client):
    with (
        patch(
            "app.routes.reports.analysis_client.get_paths",
            new=AsyncMock(return_value=SAMPLE_PATHS),
        ),
        patch(
            "app.routes.reports.analysis_client.get_patches",
            new=AsyncMock(return_value=SAMPLE_PATCHES),
        ),
    ):
        resp = admin_client.get("/reports/csv")
    lines = resp.text.strip().split("\n")
    header_cols = len(lines[0].split(","))
    assert header_cols >= 12  # Should have at least 13 columns


def test_pdf_report_download(admin_client):
    with (
        patch(
            "app.routes.reports.analysis_client.get_paths",
            new=AsyncMock(return_value=SAMPLE_PATHS),
        ),
        patch(
            "app.routes.reports.analysis_client.get_patches",
            new=AsyncMock(return_value=SAMPLE_PATCHES),
        ),
    ):
        resp = admin_client.get("/reports/pdf")
    assert resp.status_code == 200
    assert "application/pdf" in resp.headers["content-type"]
    # PDF files always start with %PDF-
    assert resp.content[:5] == b"%PDF-"


def test_pdf_report_with_target_filter(admin_client):
    with (
        patch(
            "app.routes.reports.analysis_client.get_paths",
            new=AsyncMock(return_value=[SAMPLE_PATHS[0]]),
        ),
        patch(
            "app.routes.reports.analysis_client.get_patches",
            new=AsyncMock(return_value=SAMPLE_PATCHES),
        ),
    ):
        resp = admin_client.get("/reports/pdf?target=db-01")
    assert resp.status_code == 200
    assert resp.content[:5] == b"%PDF-"


def test_reports_require_auth():
    from fastapi.testclient import TestClient
    from app.main import app
    c = TestClient(app)
    assert c.get("/reports/csv").status_code == 401
    assert c.get("/reports/pdf").status_code == 401
