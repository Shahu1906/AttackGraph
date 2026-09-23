"""
AttackGraphX Recon Service — Nmap XML Parser
=============================================
Converts raw Nmap XML output into Python dicts.

This module understands Nmap's XML schema.
It does NOT know about the AttackGraphX scan contract — that is normalizer.py.

Uses defusedxml to prevent XXE (XML External Entity) attacks.
All fields are treated as optional and missing fields are handled gracefully.
"""

from __future__ import annotations

import logging
from typing import Any

import defusedxml.ElementTree as ET

logger = logging.getLogger(__name__)


# ─── Custom Exceptions ────────────────────────────────────────────────────────

class XmlParseError(ValueError):
    """Raised when the Nmap XML cannot be parsed."""


# ─── Internal Helpers ─────────────────────────────────────────────────────────

def _get_text(element: Any, attr: str, default: str | None = None) -> str | None:
    """Safely get an attribute value from an XML element."""
    if element is None:
        return default
    return element.get(attr, default)


def _parse_service(port_elem: Any) -> dict[str, Any]:
    """
    Extract service information from a <port> element.

    Example Nmap XML:
        <service name="http" product="nginx" version="1.25.0" extrainfo="..." />

    Returns a dict with: name, product, version, extra_info
    """
    service_elem = port_elem.find("service")
    if service_elem is None:
        return {
            "name": None,
            "product": None,
            "version": None,
            "extra_info": None,
        }

    return {
        "name": _get_text(service_elem, "name"),
        "product": _get_text(service_elem, "product"),
        "version": _get_text(service_elem, "version"),
        "extra_info": _get_text(service_elem, "extrainfo"),
    }


def _parse_port(port_elem: Any) -> dict[str, Any]:
    """
    Extract a single port's data from a <port> element.

    Example Nmap XML:
        <port protocol="tcp" portid="80">
            <state state="open" reason="syn-ack"/>
            <service name="http" product="nginx" .../>
        </port>
    """
    portid = _get_text(port_elem, "portid", "0")
    protocol = _get_text(port_elem, "protocol", "tcp")

    state_elem = port_elem.find("state")
    state = _get_text(state_elem, "state", "unknown") if state_elem is not None else "unknown"

    service_info = _parse_service(port_elem)

    return {
        "port": int(portid) if portid and portid.isdigit() else 0,
        "protocol": protocol or "tcp",
        "state": state or "unknown",
        **service_info,
    }


def _parse_host(host_elem: Any) -> dict[str, Any]:
    """
    Extract all information from a <host> element.

    Example Nmap XML:
        <host>
            <status state="up"/>
            <address addr="172.20.0.10" addrtype="ipv4"/>
            <hostnames><hostname name="web-server" type="PTR"/></hostnames>
            <ports>
                <port ...>...</port>
            </ports>
        </host>

    Returns a dict matching the AttackGraphX host structure.
    """
    # ── Host state ──────────────────────────────────────────────────────────
    status_elem = host_elem.find("status")
    host_state = _get_text(status_elem, "state", "unknown") if status_elem is not None else "unknown"

    # ── IP address ──────────────────────────────────────────────────────────
    ip_address: str | None = None
    for addr_elem in host_elem.findall("address"):
        addr_type = _get_text(addr_elem, "addrtype", "")
        if addr_type in ("ipv4", "ipv6"):
            ip_address = _get_text(addr_elem, "addr")
            break

    if not ip_address:
        # Fallback: grab any address element
        addr_elem = host_elem.find("address")
        ip_address = _get_text(addr_elem, "addr") if addr_elem is not None else None

    # ── Hostname ────────────────────────────────────────────────────────────
    hostname: str | None = None
    hostnames_elem = host_elem.find("hostnames")
    if hostnames_elem is not None:
        hostname_elem = hostnames_elem.find("hostname")
        if hostname_elem is not None:
            hostname = _get_text(hostname_elem, "name")

    # ── Ports ───────────────────────────────────────────────────────────────
    ports: list[dict[str, Any]] = []
    ports_elem = host_elem.find("ports")
    if ports_elem is not None:
        for port_elem in ports_elem.findall("port"):
            try:
                port_data = _parse_port(port_elem)
                ports.append(port_data)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Skipping malformed port element: %s", exc)

    return {
        "ip": ip_address,
        "hostname": hostname,
        "state": host_state,
        "ports": ports,
    }


# ─── Public API ───────────────────────────────────────────────────────────────

def parse_nmap_xml(xml_string: str) -> list[dict[str, Any]]:
    """
    Parse raw Nmap XML output and return a list of host dicts.

    Each dict contains: ip, hostname, state, ports (list of port dicts).
    Each port dict contains: port, protocol, state, name, product, version, extra_info.

    Args:
        xml_string: Raw XML string from `nmap -oX -`

    Returns:
        List of host dicts. Empty list if no hosts found.

    Raises:
        XmlParseError: If the XML is malformed and cannot be parsed at all.
    """
    if not xml_string or not xml_string.strip():
        logger.warning("Empty XML string passed to parser — returning empty host list")
        return []

    try:
        root = ET.fromstring(xml_string)
    except ET.ParseError as exc:
        raise XmlParseError(f"Failed to parse Nmap XML: {exc}") from exc
    except Exception as exc:
        raise XmlParseError(f"Unexpected error parsing Nmap XML: {exc}") from exc

    hosts: list[dict[str, Any]] = []

    for host_elem in root.findall("host"):
        try:
            host_data = _parse_host(host_elem)

            # Skip hosts without an IP address (shouldn't happen, but be safe)
            if not host_data.get("ip"):
                logger.warning("Skipping host element with no IP address")
                continue

            hosts.append(host_data)
            logger.debug(
                "Parsed host: ip=%s state=%s ports=%d",
                host_data.get("ip"),
                host_data.get("state"),
                len(host_data.get("ports", [])),
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Skipping malformed host element: %s", exc)

    logger.info("Parsed %d host(s) from Nmap XML", len(hosts))
    return hosts
