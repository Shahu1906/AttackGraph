"""
AttackGraphX — Async HTTP client for the upstream Analysis Service.

Responsibilities:
- Forwards requests to the analysis service
- Implements configurable retry with exponential backoff
- Translates all errors into AnalysisServiceError
- Never exposes internal stack traces to the API layer
"""
import asyncio
from typing import Any

import httpx
import structlog

from app.config import get_settings

log = structlog.get_logger(__name__)
settings = get_settings()

# Retry delays in seconds (attempt 1, 2, 3)
_RETRY_DELAYS = [0.5, 1.0, 2.0]


class AnalysisServiceError(Exception):
    """Raised when the analysis service is unreachable or returns an error after all retries."""

    def __init__(self, message: str = "Analysis service unavailable"):
        super().__init__(message)
        self.message = message


class AnalysisServiceClient:
    """Async HTTP client that proxies requests to the upstream analysis service."""

    def __init__(self):
        self._base_url = settings.analysis_service_url.rstrip("/")
        self._timeout = httpx.Timeout(
            connect=5.0,
            read=settings.analysis_timeout,
            write=5.0,
            pool=5.0,
        )
        self._max_retries = min(settings.analysis_retries, len(_RETRY_DELAYS))

    async def _request(self, method: str, path: str, **kwargs) -> Any:
        """
        Return parsed JSON from an upstream request after bounded retries.

        Timeouts, connection failures, and non-success HTTP responses are retried
        with exponential backoff, then translated to ``AnalysisServiceError``.
        """
        url = f"{self._base_url}{path}"
        last_error: Exception | None = None

        for attempt in range(self._max_retries):
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    response = await client.request(method, url, **kwargs)
                    response.raise_for_status()
                    return response.json()
            except httpx.TimeoutException as exc:
                last_error = exc
                log.warning(
                    "Analysis service timeout",
                    attempt=attempt + 1,
                    url=url,
                )
            except httpx.HTTPStatusError as exc:
                last_error = exc
                log.warning(
                    "Analysis service HTTP error",
                    attempt=attempt + 1,
                    status=exc.response.status_code,
                    url=url,
                )
            except (httpx.ConnectError, httpx.RequestError) as exc:
                last_error = exc
                log.warning(
                    "Analysis service connection error",
                    attempt=attempt + 1,
                    url=url,
                )

            # Wait before retry (skip wait on last attempt)
            if attempt < self._max_retries - 1:
                delay = _RETRY_DELAYS[attempt]
                log.info("Retrying analysis service request", delay=delay, attempt=attempt + 1)
                await asyncio.sleep(delay)

        log.error("Analysis service unavailable after all retries", url=url)
        raise AnalysisServiceError()

    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------

    async def get_paths(self, target: str = "all") -> list:
        """Return attack paths, accepting either a bare list or a wrapped upstream payload."""
        params = {}
        if target and target != "all":
            params["target"] = target
        result = await self._request("GET", "/paths", params=params)
        # Accept both {data: [...]} and [...] shapes from the analysis service
        if isinstance(result, dict):
            return result.get("data", result.get("paths", []))
        return result if isinstance(result, list) else []

    async def get_patches(self) -> list:
        """Return patches, accepting either a bare list or a wrapped upstream payload."""
        result = await self._request("GET", "/patches")
        if isinstance(result, dict):
            return result.get("data", result.get("patches", []))
        return result if isinstance(result, list) else []

    async def simulate_fix(self, vulnerability_id: str) -> dict:
        """Request the modeled impact of fixing one vulnerability."""
        return await self._request(
            "POST",
            "/simulate",
            json={"vulnerability_id": vulnerability_id},
        )

    async def reset_simulation(self) -> dict:
        """Request removal of all active upstream simulations."""
        return await self._request("POST", "/simulate/reset")

    async def get_scan_status(self) -> dict:
        """Return the upstream infrastructure-scan status payload."""
        return await self._request("GET", "/scan/status")

    async def trigger_scan(self) -> dict:
        """Request an upstream infrastructure scan."""
        return await self._request("GET", "/scan/trigger")

    async def health_check(self) -> bool:
        """Returns True if the analysis service responds to a health probe."""
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(3.0)) as client:
                resp = await client.get(f"{self._base_url}/health")
                return resp.status_code < 500
        except Exception:
            return False


# Module-level singleton
analysis_client = AnalysisServiceClient()
