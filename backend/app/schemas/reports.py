"""
AttackGraphX — Pydantic schemas for reports
"""
from pydantic import BaseModel
from typing import Optional


class ReportRequest(BaseModel):
    target: Optional[str] = "all"
