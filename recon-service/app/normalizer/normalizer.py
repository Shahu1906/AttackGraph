"""
AttackGraphX Recon Service — Scan Result Normalizer
=====================================================
Transforms raw parsed Nmap data (Python dicts from xml_parser.py) into
the canonical AttackGraphX ScanResult Pydantic model.

Key principle: This module understands the AttackGraphX schema.
               xml_parser.py understands Nmap's XML schema.
               Keeping them separate means Nmap can be replaced without
               changing the contract that Person 2 consumes.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from app.config import settings
from app.models.scan_models import Host, ScanResult, Service

logger = logging.getLogger(__name__)


# ─── Scan ID Generation ───────────────────────────────────────────────────────

def generate_scan_id() -> str:
    """
    Generate a unique scan ID.
    Format: scan-<8 hex chars from uuid4>
    Example: scan-a3f2b891

    Every call returns a different ID (UUID4 guarantees this).
    """
    return f"scan-{uuid.uuid4().hex[:8]}"


# ─── Segment Inference ────────────────────────────────────────────────────────

def _infer_segment(host_data: dict[str, Any]) -> str | None:
    """
    Attempt to infer the network segment label from hostname or services.
    This is a best-effort inference, not guaranteed to be accurate.

    Examples:
        hostname='web-server'         → 'web'
        hostname='ftp-server'         → 'ftp'
        hostname='custom-flask-app'   → 'internal'
        port 80 open (no hostname)    → 'web'
        port 21 open (no hostname)    → 'ftp'
    """
    hostname = (host_data.get("hostname") or "").lower()

    if "web" in hostname:
        return "web"
    if "ftp" in hostname:
        return "ftp"
    if "flask" in hostname or "app" in hostname or "custom" in hostname:
        return "internal"

    # Fall back to port-based inference
    ports: list[dict[str, Any]] = host_data.get("ports", [])
    open_port_numbers = {
        p["port"] for p in ports if p.get("state") == "open"
    }

    if 80 in open_port_numbers or 443 in open_port_numbers or 8080 in open_port_numbers:
        return "web"
    if 21 in open_port_numbers:
        return "ftp"
    if 22 in open_port_numbers:
        return "ssh"

    return None


# ─── Service Normalization ────────────────────────────────────────────────────

def _normalize_service(port_data: dict[str, Any]) -> Service | None:
    """
    Convert a raw port dict (from xml_parser) into a Service model.

    Returns None if the port data is clearly invalid (e.g., port=0).
    """
    port_num = port_data.get("port", 0)
    if not isinstance(port_num, int) or port_num < 1 or port_num > 65535:
        logger.debug("Skipping port with invalid port number: %s", port_num)
        return None

    try:
        return Service(
            port=port_num,
            protocol=port_data.get("protocol") or "tcp",
            state=port_data.get("state") or "unknown",
            name=port_data.get("name"),
            product=port_data.get("product"),
            version=port_data.get("version"),
            extra_info=port_data.get("extra_info"),
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to create Service from port data %s: %s", port_data, exc)
        return None


# ─── Host Normalization ───────────────────────────────────────────────────────

def _normalize_host(host_data: dict[str, Any]) -> Host | None:
    """
    Convert a raw host dict (from xml_parser) into a Host model.

    Returns None if the host data is invalid (e.g., missing IP).
    """
    ip = host_data.get("ip", "").strip()
    if not ip:
        logger.warning("Skipping host with no IP address: %s", host_data)
        return None

    services: list[Service] = []
    for port_data in host_data.get("ports", []):
        svc = _normalize_service(port_data)
        if svc is not None:
            services.append(svc)

    segment = _infer_segment(host_data)

    try:
        return Host(
            ip=ip,
            hostname=host_data.get("hostname"),
            state=host_data.get("state") or "unknown",
            segment=segment,
            services=services,
            vulnerabilities=[],  # Future: populated by vulnerability scanner
            credentials=[],      # Future: populated by credential scanner
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to create Host from data %s: %s", host_data, exc)
        return None


# ─── Main Normalization Pipeline ──────────────────────────────────────────────

def normalize(
    parsed_hosts: list[dict[str, Any]],
    target_scope: str,
    scan_id: str | None = None,
    timestamp: datetime | None = None,
) -> ScanResult:
    """
    Convert a list of parsed host dicts into a validated ScanResult.

    This is the central normalization function called by the scan pipeline.

    Args:
        parsed_hosts: Output from xml_parser.parse_nmap_xml()
        target_scope: The scan target (CIDR or host), e.g. '172.20.0.0/24'
        scan_id: Optional pre-generated scan ID. Auto-generated if None.
        timestamp: Optional UTC timestamp. Defaults to now(UTC).

    Returns:
        Validated ScanResult ready for Redis publication.

    Raises:
        ValueError: If the resulting ScanResult fails Pydantic validation
                    (this should not happen under normal operation).
    """
    sid = scan_id or generate_scan_id()
    ts = timestamp or datetime.now(UTC)

    hosts: list[Host] = []
    skipped = 0

    for host_data in parsed_hosts:
        host = _normalize_host(host_data)
        if host is not None:
            hosts.append(host)
        else:
            skipped += 1

    if skipped > 0:
        logger.warning("Skipped %d invalid host(s) during normalization", skipped)

    total_services = sum(len(h.services) for h in hosts)
    logger.info(
        "Normalization complete | scan_id=%s | hosts=%d | services=%d",
        sid, len(hosts), total_services,
    )

    # Pydantic validation happens here — raises ValidationError if invalid
    result = ScanResult(
        scan_id=sid,
        timestamp=ts,
        scanner="nmap",
        target_scope=target_scope,
        hosts=hosts,
    )

    return result
