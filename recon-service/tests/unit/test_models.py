"""
Unit Tests — Pydantic Models
=============================
Tests for app/models/scan_models.py

Verifies that the canonical AttackGraphX scan contract correctly
validates both valid and invalid data.
"""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.models.scan_models import (
    HealthResponse,
    Host,
    ScanRequest,
    ScanResponse,
    ScanResult,
    ScanStatus,
    Service,
)


# ─── Service Model Tests ──────────────────────────────────────────────────────

class TestServiceModel:

    def test_valid_service(self):
        svc = Service(port=80, protocol="tcp", state="open", name="http",
                      product="nginx", version="1.25.0")
        assert svc.port == 80
        assert svc.protocol == "tcp"
        assert svc.name == "http"

    def test_optional_fields_default_none(self):
        svc = Service(port=80, protocol="tcp", state="open")
        assert svc.name is None
        assert svc.product is None
        assert svc.version is None
        assert svc.extra_info is None

    def test_port_too_low_fails(self):
        with pytest.raises(ValidationError):
            Service(port=0, protocol="tcp", state="open")

    def test_port_too_high_fails(self):
        with pytest.raises(ValidationError):
            Service(port=65536, protocol="tcp", state="open")

    def test_port_boundary_valid(self):
        """Port 1 and 65535 should both be valid."""
        svc1 = Service(port=1, protocol="tcp", state="open")
        svc2 = Service(port=65535, protocol="tcp", state="open")
        assert svc1.port == 1
        assert svc2.port == 65535

    def test_protocol_lowercased(self):
        """Protocol field should be normalized to lowercase."""
        svc = Service(port=80, protocol="TCP", state="open")
        assert svc.protocol == "tcp"

    def test_state_lowercased(self):
        svc = Service(port=80, protocol="tcp", state="OPEN")
        assert svc.state == "open"

    def test_missing_required_port_fails(self):
        with pytest.raises(ValidationError):
            Service(protocol="tcp", state="open")  # type: ignore[call-arg]

    def test_missing_required_protocol_fails(self):
        with pytest.raises(ValidationError):
            Service(port=80, state="open")  # type: ignore[call-arg]

    def test_missing_required_state_fails(self):
        with pytest.raises(ValidationError):
            Service(port=80, protocol="tcp")  # type: ignore[call-arg]


# ─── Host Model Tests ─────────────────────────────────────────────────────────

class TestHostModel:

    def _valid_host_data(self) -> dict:
        return {
            "ip": "172.20.0.10",
            "hostname": "web-server",
            "state": "up",
            "services": [
                {"port": 80, "protocol": "tcp", "state": "open", "name": "http"}
            ],
        }

    def test_valid_host(self):
        host = Host(**self._valid_host_data())
        assert host.ip == "172.20.0.10"
        assert host.hostname == "web-server"
        assert len(host.services) == 1

    def test_optional_hostname(self):
        data = self._valid_host_data()
        data.pop("hostname")
        host = Host(**data)
        assert host.hostname is None

    def test_empty_ip_fails(self):
        data = self._valid_host_data()
        data["ip"] = ""
        with pytest.raises(ValidationError):
            Host(**data)

    def test_missing_ip_fails(self):
        data = self._valid_host_data()
        data.pop("ip")
        with pytest.raises(ValidationError):
            Host(**data)

    def test_missing_state_fails(self):
        data = self._valid_host_data()
        data.pop("state")
        with pytest.raises(ValidationError):
            Host(**data)

    def test_state_lowercased(self):
        data = self._valid_host_data()
        data["state"] = "UP"
        host = Host(**data)
        assert host.state == "up"

    def test_vulnerabilities_default_empty(self):
        host = Host(**self._valid_host_data())
        assert host.vulnerabilities == []

    def test_credentials_default_empty(self):
        host = Host(**self._valid_host_data())
        assert host.credentials == []

    def test_services_default_empty(self):
        host = Host(ip="172.20.0.10", state="up")
        assert host.services == []

    def test_segment_optional(self):
        host = Host(**self._valid_host_data())
        assert host.segment is None  # Not set in _valid_host_data()

    def test_segment_can_be_set(self):
        data = self._valid_host_data()
        data["segment"] = "web"
        host = Host(**data)
        assert host.segment == "web"


# ─── ScanResult Model Tests ───────────────────────────────────────────────────

class TestScanResultModel:

    def _valid_scan(self) -> dict:
        return {
            "scan_id": "scan-a1b2c3d4",
            "timestamp": datetime(2026, 9, 22, 10, 30, 0, tzinfo=UTC),
            "scanner": "nmap",
            "target_scope": "172.20.0.0/24",
            "hosts": [
                {
                    "ip": "172.20.0.10",
                    "state": "up",
                    "services": [
                        {"port": 80, "protocol": "tcp", "state": "open"}
                    ],
                }
            ],
        }

    def test_valid_scan_result(self):
        result = ScanResult(**self._valid_scan())
        assert result.scan_id == "scan-a1b2c3d4"
        assert result.scanner == "nmap"

    def test_missing_scan_id_fails(self):
        data = self._valid_scan()
        data.pop("scan_id")
        with pytest.raises(ValidationError):
            ScanResult(**data)

    def test_missing_timestamp_fails(self):
        data = self._valid_scan()
        data.pop("timestamp")
        with pytest.raises(ValidationError):
            ScanResult(**data)

    def test_missing_target_scope_fails(self):
        data = self._valid_scan()
        data.pop("target_scope")
        with pytest.raises(ValidationError):
            ScanResult(**data)

    def test_scanner_field_literal(self):
        """scanner must be exactly 'nmap'."""
        data = self._valid_scan()
        data["scanner"] = "masscan"  # invalid
        with pytest.raises(ValidationError):
            ScanResult(**data)

    def test_empty_hosts_list_valid(self):
        """ScanResult with no hosts is still valid."""
        data = self._valid_scan()
        data["hosts"] = []
        result = ScanResult(**data)
        assert result.hosts == []

    def test_json_serialization_roundtrip(self):
        """model_dump_json → parse_raw should produce identical model."""
        result = ScanResult(**self._valid_scan())
        json_str = result.model_dump_json()
        restored = ScanResult.model_validate_json(json_str)
        assert restored.scan_id == result.scan_id
        assert restored.scanner == result.scanner
        assert len(restored.hosts) == len(result.hosts)

    def test_summary_keys(self):
        result = ScanResult(**self._valid_scan())
        summary = result.summary()
        assert "scan_id" in summary
        assert "hosts_found" in summary
        assert "services_found" in summary
        assert "timestamp" in summary
        assert "target_scope" in summary


# ─── ScanRequest Model Tests ──────────────────────────────────────────────────

class TestScanRequest:

    def test_valid_cidr_target(self):
        req = ScanRequest(target="172.20.0.0/24")
        assert req.target == "172.20.0.0/24"

    def test_valid_host_target(self):
        req = ScanRequest(target="172.20.0.10")
        assert req.target == "172.20.0.10"

    def test_missing_target_fails(self):
        with pytest.raises(ValidationError):
            ScanRequest()  # type: ignore[call-arg]


# ─── ScanStatus Model Tests ───────────────────────────────────────────────────

class TestScanStatus:

    def test_queued_status(self):
        s = ScanStatus(scan_id="scan-abc", status="queued", target="172.20.0.0/24")
        assert s.status == "queued"
        assert s.started_at is None

    def test_invalid_status_fails(self):
        with pytest.raises(ValidationError):
            ScanStatus(scan_id="scan-abc", status="pending", target="172.20.0.0/24")

    def test_all_statuses_valid(self):
        for st in ("queued", "running", "completed", "failed"):
            s = ScanStatus(scan_id="x", status=st, target="172.20.0.0/24")
            assert s.status == st
