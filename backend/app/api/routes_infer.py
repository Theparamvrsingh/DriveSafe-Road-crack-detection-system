import os
import io
import base64
import numpy as np
import cv2
from typing import Optional

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse
from PIL import Image

import sys
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from backend.app.services import model_loader
from app.services.severity import compute_metrics, classify_severity
from app.services.recommendation import recommend_action
from app.db.sqlite import insert_record

router = APIRouter()


def _cv2_fallback_mask(img_bgr: np.ndarray) -> tuple[np.ndarray, float]:
    """
    CV2-based crack detection fallback when YOLO returns no masks.
    Uses adaptive thresholding + morphological ops to find dark crack regions.
    Returns (mask_binary uint8, crack_percentage float).
    """
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    # Enhance contrast
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    # Adaptive threshold to find dark crack regions
    thresh = cv2.adaptiveThreshold(
        enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 8
    )
    # Clean up noise
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    cleaned = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
    # Only keep significant crack-like regions (remove tiny noise)
    kernel2 = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 5))
    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel2, iterations=1)

    mask_binary = (cleaned > 0).astype(np.uint8)
    h, w = img_bgr.shape[:2]
    crack_percentage = float(mask_binary.sum() / (h * w) * 100)
    return mask_binary, crack_percentage


def _build_overlay(img_bgr: np.ndarray, mask_binary: np.ndarray) -> str:
    """
    Create a vivid overlay: original image + bright red/orange crack highlights.
    Returns base64 PNG string (data URI).
    """
    original_size = (img_bgr.shape[1], img_bgr.shape[0])
    mask_resized = cv2.resize(mask_binary, original_size, interpolation=cv2.INTER_NEAREST)

    # Build RGBA overlay
    overlay = img_bgr.copy()
    # Bright orange-red highlight on crack pixels
    crack_color = np.array([0, 80, 255], dtype=np.float32)  # BGR: bright red-orange
    
    # Use float32 for blending to avoid uint8 overflow/darkening
    region = overlay[mask_resized == 1].astype(np.float32)
    blended = region * 0.3 + crack_color * 0.7
    overlay[mask_resized == 1] = np.clip(blended, 0, 255).astype(np.uint8)

    # Add a bright contour around crack regions for extra visibility
    contours, _ = cv2.findContours(mask_resized.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(overlay, contours, -1, (0, 200, 255), 2)  # cyan contour

    _, buffer = cv2.imencode('.png', overlay)
    b64 = base64.b64encode(buffer).decode('utf-8')
    return f"data:image/png;base64,{b64}"


@router.post("/predict-segmentation")
async def predict_seg(file: UploadFile = File(...)):
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    original_size = (img.shape[1], img.shape[0])

    mask_binary = np.zeros((img.shape[0], img.shape[1]), dtype=np.uint8)
    source = "yolo"

    if model_loader.seg_model is None:
        # No model loaded — use CV2 fallback
        mask_binary, _ = _cv2_fallback_mask(img)
        source = "cv2_fallback"
    else:
        # YOLOv8 Segmentation Predict
        try:
            results = model_loader.seg_model(img)
            result = results[0]

            if result.masks is not None:
                masks = result.masks.data.cpu().numpy()
                for m in masks:
                    mask_resized = cv2.resize(m, original_size, interpolation=cv2.INTER_NEAREST)
                    mask_binary = np.logical_or(mask_binary, mask_resized > 0.5).astype(np.uint8)
            
            # If YOLO detected nothing, fall back to CV2
            if mask_binary.sum() == 0:
                mask_binary, _ = _cv2_fallback_mask(img)
                source = "cv2_fallback"
        except Exception as e:
            mask_binary, _ = _cv2_fallback_mask(img)
            source = "cv2_fallback"

    # Build bright visible overlay
    overlay_b64 = _build_overlay(img, mask_binary)

    # Metrics
    h, w = img.shape[:2]
    crack_pixels = int(mask_binary.sum())
    crack_percentage = float((crack_pixels / (h * w)) * 100)

    # Severity & recommendation using the full metrics pipeline
    try:
        sev_metrics = compute_metrics(mask_binary)
        severity = classify_severity(sev_metrics)
        recommendation = recommend_action(severity, sev_metrics)
        metrics_dict = {
            "crack_area_px": int(sev_metrics.crack_area_px),
            "crack_density": float(sev_metrics.crack_density),
            "crack_length_px": float(sev_metrics.crack_length_px),
            "crack_width_mean_px": float(sev_metrics.crack_width_mean_px),
            "crack_width_p95_px": float(sev_metrics.crack_width_p95_px),
        }
        # Save to DB for history/maintenance tracking
        try:
            insert_record(
                lat=None, lon=None,
                metrics=metrics_dict,
                recommendation={"severity": severity, "action": recommendation["action"], "rationale": recommendation["rationale"]},
                image_path=None, mask_path=None, overlay_path=None,
            )
        except Exception:
            pass  # Don't break if DB save fails
    except Exception:
        severity = "Low" if crack_percentage < 5 else ("Medium" if crack_percentage < 20 else "High")
        recommendation = {"action": "Inspect manually", "rationale": "Automated metrics unavailable."}
        metrics_dict = {}

    return {
        "mask_base64": overlay_b64,
        "crack_percentage": round(crack_percentage, 2),
        "severity": severity,
        "action": recommendation.get("action", "N/A"),
        "rationale": recommendation.get("rationale", ""),
        "metrics": metrics_dict,
        "source": source,
    }


@router.post("/detect-rdd")
async def detect(file: UploadFile = File(...)):
    if model_loader.det_model is None:
        return {"detections": [], "warning": "Detection model not loaded"}

    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    results = model_loader.det_model(img)

    detections = []
    for r in results:
        boxes = r.boxes
        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            conf = float(box.conf[0])
            cls = int(box.cls[0])
            name = model_loader.det_model.names[cls]
            detections.append({
                "class": name,
                "confidence": conf,
                "bbox": [x1, y1, x2, y2]
            })

    return {"detections": detections}


@router.get("/get-map-data")
def map_data():
    from app.db.sqlite import list_records
    records = list_records(limit=200)
    data = [
        {"image": r.get("image_path"), "lat": r.get("lat"), "lon": r.get("lon"), "severity": r.get("severity")}
        for r in records if r.get("lat") is not None
    ]
    return {"data": data}
