"""
AttackGraphX — Report routes

GET /reports/pdf?target=<str>  — Auth required
GET /reports/csv               — Auth required
"""
import io
from datetime import datetime, timezone
from typing import Annotated, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from app.auth.dependencies import get_current_user
from app.services.analysis_client import analysis_client, AnalysisServiceError
from app.services.cache_service import cache_service
from app.services.report_service import generate_csv, generate_pdf

log = structlog.get_logger(__name__)
router = APIRouter(tags=["Reports"])


async def _load_data_for_report(target: str) -> tuple[list, list]:
    """
    Load paths and patches for report generation.
    Falls back to Redis cache if the analysis service is unavailable.
    """
    # Paths
    try:
        paths = await analysis_client.get_paths(target)
    except AnalysisServiceError:
        cached = await cache_service.get(cache_service.paths_key(target))
        paths = cached if cached is not None else []

    # Patches
    try:
        patches = await analysis_client.get_patches()
    except AnalysisServiceError:
        cached = await cache_service.get(cache_service.patches_key())
        patches = cached if cached is not None else []

    return paths, patches


@router.get("/reports/pdf", summary="Download executive security assessment PDF report")
async def download_pdf_report(
    target: Optional[str] = Query(default="all", description="Target host filter"),
    _user: Annotated[dict, Depends(get_current_user)] = None,
):
    log.info("PDF report requested", user=_user.get("sub"), target=target)
    try:
        paths, patches = await _load_data_for_report(target or "all")
        pdf_bytes = generate_pdf(paths, patches, target or "all")
        log.info("PDF report generated", paths=len(paths), patches=len(patches))
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"attackgraphx-report-{target or 'all'}-{timestamp}.pdf"
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as exc:
        log.error("PDF generation failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "REPORT_GENERATION_FAILED",
                "message": "Failed to generate PDF report. Please try again.",
            },
        )


@router.get("/reports/csv", summary="Download raw attack telemetry CSV export")
async def download_csv_report(
    _user: Annotated[dict, Depends(get_current_user)] = None,
):
    log.info("CSV report requested", user=_user.get("sub"))
    try:
        paths, _ = await _load_data_for_report("all")
        csv_content = generate_csv(paths)
        log.info("CSV report generated", paths=len(paths))
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"attackgraphx-telemetry-{timestamp}.csv"
        return StreamingResponse(
            io.StringIO(csv_content),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as exc:
        log.error("CSV generation failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "REPORT_GENERATION_FAILED",
                "message": "Failed to generate CSV export. Please try again.",
            },
        )
