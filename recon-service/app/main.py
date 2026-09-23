"""
AttackGraphX Recon Service — FastAPI Application Entry Point
=============================================================

Startup sequence:
  1. Configure structured logging
  2. Register API routers
  3. Start APScheduler for periodic scans (if SCAN_INTERVAL_MINUTES > 0)
  4. Serve via Uvicorn

This module does NOT contain business logic — delegate to api/, scanner/,
normalizer/, publisher/.
"""

from __future__ import annotations

import logging
import logging.config
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

# ─── Logging Setup ────────────────────────────────────────────────────────────

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
logger = logging.getLogger(__name__)

# ─── Global State ─────────────────────────────────────────────────────────────
# Minimal shared state — avoids circular imports by keeping this here.
_state: dict[str, Any] = {
    "last_successful_scan": None,
}

# ─── Scheduler ────────────────────────────────────────────────────────────────

_scheduler = AsyncIOScheduler(timezone="UTC")


async def _scheduled_scan_job() -> None:
    """
    Periodic scan job — uses the same pipeline as POST /scan.
    Does NOT use BackgroundTasks (not inside a request context).
    """
    from app.api.scan import _run_scan_pipeline
    from app.normalizer.normalizer import generate_scan_id

    scan_id = generate_scan_id()
    target = settings.scan_default_target

    logger.info("Scheduled scan triggered | scan_id=%s | target=%s", scan_id, target)

    # Register in store so /scans shows scheduled runs too
    from app.api.scan import _scan_store
    from app.models.scan_models import ScanStatus

    _scan_store[scan_id] = ScanStatus(
        scan_id=scan_id,
        status="queued",
        target=target,
    )

    await _run_scan_pipeline(scan_id, target)


# ─── Lifespan ────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan: start scheduler on startup, stop on shutdown."""
    logger.info(
        "Starting %s v%s | range_cidr=%s | redis_topic=%s",
        settings.app_name,
        settings.app_version,
        settings.range_cidr,
        settings.redis_topic,
    )

    # Start periodic scanner if configured
    if settings.scan_interval_minutes > 0:
        _scheduler.add_job(
            _scheduled_scan_job,
            trigger="interval",
            minutes=settings.scan_interval_minutes,
            id="periodic_scan",
            replace_existing=True,
            next_run_time=None,  # Don't run immediately on startup
        )
        _scheduler.start()
        logger.info(
            "Scheduler started | interval=%d minutes | target=%s",
            settings.scan_interval_minutes,
            settings.scan_default_target,
        )
    else:
        logger.info("Scheduler disabled (SCAN_INTERVAL_MINUTES=0)")

    yield  # Application runs here

    # ── Shutdown ──────────────────────────────────────────────────────────
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")

    logger.info("Recon Service shutdown complete")


# ─── App Factory ──────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "AttackGraphX Person 1 — Recon Service. "
            "Scans the controlled Docker lab range using Nmap and publishes "
            "standardized scan results to Redis for the Analysis Service."
        ),
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS — allow all for lab/development use
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Register routers ──────────────────────────────────────────────────
    from app.api.health import router as health_router
    from app.api.scan import router as scan_router

    app.include_router(scan_router, prefix="")
    app.include_router(health_router, prefix="")

    # ── Root endpoint ─────────────────────────────────────────────────────
    @app.get("/", tags=["root"], summary="Service info")
    async def root() -> dict[str, str]:
        return {
            "service": settings.app_name,
            "version": settings.app_version,
            "status": "running",
            "docs": "/docs",
            "health": "/health",
        }

    return app


# ─── Application Instance ─────────────────────────────────────────────────────

app = create_app()


# ─── Dev Runner ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level=settings.log_level.lower(),
    )
