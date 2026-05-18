import os
import io
import uuid
import base64
import numpy as np
import cv2
from typing import Optional

from fastapi import APIRouter, File, Form, UploadFile

import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from app.services import model_loader
from app.services.severity import compute_metrics, classify_severity
from app.services.recommendation import recommend_action
from app.db.sqlite import insert_record

router = APIRouter()

UPLOADS_DIR = os.path.join(BASE_DIR, "backend", "storage", "uploads")
OUTPUTS_DIR = os.path.join(BASE_DIR, "backend", "storage", "outputs")


def _encode_png_bgr(img_bgr: np.ndarray) -> str:
    _, buffer = cv2.imencode(".png", img_bgr)
    b64 = base64.b64encode(buffer).decode("utf-8")
    return f"data:image/png;base64,{b64}"


def _build_mask_visual(mask_binary: np.ndarray) -> str:
    """Pure segmentation mask: black background, bright cyan crack pixels."""
    h, w = mask_binary.shape[:2]
    vis = np.zeros((h, w, 3), dtype=np.uint8)
    vis[mask_binary == 1] = (255, 220, 0)  # BGR cyan
    return _encode_png_bgr(vis)


def _build_overlay_bgr(img_bgr: np.ndarray, mask_binary: np.ndarray) -> np.ndarray:
    """Original image with highlighted crack regions."""
    mask_resized = cv2.resize(
        mask_binary.astype(np.uint8),
        (img_bgr.shape[1], img_bgr.shape[0]),
        interpolation=cv2.INTER_NEAREST,
    )
    overlay = img_bgr.copy()
    crack_color = np.array([0, 80, 255], dtype=np.float32)
    region = overlay[mask_resized == 1].astype(np.float32)
    if region.size > 0:
        blended = region * 0.35 + crack_color * 0.65
        overlay[mask_resized == 1] = np.clip(blended, 0, 255).astype(np.uint8)
    contours, _ = cv2.findContours(
        mask_resized.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    cv2.drawContours(overlay, contours, -1, (0, 200, 255), 2)
    return overlay


def _run_yolo_segmentation(img: np.ndarray) -> tuple[np.ndarray, str]:
    """Returns (mask_binary, source). No fake edge-detection fallback."""
    h, w = img.shape[:2]
    mask_binary = np.zeros((h, w), dtype=np.uint8)

    if model_loader.seg_model is None:
        return mask_binary, "no_model"

    try:
        results = model_loader.seg_model.predict(img, imgsz=640, verbose=False)
        result = results[0]
        if result.masks is not None:
            masks = result.masks.data.cpu().numpy()
            for m in masks:
                mask_resized = cv2.resize(m, (w, h), interpolation=cv2.INTER_NEAREST)
                mask_binary = np.logical_or(mask_binary, mask_resized > 0.5).astype(np.uint8)
        return mask_binary, "yolo" if mask_binary.sum() > 0 else "yolo_empty"
    except Exception as exc:
        print(f"Segmentation error: {exc}")
        return mask_binary, "error"


@router.post("/predict-segmentation")
async def predict_seg(
    file: UploadFile = File(...),
    lat: Optional[float] = Form(None),
    lon: Optional[float] = Form(None),
):
    model_loader.ensure_models()
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        return {"error": "Invalid image file"}

    mask_binary, source = _run_yolo_segmentation(img)
    h, w = img.shape[:2]
    crack_pixels = int(mask_binary.sum())
    crack_percentage = float((crack_pixels / (h * w)) * 100) if h * w > 0 else 0.0

    mask_b64 = _build_mask_visual(mask_binary)
    overlay_bgr = _build_overlay_bgr(img, mask_binary)
    overlay_b64 = _encode_png_bgr(overlay_bgr)

    severity = "Low"
    recommendation = {"action": "No action required", "rationale": "No cracks detected."}
    metrics_dict: dict = {}

    if crack_pixels > 0:
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
        except Exception:
            severity = (
                "Low"
                if crack_percentage < 5
                else ("Medium" if crack_percentage < 20 else "High")
            )
            recommendation = {
                "action": "Inspect manually",
                "rationale": "Automated metrics unavailable.",
            }

    # Persist inspection for Maintenance tab
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    file_id = str(uuid.uuid4())[:8]
    img_path = os.path.join(UPLOADS_DIR, f"scan_{file_id}.jpg")
    mask_path = os.path.join(OUTPUTS_DIR, f"mask_{file_id}.png")
    overlay_path = os.path.join(OUTPUTS_DIR, f"overlay_{file_id}.png")

    mask_vis = np.zeros((h, w, 3), dtype=np.uint8)
    mask_vis[mask_binary == 1] = (255, 220, 0)
    cv2.imwrite(img_path, img)
    cv2.imwrite(mask_path, mask_vis)
    cv2.imwrite(overlay_path, overlay_bgr)

    record_id = None
    if metrics_dict:
        try:
            record_id = insert_record(
                lat=lat,
                lon=lon,
                metrics=metrics_dict,
                recommendation={
                    "severity": severity,
                    "action": recommendation["action"],
                    "rationale": recommendation["rationale"],
                },
                image_path=img_path,
                mask_path=mask_path,
                overlay_path=overlay_path,
            )
        except Exception as exc:
            print(f"DB insert failed: {exc}")
    elif crack_pixels == 0:
        try:
            record_id = insert_record(
                lat=lat,
                lon=lon,
                metrics={
                    "crack_area_px": 0,
                    "crack_density": 0.0,
                    "crack_length_px": 0.0,
                    "crack_width_mean_px": 0.0,
                    "crack_width_p95_px": 0.0,
                },
                recommendation={
                    "severity": "Low",
                    "action": "No action required",
                    "rationale": "No cracks detected in this scan.",
                },
                image_path=img_path,
                mask_path=mask_path,
                overlay_path=overlay_path,
            )
        except Exception:
            pass

    model_ready = model_loader.seg_model is not None
    warning = None
    if not model_ready:
        warning = "AI model weights not loaded. Upload weights to the weights/ folder or set GITHUB_WEIGHTS_REPO."
    elif source == "yolo_empty":
        warning = "Model ran successfully but found no crack regions in this image."

    return {
        "mask_base64": mask_b64,
        "overlay_base64": overlay_b64,
        "crack_percentage": round(crack_percentage, 2),
        "severity": severity,
        "action": recommendation.get("action", "N/A"),
        "rationale": recommendation.get("rationale", ""),
        "metrics": metrics_dict,
        "source": source,
        "model_loaded": model_ready,
        "warning": warning,
        "record_id": record_id,
    }


@router.post("/detect-rdd")
async def detect(file: UploadFile = File(...)):
    model_loader.ensure_models()
    if model_loader.det_model is None:
        return {"detections": [], "warning": "Detection model not loaded"}

    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        return {"detections": [], "warning": "Invalid image"}

    results = model_loader.det_model.predict(img, imgsz=640, verbose=False)

    detections = []
    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            conf = float(box.conf[0])
            cls = int(box.cls[0])
            name = model_loader.det_model.names[cls]
            detections.append(
                {"class": name, "confidence": conf, "bbox": [x1, y1, x2, y2]}
            )

    return {"detections": detections}


@router.get("/get-map-data")
def map_data():
    from app.db.sqlite import list_records

    records = list_records(limit=200)
    data = [
        {
            "image": r.get("image_path"),
            "lat": r.get("lat"),
            "lon": r.get("lon"),
            "severity": r.get("severity"),
        }
        for r in records
        if r.get("lat") is not None
    ]
    return {"data": data}
