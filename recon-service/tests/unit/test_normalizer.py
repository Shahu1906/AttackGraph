"""
Unit Tests — Normalizer
========================
Tests for app/normalizer/normalizer.py

Verifies that raw parsed host dicts are correctly converted to
the canonical AttackGraphX ScanResult schema.
"""

from datetime import UTC, datetime

import pytest

from app.normalizer.normalizer import generate_scan_id, normalize
from app.models.scan_models import ScanResult, Host, Service


# ─── Fixtures ────────────────────────────────────────────────────────────────

def _web_host_dict() -> dict:
    return {
        "ip": "172.20.0.10",
        "hostname": "web-server",
        "state": "up",
        "ports": [
            {
                "port": 80,
                "protocol": "tcp",
                "state": "open",
                "name": "http",
                "product": "nginx",
                "version": "1.25.0",
                "extra_info": None,
            }
        ],
    }


def _ftp_host_dict() -> dict:
    return {
        "ip": "172.20.0.11",
        "hostname": "ftp-server",
        "state": "up",
        "ports": [
            {
                "port": 21,
                "protocol": "tcp",
                "state": "open",
                "name": "ftp",
                "product": "vsftpd",
                "version": "3.0.5",
                "extra_info": "anonymous",
            }
        ],
    }


def _flask_host_dict() -> dict:
    return {
        "ip": "172.20.0.12",
        "hostname": "custom-flask-app",
        "state": "up",
        "ports": [
            {
                "port": 5000,
                "protocol": "tcp",
                "state": "open",
                "name": "http",
                "product": "Werkzeug httpd",
                "version": "3.0.4",
                "extra_info": "Python 3.11.9",
            }
        ],
    }


# ─── Scan ID Tests ────────────────────────────────────────────────────────────

class TestGenerateScanId:

    def test_format(self):
        """Scan ID should start with 'scan-' followed by 8 hex chars."""
        scan_id = generate_scan_id()
        assert scan_id.startswith("scan-")
        suffix = scan_id[len("scan-"):]
        assert len(suffix) == 8
        assert all(c in "0123456789abcdef" for c in suffix)

    def test_uniqueness(self):
        """Every call should produce a different scan ID."""
        ids = {generate_scan_id() for _ in range(100)}
        assert len(ids) == 100


# ─── Normalization Tests ──────────────────────────────────────────────────────

class TestNormalize:

    def test_returns_scan_result_instance(self):
        result = normalize([_web_host_dict()], "172.20.0.0/24")
        assert isinstance(result, ScanResult)

    def test_scan_id_is_set(self):
        result = normalize([_web_host_dict()], "172.20.0.0/24")
        assert result.scan_id.startswith("scan-")

    def test_custom_scan_id_preserved(self):
        result = normalize([_web_host_dict()], "172.20.0.0/24", scan_id="scan-custom01")
        assert result.scan_id == "scan-custom01"

    def test_timestamp_is_utc(self):
        result = normalize([_web_host_dict()], "172.20.0.0/24")
        assert result.timestamp.tzinfo is not None
        assert result.timestamp.tzinfo == UTC or str(result.timestamp.tzinfo) in ("+00:00", "UTC")

    def test_custom_timestamp_preserved(self):
        ts = datetime(2026, 9, 22, 10, 30, 0, tzinfo=UTC)
        result = normalize([_web_host_dict()], "172.20.0.0/24", timestamp=ts)
        assert result.timestamp == ts

    def test_scanner_field_is_nmap(self):
        result = normalize([_web_host_dict()], "172.20.0.0/24")
        assert result.scanner == "nmap"

    def test_target_scope_preserved(self):
        result = normalize([_web_host_dict()], "172.20.0.0/24")
        assert result.target_scope == "172.20.0.0/24"

    def test_empty_hosts_list(self):
        """No hosts → valid ScanResult with empty hosts list."""
        result = normalize([], "172.20.0.0/24")
        assert result.hosts == []

    def test_web_host_fields(self):
        """Web host's fields should map correctly to Host model."""
        result = normalize([_web_host_dict()], "172.20.0.0/24")
        assert len(result.hosts) == 1

        host = result.hosts[0]
        assert isinstance(host, Host)
        assert host.ip == "172.20.0.10"
        assert host.hostname == "web-server"
        assert host.state == "up"

    def test_web_host_segment_inferred(self):
        """Web server hostname → segment='web'."""
        result = normalize([_web_host_dict()], "172.20.0.0/24")
        assert result.hosts[0].segment == "web"

    def test_ftp_host_segment_inferred(self):
        """FTP server hostname → segment='ftp'."""
        result = normalize([_ftp_host_dict()], "172.20.0.0/24")
        assert result.hosts[0].segment == "ftp"

    def test_flask_host_segment_inferred(self):
        """Flask app hostname → segment='internal'."""
        result = normalize([_flask_host_dict()], "172.20.0.0/24")
        assert result.hosts[0].segment == "internal"

    def test_port_segment_inference_no_hostname(self):
        """Without hostname, port 80 → segment='web'."""
        host = {
            "ip": "172.20.0.99",
            "hostname": None,
            "state": "up",
            "ports": [{"port": 80, "protocol": "tcp", "state": "open",
                        "name": "http", "product": None, "version": None, "extra_info": None}],
        }
        result = normalize([host], "172.20.0.0/24")
        assert result.hosts[0].segment == "web"

    def test_service_fields_mapped_correctly(self):
        """Service fields should map 1-to-1 from port dict to Service model."""
        result = normalize([_web_host_dict()], "172.20.0.0/24")
        svc = result.hosts[0].services[0]

        assert isinstance(svc, Service)
        assert svc.port == 80
        assert svc.protocol == "tcp"
        assert svc.state == "open"
        assert svc.name == "http"
        assert svc.product == "nginx"
        assert svc.version == "1.25.0"

    def test_vulnerabilities_empty_by_default(self):
        """vulnerabilities should always be empty list initially."""
        result = normalize([_web_host_dict()], "172.20.0.0/24")
        assert result.hosts[0].vulnerabilities == []

    def test_credentials_empty_by_default(self):
        """credentials should always be empty list initially."""
        result = normalize([_web_host_dict()], "172.20.0.0/24")
        assert result.hosts[0].credentials == []

    def test_multiple_hosts_normalized(self):
        """Three hosts → three Host entries in ScanResult."""
        result = normalize(
            [_web_host_dict(), _ftp_host_dict(), _flask_host_dict()],
            "172.20.0.0/24",
        )
        assert len(result.hosts) == 3

    def test_host_without_ip_skipped(self):
        """Host with no IP should be silently skipped."""
        bad_host = {"ip": "", "hostname": "ghost", "state": "up", "ports": []}
        result = normalize([bad_host, _web_host_dict()], "172.20.0.0/24")
        assert len(result.hosts) == 1
        assert result.hosts[0].ip == "172.20.0.10"

    def test_invalid_port_number_skipped(self):
        """Port with invalid number (0 or >65535) should be skipped."""
        host = {
            "ip": "172.20.0.10",
            "hostname": "web-server",
            "state": "up",
            "ports": [
                {"port": 0, "protocol": "tcp", "state": "open",
                 "name": "http", "product": None, "version": None, "extra_info": None},
                {"port": 80, "protocol": "tcp", "state": "open",
                 "name": "http", "product": "nginx", "version": "1.25.0", "extra_info": None},
            ],
        }
        result = normalize([host], "172.20.0.0/24")
        assert len(result.hosts[0].services) == 1
        assert result.hosts[0].services[0].port == 80

    def test_summary_method(self):
        result = normalize(
            [_web_host_dict(), _ftp_host_dict()],
            "172.20.0.0/24",
        )
        summary = result.summary()
        assert summary["hosts_found"] == 2
        assert summary["services_found"] == 2
        assert "scan_id" in summary
        assert "timestamp" in summary
