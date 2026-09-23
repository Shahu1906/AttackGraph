"""
AttackGraphX — Centralised API error helpers.
Provides consistent error response shapes that the frontend can parse.
"""
from fastapi import HTTPException
from fastapi.responses import JSONResponse


def api_error_response(
    code: str,
    message: str,
    status_code: int = 500,
    status: str = "unavailable",
) -> JSONResponse:
    """
    Returns a JSONResponse with the standard error envelope:
      {"error": {"code": "...", "message": "...", "status": "..."}}
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "status": status,
            }
        },
    )


def raise_api_error(code: str, message: str, status_code: int = 500) -> None:
    """Raises an HTTPException with a standard detail envelope."""
    raise HTTPException(
        status_code=status_code,
        detail={"code": code, "message": message},
    )
