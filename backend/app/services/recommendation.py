from __future__ import annotations

from typing import Literal

from app.services.severity import SeverityLevel, SeverityMetrics


MaintenanceAction = Literal["Crack sealing", "Patching", "Full resurfacing"]


def recommend_action(severity: SeverityLevel, m: SeverityMetrics) -> dict:
    """
    Simple decision logic (swap for an ML classifier later).
    """
    if severity == "Low":
        return {
            "severity": "Low",
            "action": "Crack sealing",
            "rationale": "Cracks are sparse/thin. Seal to prevent water ingress and growth.",
        }

    if severity == "Medium":
        # If width is growing, prefer patching
        if m.crack_width_p95_px >= 8:
            rationale = "Moderate cracking with wider sections. Local patching reduces propagation."
        else:
            rationale = "Moderate cracking. Patching is cost-effective before structural damage increases."
        return {"severity": "Medium", "action": "Patching", "rationale": rationale}

    return {
        "severity": "High",
        "action": "Full resurfacing",
        "rationale": "Cracking is extensive/wide/dense. Resurfacing is recommended to restore structural integrity.",
    }

