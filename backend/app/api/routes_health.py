from __future__ import annotations

import os
import sys
import torch
import platform
from datetime import datetime, timezone
from fastapi import APIRouter

router = APIRouter()


@router.get("/health", tags=["health"])
def health():
    """
    System health check — returns model status, runtime info, and uptime.
    Used by the dashboard live-status indicator.
    """
    import sys
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    if BASE_DIR not in sys.path:
        sys.path.append(BASE_DIR)

    from app.services import model_loader

    seg_loaded = model_loader.seg_model is not None
    det_loaded = model_loader.det_model is not None

    seg_weights = os.path.join(BASE_DIR, "weights", "best_segmentation.pt")
    det_weights = os.path.join(BASE_DIR, "weights", "best_detection.pt")

    seg_size_mb = round(os.path.getsize(seg_weights) / 1e6, 1) if os.path.exists(seg_weights) else 0
    det_size_mb = round(os.path.getsize(det_weights) / 1e6, 1) if os.path.exists(det_weights) else 0

    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "python": sys.version.split()[0],
        "pytorch": torch.__version__,
        "cuda": torch.cuda.is_available(),
        "platform": platform.system(),
        "models": {
            "segmentation": {
                "loaded": seg_loaded,
                "architecture": "U-Net (custom encoder-decoder)",
                "weight_mb": seg_size_mb,
            },
            "detection": {
                "loaded": det_loaded,
                "architecture": "YOLOv8n",
                "weight_mb": det_size_mb,
            },
        },
        "services": {
            "email_configured": bool(os.getenv("SMTP_PASSWORD")),
            "alert_recipient": os.getenv("ALERT_EMAIL", "paramveercse@gmail.com"),
        },
    }
