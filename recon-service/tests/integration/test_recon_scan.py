"""
Integration Tests — Full Recon Pipeline & Redis
================================================

These tests require:
  1. Docker to be installed and running
  2. Nmap to be installed on the host machine
  3. The testcontainers library

Tests are automatically skipped if Docker or Nmap is not available.

What these tests verify:
  - A temporary HTTP container is spun up
  - Nmap scans it within a test Docker network
  - XML is parsed correctly
  - ScanResult is normalized and validated
  - ScanResult is published to a temporary Redis container
  - The published data can be read back and deserialized

These tests prove the full pipeline end-to-end without requiring
the real attackgraphx-net range.
"""

from __future__ import annotations

import json
import shutil
import time
from datetime import UTC, datetime

import pytest
import pytest_asyncio

# ─── Skip guards ──────────────────────────────────────────────────────────────

def _docker_available() -> bool:
    """Check if Docker daemon is reachable."""
    try:
        import docker
        client = docker.from_env()
        client.ping()
        return True
    except Exception:
        return False


def _nmap_available() -> bool:
    return shutil.which("nmap") is not None


NEEDS_DOCKER = pytest.mark.skipif(
    not _docker_available(),
    reason="Docker not available — skipping integration tests",
)
NEEDS_NMAP = pytest.mark.skipif(
    not _nmap_available(),
    reason="nmap not installed — skipping integration tests",
)
NEEDS_BOTH = pytest.mark.skipif(
    not (_docker_available() and _nmap_available()),
    reason="Docker and/or nmap not available — skipping integration tests",
)


# ─── Test: Full Pipeline (Docker + Nmap) ─────────────────────────────────────

@NEEDS_BOTH
class TestFullScanPipeline:
    """
    Spins up a temporary nginx container, scans it with Nmap,
    and validates the full parse → normalize → validate pipeline.
    """

    def test_scan_real_container(self):
        """
        INTEGRATION: Start an nginx container, scan it, validate pipeline.
        """
        import docker

        client = docker.from_env()
        network = None
        container = None

        try:
            # ── Create isolated test network ───────────────────────────────
            network_name = f"attackgraphx-test-{int(time.time())}"
            network = client.networks.create(
                network_name,
                driver="bridge",
                ipam=docker.types.IPAMConfig(
                    pool_configs=[
                        docker.types.IPAMPool(subnet="192.168.99.0/29")
                    ]
                ),
            )

            # ── Start nginx container ──────────────────────────────────────
            container = client.containers.run(
                "nginx:alpine",
                detach=True,
                name=f"test-web-{int(time.time())}",
                network=network_name,
                remove=True,
            )

            # Give nginx a moment to start
            time.sleep(3)

            # Get container's IP on the test network
            container.reload()
            net_settings = container.attrs["NetworkSettings"]["Networks"]
            container_ip = net_settings[network_name]["IPAddress"]
            assert container_ip, "Container has no IP on test network"

            # ── Run Nmap ───────────────────────────────────────────────────
            # Temporarily override the authorized CIDR to allow this test subnet
            from app.scanner import nmap_runner
            original_cidr = nmap_runner.settings.range_cidr

            try:
                # Patch settings for test
                nmap_runner.settings.__dict__["range_cidr"] = "192.168.99.0/29"
                xml_output = nmap_runner.run_nmap(
                    container_ip,
                    extra_flags="-sV -T4 -p 80",
                    timeout=60,
                )
            finally:
                nmap_runner.settings.__dict__["range_cidr"] = original_cidr

            assert xml_output, "Nmap produced no XML output"
            assert "<nmaprun" in xml_output

            # ── Parse XML ─────────────────────────────────────────────────
            from app.scanner.xml_parser import parse_nmap_xml
            hosts = parse_nmap_xml(xml_output)

            assert len(hosts) >= 1, "No hosts parsed from Nmap output"

            target_host = next((h for h in hosts if h["ip"] == container_ip), None)
            assert target_host is not None, f"Container IP {container_ip} not in parsed hosts"
            assert target_host["state"] == "up"

            # ── Check for port 80 ─────────────────────────────────────────
            open_ports = [
                p for p in target_host["ports"]
                if p["state"] == "open"
            ]
            port_numbers = {p["port"] for p in open_ports}
            assert 80 in port_numbers, (
                f"Expected port 80 to be open, found: {port_numbers}"
            )

            http_service = next((p for p in open_ports if p["port"] == 80), None)
            assert http_service is not None
            assert http_service["name"] == "http"

            # ── Normalize ─────────────────────────────────────────────────
            from app.normalizer.normalizer import normalize
            result = normalize(hosts, container_ip)

            assert result.scan_id.startswith("scan-")
            assert result.scanner == "nmap"
            assert len(result.hosts) >= 1

            # ── Validate JSON serialization ───────────────────────────────
            json_str = result.model_dump_json()
            data = json.loads(json_str)
            assert "scan_id" in data
            assert "hosts" in data
            assert "timestamp" in data

            # ── Verify host fields ────────────────────────────────────────
            host_data = next(
                (h for h in data["hosts"] if h["ip"] == container_ip), None
            )
            assert host_data is not None
            assert host_data["state"] == "up"

            svc_80 = next(
                (s for s in host_data["services"] if s["port"] == 80), None
            )
            assert svc_80 is not None, "Port 80 service not in normalized output"
            assert svc_80["protocol"] == "tcp"
            assert svc_80["state"] == "open"

        finally:
            # ── Cleanup ───────────────────────────────────────────────────
            if container:
                try:
                    container.stop(timeout=5)
                except Exception:
                    pass
            if network:
                try:
                    network.remove()
                except Exception:
                    pass


# ─── Test: Redis Integration ──────────────────────────────────────────────────

@NEEDS_DOCKER
class TestRedisIntegration:
    """
    Spins up a temporary Redis container and tests the full
    publish → read → deserialize → validate cycle.
    """

    @pytest.mark.asyncio
    async def test_publish_and_read_scan_result(self):
        """
        INTEGRATION: Publish a ScanResult to Redis, read it back, validate schema.
        """
        import docker

        client = docker.from_env()
        redis_container = None

        try:
            # ── Start Redis container ──────────────────────────────────────
            redis_container = client.containers.run(
                "redis:7-alpine",
                detach=True,
                ports={"6379/tcp": None},  # Random host port
                name=f"test-redis-{int(time.time())}",
                remove=True,
            )
            time.sleep(2)

            redis_container.reload()
            host_port = redis_container.ports["6379/tcp"][0]["HostPort"]
            redis_url = f"redis://localhost:{host_port}/0"

            # ── Build a test ScanResult ────────────────────────────────────
            from app.models.scan_models import Host, ScanResult, Service

            test_result = ScanResult(
                scan_id="scan-integtest01",
                timestamp=datetime(2026, 9, 22, 10, 30, 0, tzinfo=UTC),
                scanner="nmap",
                target_scope="172.20.0.0/24",
                hosts=[
                    Host(
                        ip="172.20.0.10",
                        hostname="web-server",
                        state="up",
                        segment="web",
                        services=[
                            Service(
                                port=80,
                                protocol="tcp",
                                state="open",
                                name="http",
                                product="nginx",
                                version="1.25.0",
                            )
                        ],
                    )
                ],
            )

            # ── Publish to test Redis ──────────────────────────────────────
            import redis.asyncio as aioredis
            from app.publisher.redis_publisher import RedisPublishError

            # Patch settings temporarily
            from app import publisher
            from app.publisher import redis_publisher
            original_url = redis_publisher.settings.redis_url
            redis_publisher.settings.__dict__["redis_url"] = redis_url

            try:
                entry_id = await redis_publisher.publish_scan_result(test_result)
            finally:
                redis_publisher.settings.__dict__["redis_url"] = original_url

            assert entry_id, "No entry_id returned from XADD"

            # ── Read back from stream ──────────────────────────────────────
            redis_client = aioredis.from_url(redis_url, decode_responses=True)

            try:
                entries = await redis_client.xrevrange("scan_results", count=1)
            finally:
                await redis_client.aclose()

            assert len(entries) == 1, "Expected 1 entry in stream"

            entry_id_read, fields = entries[0]
            assert fields.get("scan_id") == "scan-integtest01"

            # ── Deserialize and validate ───────────────────────────────────
            raw_json = fields.get("data")
            assert raw_json, "No data field in stream entry"

            restored = ScanResult.model_validate_json(raw_json)

            assert restored.scan_id == "scan-integtest01"
            assert restored.scanner == "nmap"
            assert len(restored.hosts) == 1
            assert restored.hosts[0].ip == "172.20.0.10"
            assert restored.hosts[0].hostname == "web-server"
            assert restored.hosts[0].services[0].port == 80
            assert restored.hosts[0].services[0].name == "http"

        finally:
            if redis_container:
                try:
                    redis_container.stop(timeout=5)
                except Exception:
                    pass


# ─── Test: Target Validation ──────────────────────────────────────────────────

class TestTargetValidation:
    """
    Tests for nmap_runner.validate_target — no Docker or Nmap needed.
    """

    def test_valid_ip_within_range(self):
        from app.scanner.nmap_runner import validate_target
        # Should not raise
        validate_target("172.20.0.10", "172.20.0.0/24")

    def test_valid_subnet_within_range(self):
        from app.scanner.nmap_runner import validate_target
        validate_target("172.20.0.0/24", "172.20.0.0/24")

    def test_valid_smaller_subnet(self):
        from app.scanner.nmap_runner import validate_target
        validate_target("172.20.0.128/25", "172.20.0.0/24")

    def test_ip_outside_range_raises(self):
        from app.scanner.nmap_runner import InvalidTargetError, validate_target
        with pytest.raises(InvalidTargetError):
            validate_target("8.8.8.8", "172.20.0.0/24")

    def test_different_subnet_raises(self):
        from app.scanner.nmap_runner import InvalidTargetError, validate_target
        with pytest.raises(InvalidTargetError):
            validate_target("10.0.0.1", "172.20.0.0/24")

    def test_invalid_ip_format_raises(self):
        from app.scanner.nmap_runner import InvalidTargetError, validate_target
        with pytest.raises(InvalidTargetError):
            validate_target("not-an-ip", "172.20.0.0/24")

    def test_internet_ip_raises(self):
        from app.scanner.nmap_runner import InvalidTargetError, validate_target
        with pytest.raises(InvalidTargetError):
            validate_target("1.1.1.1", "172.20.0.0/24")
