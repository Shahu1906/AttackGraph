"""
AttackGraphX Recon Service — Application Configuration
=======================================================
All settings are loaded from environment variables.
Use .env.example as a template for your .env file.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """
    All configuration values for the Recon Service.
    Values are read from environment variables (case-insensitive).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ────────────────────────────────────────────────────────
    app_name: str = Field(default="AttackGraphX Recon Service")
    app_version: str = Field(default="1.0.0")
    log_level: str = Field(default="INFO")
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)

    # ── Redis ──────────────────────────────────────────────────────────────
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Full Redis connection URL",
    )
    redis_topic: str = Field(
        default="scan_results",
        description="Redis Stream key where scan results are published",
    )
    redis_connect_timeout: int = Field(
        default=5,
        description="Seconds to wait for Redis connection",
    )
    redis_max_retries: int = Field(
        default=3,
        description="Max publish retry attempts before giving up",
    )

    # ── Network / Scan Scope ───────────────────────────────────────────────
    range_network: str = Field(
        default="attackgraphx-net",
        description="Docker network name for the attack range",
    )
    range_cidr: str = Field(
        default="172.20.0.0/24",
        description="Authorized CIDR block. Scans outside this block are rejected.",
    )

    # ── Nmap ───────────────────────────────────────────────────────────────
    nmap_scan_flags: str = Field(
        default="-sV",
        description="Nmap flags. Default: service version detection only.",
    )
    nmap_timeout_seconds: int = Field(
        default=300,
        description="Max seconds to wait for Nmap to complete",
    )

    # ── Scheduler ─────────────────────────────────────────────────────────
    scan_interval_minutes: int = Field(
        default=30,
        description="How often the scheduled scan runs (0 = disabled)",
    )
    scan_default_target: str = Field(
        default="172.20.0.0/24",
        description="Default target CIDR for scheduled scans",
    )


# Single shared settings instance — import this everywhere
settings = Settings()
