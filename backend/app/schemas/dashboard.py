"""
AttackGraphX — Pydantic schemas for What-If simulation
"""
from pydantic import BaseModel


class SimulateRequest(BaseModel):
    vulnerability_id: str


class SimulateStats(BaseModel):
    path_count: int
    avg_risk: int
    critical_paths: int


class SimulateResponse(BaseModel):
    before: SimulateStats
    after: SimulateStats
    vulnerability_id: str
    status: str


class ScanStatusResponse(BaseModel):
    status: str
    last_scan: str
