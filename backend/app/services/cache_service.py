"""
AttackGraphX — Redis last-known-good cache service.

Purpose:
  If the analysis service is unavailable, the frontend receives the most
  recent valid result with status='stale_cache' rather than crashing.

Cache keys:
  paths:{target}
  patches
  simulate:{vulnerability_id}
"""
import json
from typing import Any

import redis.asyncio as aioredis
import structlog

from app.config import get_settings

log = structlog.get_logger(__name__)
settings = get_settings()


class CacheService:
    """Async Redis cache wrapper for last-known-good data persistence."""

    def __init__(self):
        self._url = settings.redis_url
        self._ttl = settings.redis_ttl
        self._client: aioredis.Redis | None = None

    def _get_client(self) -> aioredis.Redis:
        if self._client is None:
            self._client = aioredis.from_url(
                self._url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
            )
        return self._client

    async def get(self, key: str) -> Any | None:
        """Retrieve a cached value. Returns None if missing or Redis unavailable."""
        try:
            client = self._get_client()
            raw = await client.get(key)
            if raw is None:
                return None
            return json.loads(raw)
        except Exception as exc:
            log.warning("Redis GET failed", key=key, error=str(exc))
            return None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """Store a value in Redis. Returns False on failure (non-fatal)."""
        try:
            client = self._get_client()
            await client.setex(key, ttl or self._ttl, json.dumps(value))
            log.debug("Cache SET", key=key, ttl=ttl or self._ttl)
            return True
        except Exception as exc:
            log.warning("Redis SET failed", key=key, error=str(exc))
            return False

    async def ping(self) -> bool:
        """Returns True if Redis is reachable."""
        try:
            client = self._get_client()
            return await client.ping()
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Convenience key builders
    # ------------------------------------------------------------------

    @staticmethod
    def paths_key(target: str) -> str:
        return f"paths:{target}"

    @staticmethod
    def patches_key() -> str:
        return "patches"

    @staticmethod
    def simulate_key(vulnerability_id: str) -> str:
        return f"simulate:{vulnerability_id}"


# Module-level singleton
cache_service = CacheService()
