"""
AttackGraphX — JWT creation and verification utilities
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

import structlog
from jose import JWTError, jwt
from fastapi import HTTPException, status

from app.config import get_settings

log = structlog.get_logger(__name__)
settings = get_settings()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.jwt_expiration_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def verify_token(token: str) -> dict:
    """
    Verify and decode a JWT token.
    Raises HTTPException 401 if the token is invalid or expired.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        sub: str = payload.get("sub")
        if sub is None:
            log.warning("JWT missing 'sub' claim")
            raise credentials_exception
        return payload
    except JWTError as exc:
        log.warning("JWT verification failed", error=str(exc))
        raise credentials_exception
