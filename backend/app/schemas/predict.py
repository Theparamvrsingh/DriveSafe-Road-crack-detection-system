from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field

from app.schemas.infer import SeverityLevel


RiskLevel = Literal["Low", "Medium", "High"]


class PredictionResponse(BaseModel):
    record_id: Optional[int] = None
    horizon_days: int = Field(..., ge=1, le=365)
    predicted_severity: SeverityLevel
    predicted_score: float = Field(..., ge=1.0, le=3.0)
    slope_per_day: float
    risk: RiskLevel
    alert: bool
    rationale: str

