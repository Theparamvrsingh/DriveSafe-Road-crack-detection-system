from __future__ import annotations

from typing import Optional, Literal
from pydantic import BaseModel, Field


SeverityLevel = Literal["Low", "Medium", "High"]
MaintenanceAction = Literal["Crack sealing", "Patching", "Full resurfacing"]


class GPS(BaseModel):
    lat: float
    lon: float


class SeverityMetrics(BaseModel):
    crack_area_px: int = Field(..., ge=0)
    crack_density: float = Field(..., ge=0.0, le=1.0)
    crack_length_px: float = Field(..., ge=0.0)
    crack_width_mean_px: float = Field(..., ge=0.0)
    crack_width_p95_px: float = Field(..., ge=0.0)


class Recommendation(BaseModel):
    severity: SeverityLevel
    action: MaintenanceAction
    rationale: str


class InferResponse(BaseModel):
    record_id: int
    gps: Optional[GPS] = None
    metrics: SeverityMetrics
    recommendation: Recommendation
    # returned as base64 PNGs for easy frontend rendering
    mask_png_base64: str
    overlay_png_base64: str

