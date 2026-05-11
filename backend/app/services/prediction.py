from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Literal

import numpy as np

from app.services.severity import SeverityLevel


@dataclass(frozen=True)
class PredictionResult:
    horizon_days: int
    predicted_severity: SeverityLevel
    predicted_score: float  # numeric severity score
    slope_per_day: float
    risk: Literal["Low", "Medium", "High"]
    alert: bool
    rationale: str


_SEV_TO_SCORE: dict[str, float] = {"Low": 1.0, "Medium": 2.0, "High": 3.0}
_SCORE_TO_SEV = [(1.5, "Low"), (2.5, "Medium"), (float("inf"), "High")]


def _parse_dt(s: str) -> Optional[datetime]:
    # stored as sqlite datetime('now') => "YYYY-MM-DD HH:MM:SS"
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None


def predict_future_severity(
    *,
    history: list[dict],
    horizon_days: int = 30,
) -> Optional[PredictionResult]:
    """
    Simple early-warning predictor.

    Input `history` should be crack_records ordered old->new (or any order; we sort).
    Uses a tiny linear regression on numeric severity score over time.
    """
    if horizon_days <= 0:
        raise ValueError("horizon_days must be > 0")

    rows = []
    for r in history:
        dt = _parse_dt(str(r.get("created_at", "")))
        sev = r.get("severity")
        if dt is None or sev not in _SEV_TO_SCORE:
            continue
        rows.append((dt, float(_SEV_TO_SCORE[str(sev)])))

    if len(rows) < 3:
        return None

    rows.sort(key=lambda x: x[0])
    t0 = rows[0][0]
    xs = np.array([(dt - t0).total_seconds() / 86400.0 for dt, _ in rows], dtype=np.float32)  # days
    ys = np.array([y for _, y in rows], dtype=np.float32)

    # linear fit y = a*x + b
    a, b = np.polyfit(xs, ys, deg=1)
    future_x = float(xs[-1] + horizon_days)
    pred = float(a * future_x + b)
    pred = float(np.clip(pred, 1.0, 3.0))

    if pred <= _SCORE_TO_SEV[0][0]:
        sev_pred: SeverityLevel = "Low"
    elif pred <= _SCORE_TO_SEV[1][0]:
        sev_pred = "Medium"
    else:
        sev_pred = "High"

    # risk + alert logic (simple, interpretable)
    slope = float(a)
    if sev_pred == "High" or slope >= 0.02:
        risk: Literal["Low", "Medium", "High"] = "High"
    elif sev_pred == "Medium" or slope >= 0.01:
        risk = "Medium"
    else:
        risk = "Low"

    alert = risk == "High"
    rationale = (
        f"Predicted severity in ~{horizon_days} days is {sev_pred} (score={pred:.2f}) "
        f"based on a linear trend of historical severity (slope={slope:.3f} severity/day)."
    )

    return PredictionResult(
        horizon_days=int(horizon_days),
        predicted_severity=sev_pred,
        predicted_score=float(pred),
        slope_per_day=float(slope),
        risk=risk,
        alert=bool(alert),
        rationale=rationale,
    )

