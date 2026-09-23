"""
AttackGraphX Recon Service — Redis Publisher
=============================================
Publishes validated ScanResult JSON to Redis Streams.

Uses Redis Streams (XADD) rather than Pub/Sub so that:
  - Messages are durable (not lost if Person 2 is temporarily offline)
  - Person 2 can use consumer groups for reliable processing
  - Messages can be replayed for debugging

Stream key: scan_results  (configurable via REDIS_TOPIC)

Person 2 reads from this stream using XREAD or consumer groups.
This module does NOT call Person 2's API — Redis is the only coupling point.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import redis.asyncio as aioredis
from redis.asyncio import Redis
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import RedisError, TimeoutError as RedisTimeoutError

from app.config import settings
from app.models.scan_models import ScanResult

logger = logging.getLogger(__name__)


# ─── Custom Exception ─────────────────────────────────────────────────────────

class RedisPublishError(RuntimeError):
    """Raised when a scan result cannot be published to Redis after all retries."""


# ─── Redis Client Factory ─────────────────────────────────────────────────────

def _create_redis_client() -> Redis:
    """Create an async Redis client from settings."""
    return aioredis.from_url(
        settings.redis_url,
        socket_connect_timeout=settings.redis_connect_timeout,
        decode_responses=True,
    )


# ─── Health Check ─────────────────────────────────────────────────────────────

async def check_redis_connection() -> bool:
    """
    Attempt a lightweight PING to verify Redis connectivity.
    Used by GET /health — does not publish anything.

    Returns True if Redis is reachable, False otherwise.
    """
    client: Redis | None = None
    try:
        client = _create_redis_client()
        await asyncio.wait_for(client.ping(), timeout=settings.redis_connect_timeout)
        return True
    except (RedisConnectionError, RedisTimeoutError, RedisError, asyncio.TimeoutError) as exc:
        logger.warning("Redis health check failed: %s", exc)
        return False
    finally:
        if client is not None:
            await client.aclose()


# ─── Publisher ────────────────────────────────────────────────────────────────

async def publish_scan_result(scan_result: ScanResult) -> str:
    """
    Serialize and publish a validated ScanResult to the Redis Stream.

    Uses Redis XADD for durability. Retries up to settings.redis_max_retries
    times with a 1-second backoff between attempts.

    Args:
        scan_result: A fully validated ScanResult Pydantic model.

    Returns:
        The Redis stream entry ID (e.g., '1727000000000-0') on success.

    Raises:
        RedisPublishError: If all retry attempts fail.
    """
    # Serialize to JSON — uses Pydantic's model_dump_json for proper datetime handling
    payload = scan_result.model_dump_json()

    topic = settings.redis_topic
    max_retries = settings.redis_max_retries
    last_exc: Exception | None = None

    for attempt in range(1, max_retries + 1):
        client: Redis | None = None
        try:
            client = _create_redis_client()

            # XADD to Redis Stream
            # Fields: {"data": "<json>", "scan_id": "<id>"} for easy filtering
            entry_id = await client.xadd(
                name=topic,
                fields={
                    "data": payload,
                    "scan_id": scan_result.scan_id,
                    "target": scan_result.target_scope,
                },
            )

            logger.info(
                "Published to Redis | scan_id=%s | stream=%s | entry_id=%s",
                scan_result.scan_id,
                topic,
                entry_id,
            )
            return str(entry_id)

        except (RedisConnectionError, RedisTimeoutError) as exc:
            last_exc = exc
            logger.warning(
                "Redis connection failed (attempt %d/%d) | scan_id=%s | error=%s",
                attempt,
                max_retries,
                scan_result.scan_id,
                exc,
            )

        except RedisError as exc:
            last_exc = exc
            logger.error(
                "Redis error (attempt %d/%d) | scan_id=%s | error=%s",
                attempt,
                max_retries,
                scan_result.scan_id,
                exc,
            )

        finally:
            if client is not None:
                await client.aclose()

        # Wait before retry (skip sleep after last attempt)
        if attempt < max_retries:
            await asyncio.sleep(1.0)

    # All retries exhausted
    raise RedisPublishError(
        f"Failed to publish scan_id={scan_result.scan_id} to Redis stream "
        f"'{topic}' after {max_retries} attempts. Last error: {last_exc}"
    )


# ─── Convenience: Read Back (for integration testing) ─────────────────────────

async def read_latest_from_stream(
    count: int = 5,
    topic: str | None = None,
) -> list[dict[str, Any]]:
    """
    Read the latest entries from the scan_results Redis Stream.

    This is a convenience function used by integration tests to verify
    that published data is readable and correct.

    Args:
        count: Maximum number of entries to return
        topic: Stream key override (defaults to settings.redis_topic)

    Returns:
        List of dicts with keys: entry_id, scan_id, data (raw JSON string)
    """
    stream_key = topic or settings.redis_topic
    client: Redis | None = None

    try:
        client = _create_redis_client()
        # XREVRANGE gives latest entries first
        entries = await client.xrevrange(stream_key, count=count)

        results = []
        for entry_id, fields in entries:
            results.append({
                "entry_id": entry_id,
                "scan_id": fields.get("scan_id", ""),
                "target": fields.get("target", ""),
                "data": fields.get("data", ""),
            })
        return results

    except RedisError as exc:
        logger.error("Failed to read from Redis stream '%s': %s", stream_key, exc)
        return []
    finally:
        if client is not None:
            await client.aclose()
