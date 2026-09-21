"""
AttackGraphX — Auth routes: POST /auth/login
"""
import bcrypt
import structlog
from fastapi import APIRouter, HTTPException, status

from app.auth.jwt import create_access_token
from app.schemas.auth import LoginRequest, TokenResponse

log = structlog.get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])

# ---------------------------------------------------------------------------
# Password hashing — uses bcrypt directly to avoid passlib/bcrypt 5.x compat issues
# ---------------------------------------------------------------------------

def _hash(password: str) -> bytes:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())


def _verify(plain: str, hashed: bytes) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed if isinstance(hashed, bytes) else hashed.encode("utf-8"))
    except Exception:
        return False


# ---------------------------------------------------------------------------
# In-memory user store — passwords are bcrypt hashed, NEVER plaintext.
# In production, replace with a real database lookup.
# ---------------------------------------------------------------------------
_USERS: dict[str, dict] = {
    "admin": {
        "username": "admin",
        "hashed_password": _hash("admin123"),
        "role": "admin",
    },
    "analyst": {
        "username": "analyst",
        "hashed_password": _hash("analyst123"),
        "role": "analyst",
    },
}


def _authenticate(username: str, password: str) -> dict | None:
    user = _USERS.get(username)
    if not user:
        return None
    if not _verify(password, user["hashed_password"]):
        return None
    return user


# ---------------------------------------------------------------------------
# Login endpoint
# ---------------------------------------------------------------------------
@router.post("/login", response_model=TokenResponse, summary="Authenticate and receive JWT")
async def login(body: LoginRequest):
    """
    Accepts username/password credentials.
    Returns a signed JWT access token in the format expected by the frontend.
    """
    user = _authenticate(body.username, body.password)
    if not user:
        log.warning("Login failed — invalid credentials", username=body.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(
        data={"sub": user["username"], "role": user["role"]}
    )

    log.info("Login successful", username=user["username"], role=user["role"])
    return TokenResponse(access_token=token, token_type="bearer")
