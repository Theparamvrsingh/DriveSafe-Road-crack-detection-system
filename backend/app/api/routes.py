from __future__ import annotations

from fastapi import APIRouter

from app.api.routes_health import router as health_router
from app.api.routes_infer import router as infer_router
from app.api.routes_predict import router as predict_router
from app.api.routes_records import router as records_router
from app.api.routes_pothole import router as pothole_router

router = APIRouter()
router.include_router(health_router, tags=["health"])
router.include_router(infer_router, tags=["inference"])
router.include_router(predict_router, tags=["prediction"])
router.include_router(records_router, tags=["records"])
router.include_router(pothole_router, tags=["pothole"])

