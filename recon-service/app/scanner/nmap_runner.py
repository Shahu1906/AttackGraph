"""
AttackGraphX Recon Service — Nmap Runner
=========================================
Responsible ONLY for executing Nmap and returning raw XML.

This module does NOT parse XML — that is xml_parser.py's job.
This module does NOT build the scan contract — that is normalizer.py's job.

Safety: All targets are validated against the authorized RANGE_CIDR
        before Nmap is invoked. shell=False enforced throughout.
"""

from __future__ import annotations

import ipaddress
import logging
import shutil
import subprocess
from typing import TYPE_CHECKING

from app.config import settings

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


# ─── Custom Exceptions ────────────────────────────────────────────────────────

class NmapNotFoundError(RuntimeError):
    """Raised when the nmap binary is not found on PATH."""


class NmapExecutionError(RuntimeError):
    """Raised when nmap exits with a non-zero status."""


class NmapTimeoutError(RuntimeError):
    """Raised when nmap exceeds the configured timeout."""


class InvalidTargetError(ValueError):
    """Raised when the scan target is outside the authorized CIDR range."""


# ─── Target Validation ────────────────────────────────────────────────────────

def _parse_network(cidr: str) -> ipaddress.IPv4Network:
    """Parse a CIDR string into an IPv4Network (strict=False allows host bits)."""
    return ipaddress.IPv4Network(cidr, strict=False)


def validate_target(target: str, authorized_cidr: str | None = None) -> None:
    """
    Ensure the scan target is within the authorized lab CIDR range.

    Raises InvalidTargetError if the target is not permitted.

    Args:
        target: IP address or CIDR to validate, e.g. '172.20.0.10' or '172.20.0.0/24'
        authorized_cidr: Override for the authorized range (defaults to settings.range_cidr)
    """
    cidr = authorized_cidr or settings.range_cidr

    try:
        authorized_net = _parse_network(cidr)
    except ValueError as exc:
        raise InvalidTargetError(f"Authorized CIDR '{cidr}' is invalid: {exc}") from exc

    # Target can be a single IP or a CIDR subnet
    try:
        target_net = _parse_network(target)
    except ValueError as exc:
        raise InvalidTargetError(f"Target '{target}' is not a valid IP/CIDR: {exc}") from exc

    # Subnet containment: every address in target_net must be in authorized_net
    if not authorized_net.supernet_of(target_net):
        raise InvalidTargetError(
            f"Target '{target}' is outside the authorized lab range '{cidr}'. "
            "Scanning outside the controlled lab network is not permitted."
        )

    logger.debug("Target '%s' validated against authorized range '%s'", target, cidr)


# ─── Nmap Discovery ───────────────────────────────────────────────────────────

def _nmap_binary() -> str:
    """
    Return the path to the nmap binary, or raise NmapNotFoundError.
    Uses shutil.which so the check works cross-platform.
    """
    path = shutil.which("nmap")
    if path is None:
        raise NmapNotFoundError(
            "nmap binary not found on PATH. "
            "Install nmap: https://nmap.org/download.html"
        )
    return path


def _build_nmap_command(target: str, extra_flags: str | None = None) -> list[str]:
    """
    Build the nmap argument list.

    Args:
        target: Validated scan target
        extra_flags: Space-separated flags string, e.g. '-sV -T4'.
                     Defaults to settings.nmap_scan_flags.

    Returns:
        Argument list safe for subprocess (no shell=True required).
    """
    flags_str = extra_flags if extra_flags is not None else settings.nmap_scan_flags

    # Split flags safely — no shell interpolation
    flags: list[str] = [f for f in flags_str.strip().split() if f]

    # -oX - : output XML to stdout
    cmd = [_nmap_binary()] + flags + ["-oX", "-", target]

    logger.debug("Nmap command: %s", " ".join(cmd))
    return cmd


# ─── Main Runner ──────────────────────────────────────────────────────────────

def run_nmap(
    target: str,
    extra_flags: str | None = None,
    timeout: int | None = None,
) -> str:
    """
    Validate target, run nmap, and return the raw XML output.

    Args:
        target: IP address or CIDR to scan (must be within authorized range)
        extra_flags: Optional nmap flags override
        timeout: Override for nmap timeout in seconds

    Returns:
        Raw Nmap XML string (stdout from nmap -oX -)

    Raises:
        InvalidTargetError: Target outside authorized range
        NmapNotFoundError: nmap not installed
        NmapExecutionError: nmap exited with non-zero return code
        NmapTimeoutError: nmap exceeded timeout
    """
    validate_target(target)

    cmd = _build_nmap_command(target, extra_flags)
    timeout_secs = timeout if timeout is not None else settings.nmap_timeout_seconds

    logger.info("Starting nmap scan | target=%s | flags=%s | timeout=%ds",
                target, extra_flags or settings.nmap_scan_flags, timeout_secs)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_secs,
            shell=False,   # Explicitly never use shell=True
        )
    except FileNotFoundError as exc:
        raise NmapNotFoundError(
            f"nmap binary not found when executing: {' '.join(cmd)}"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise NmapTimeoutError(
            f"nmap timed out after {timeout_secs}s scanning '{target}'"
        ) from exc

    if result.returncode != 0:
        stderr_snippet = (result.stderr or "")[:500]
        raise NmapExecutionError(
            f"nmap exited with code {result.returncode}. "
            f"Target: {target}. stderr: {stderr_snippet}"
        )

    xml_output = result.stdout.strip()
    if not xml_output:
        raise NmapExecutionError(
            f"nmap produced no XML output for target '{target}'. "
            "Check that nmap is functioning correctly."
        )

    logger.info("nmap scan completed | target=%s | xml_bytes=%d", target, len(xml_output))
    return xml_output


def is_nmap_available() -> bool:
    """Check if nmap is available on this system (used by /health endpoint)."""
    try:
        _nmap_binary()
        return True
    except NmapNotFoundError:
        return False
