"""
AttackGraphX — FastAPI dependencies for authentication & RBAC
"""
from typing import Annotated

import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.jwt import verify_token

log = structlog.get_logger(__name__)

# Extracts Bearer token from Authorization header
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> dict:
    """
    Dependency: validates JWT and returns the decoded payload.
    Raises 401 if no/invalid/expired token is provided.
    """
    if credentials is None:
        log.warning("Missing authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return verify_token(credentials.credentials)


def require_admin(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    """
    Dependency: requires admin role.
    Raises 403 if authenticated user is not an admin.
    """
    if current_user.get("role") != "admin":
        log.warning(
            "Access denied — admin required",
            user=current_user.get("sub"),
            role=current_user.get("role"),
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user
