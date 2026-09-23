"""
AttackGraphX — Pydantic schemas for attack paths and patches
"""
from typing import Optional
from pydantic import BaseModel


class HopModel(BaseModel):
    host: str
    ip: Optional[str] = None
    vulnerability: Optional[str] = None
    attack_technique: Optional[str] = None
    description: Optional[str] = None


class PathModel(BaseModel):
    id: str
    target: str
    risk_score: int
    severity: str
    detectability: Optional[str] = None
    hops: list[HopModel] = []


class PatchModel(BaseModel):
    id: str
    vulnerability_id: str
    host: str
    description: Optional[str] = None
    paths_closed: int = 0
    risk_reduction: int = 0


class PathsResponse(BaseModel):
    data: list[PathModel]
    status: str  # "live" | "stale_cache" | "unavailable"


class PatchesResponse(BaseModel):
    data: list[PatchModel]
    status: str
