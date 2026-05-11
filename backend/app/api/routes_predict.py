from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query, HTTPException

from app.db.sqlite import get_record, list_records_for_location, insert_prediction, list_predictions
from app.schemas.predict import PredictionResponse
from app.services.prediction import predict_future_severity

router = APIRouter()


@router.get("/predict", response_model=PredictionResponse)
def predict(
    record_id: Optional[int] = Query(default=None, ge=1),
    lat: Optional[float] = Query(default=None),
    lon: Optional[float] = Query(default=None),
    horizon_days: int = Query(default=30, ge=1, le=365),
):
    """
    Early warning prediction using stored historical records.

    Provide either:
    - record_id (uses that record's lat/lon)
    - or explicit lat & lon
    """
    if record_id is not None:
        rec = get_record(int(record_id))
        if not rec or rec.get("lat") is None or rec.get("lon") is None:
            # can't predict without a location history
            raise HTTPException(status_code=400, detail="record_id must exist and include lat/lon to predict")
        lat = float(rec["lat"])
        lon = float(rec["lon"])

    if lat is None or lon is None:
        raise HTTPException(status_code=400, detail="Provide either record_id or both lat and lon")

    history = list_records_for_location(lat=float(lat), lon=float(lon), limit=500)
    pred = predict_future_severity(history=history, horizon_days=int(horizon_days))
    if pred is None:
        raise HTTPException(
            status_code=409,
            detail="Not enough historical data at this location (need at least 3 records)",
        )

    payload = {
        "horizon_days": pred.horizon_days,
        "predicted_severity": pred.predicted_severity,
        "predicted_score": pred.predicted_score,
        "slope_per_day": pred.slope_per_day,
        "risk": pred.risk,
        "alert": pred.alert,
        "rationale": pred.rationale,
    }
    insert_prediction(record_id=record_id, lat=float(lat), lon=float(lon), prediction=payload)
    return PredictionResponse(record_id=record_id, **payload)


@router.get("/predictions")
def predictions(limit: int = Query(default=200, ge=1, le=2000)):
    return {"items": list_predictions(limit=limit)}

