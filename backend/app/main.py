"""
AttackGraphX API Gateway — FastAPI Application Entry Point
"""
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.auth.routes import router as auth_router
from app.routes.paths import router as paths_router
from app.routes.whatif import router as whatif_router
from app.routes.reports import router as reports_router
from app.routes.health import router as health_router

log = structlog.get_logger(__name__)
settings = get_settings()


# ---------------------------------------------------------------------------
# Lifespan — startup / shutdown
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("AttackGraphX API Gateway starting", port=settings.api_port)
    yield
    log.info("AttackGraphX API Gateway shutting down")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="AttackGraphX API Gateway",
    description=(
        "Person 3 — API Gateway & Dashboard Service. "
        "Provides JWT auth, RBAC, resilient proxying of the analysis service, "
        "Redis caching, and PDF/CSV report generation."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS — restrict to the configured frontend origin only
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(auth_router)
app.include_router(health_router)
app.include_router(paths_router)
app.include_router(whatif_router)
app.include_router(reports_router)


# ---------------------------------------------------------------------------
# Global exception handler — never expose stack traces to the frontend
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    log.error("Unhandled gateway exception", path=request.url.path, error=str(exc))
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "GATEWAY_ERROR",
                "message": "An unexpected gateway error occurred.",
                "status": "unavailable",
            }
        },
    )


# ---------------------------------------------------------------------------
# Root — basic liveness probe (also covered by /health)
# ---------------------------------------------------------------------------
@app.get("/", tags=["root"], include_in_schema=False)
async def root():
    return {"service": "AttackGraphX API Gateway", "status": "running"}
