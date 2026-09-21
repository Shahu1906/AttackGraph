"""
AttackGraphX — Pydantic schemas for Authentication
"""
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=128)
    password: str = Field(..., min_length=1, max_length=256)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    sub: str
    role: str = "analyst"
