"""
AttackGraphX Recon Service — Canonical Scan Data Models
=========================================================
These Pydantic models define the stable JSON contract that
Person 2 (Analysis Service) consumes from Redis.

IMPORTANT: Do NOT change field names without coordinating with Person 2.
The contract is the interface boundary between Person 1 and Person 2.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


# ─── Service ──────────────────────────────────────────────────────────────────

class Service(BaseModel):
    """A single network service discovered on a host port."""

    port: int = Field(..., ge=1, le=65535, description="TCP/UDP port number")
    protocol: str = Field(..., description="Network protocol, e.g. 'tcp' or 'udp'")
    state: str = Field(..., description="Port state: open | closed | filtered")
    name: str | None = Field(default=None, description="Service name, e.g. 'http', 'ftp'")
    product: str | None = Field(default=None, description="Service product name, e.g. 'nginx'")
    version: str | None = Field(default=None, description="Service version string")
    extra_info: str | None = Field(default=None, description="Additional banner/info from Nmap")

    @field_validator("protocol")
    @classmethod
    def protocol_lowercase(cls, v: str) -> str:
        return v.lower().strip()

    @field_validator("state")
    @classmethod
    def state_lowercase(cls, v: str) -> str:
        return v.lower().strip()


# ─── Host ─────────────────────────────────────────────────────────────────────

class Host(BaseModel):
    """A discovered host with its services."""

    ip: str = Field(..., description="IP address of the host")
    hostname: str | None = Field(default=None, description="Resolved hostname if available")
    state: str = Field(..., description="Host state: up | down | unknown")
    segment: str | None = Field(
        default=None,
        description="Network segment label, e.g. 'web', 'ftp', 'internal'",
    )
    services: list[Service] = Field(default_factory=list)
    vulnerabilities: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Reserved for future vulnerability data. Initially always empty.",
    )
    credentials: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Reserved for future credential data. Initially always empty.",
    )

    @field_validator("state")
    @classmethod
    def state_lowercase(cls, v: str) -> str:
        return v.lower().strip()

    @field_validator("ip")
    @classmethod
    def ip_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("IP address must not be empty")
        return v


# ─── ScanResult ───────────────────────────────────────────────────────────────

class ScanResult(BaseModel):
    """
    Top-level scan result published to Redis.
    This is the canonical AttackGraphX scan contract.
    """

    scan_id: str = Field(..., description="Unique scan identifier, e.g. 'scan-<uuid8>'")
    timestamp: datetime = Field(..., description="UTC time when scan completed")
    scanner: Literal["nmap"] = Field(default="nmap", description="Scanner that produced this result")
    target_scope: str = Field(..., description="The scan target CIDR or host")
    hosts: list[Host] = Field(default_factory=list, description="All discovered hosts")

    def summary(self) -> dict[str, Any]:
        """Return a brief summary for logging."""
        total_services = sum(len(h.services) for h in self.hosts)
        return {
            "scan_id": self.scan_id,
            "target_scope": self.target_scope,
            "hosts_found": len(self.hosts),
            "services_found": total_services,
            "timestamp": self.timestamp.isoformat(),
        }


# ─── Scan Status (in-memory tracking) ────────────────────────────────────────

class ScanStatus(BaseModel):
    """Tracks the lifecycle of a single scan request."""

    scan_id: str
    status: Literal["queued", "running", "completed", "failed"]
    target: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None
    hosts_found: int = 0
    services_found: int = 0
    redis_published: bool = False


# ─── API Request/Response models ──────────────────────────────────────────────

class ScanRequest(BaseModel):
    """Incoming POST /scan request body."""

    target: str = Field(
        ...,
        description="Target CIDR or IP to scan. Must be within the authorized lab range.",
        examples=["172.20.0.0/24", "172.20.0.10"],
    )


class ScanResponse(BaseModel):
    """Response returned immediately from POST /scan."""

    scan_id: str
    status: str
    message: str


class HealthResponse(BaseModel):
    """GET /health response."""

    status: Literal["healthy", "degraded"]
    scanner: Literal["available", "unavailable"]
    redis: Literal["connected", "disconnected"]
    last_successful_scan: datetime | None = None
    version: str = "1.0.0"
