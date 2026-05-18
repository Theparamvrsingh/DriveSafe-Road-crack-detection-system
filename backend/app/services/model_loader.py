import os
import shutil
from ultralytics import YOLO

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
WEIGHTS_DIR = os.path.join(BASE_DIR, "weights")

from app.services.weight_downloader import download_weights

seg_model = None
det_model = None


def _resolve_weight(*candidates: str) -> str | None:
    for name in candidates:
        path = os.path.join(WEIGHTS_DIR, name)
        if os.path.exists(path) and os.path.getsize(path) > 10_000:
            return path
    return None


def load_models():
    global seg_model, det_model

    download_weights()

    # weight_downloader saves best_segmentation.pt; legacy name best_segmentation_yolo.pt
    seg_weights = _resolve_weight("best_segmentation_yolo.pt", "best_segmentation.pt")
    if seg_weights and not os.path.exists(os.path.join(WEIGHTS_DIR, "best_segmentation_yolo.pt")):
        try:
            shutil.copy2(
                seg_weights,
                os.path.join(WEIGHTS_DIR, "best_segmentation_yolo.pt"),
            )
        except OSError:
            pass

    det_weights = _resolve_weight("best_detection.pt")

    if seg_weights:
        seg_model = YOLO(seg_weights)
        print(f"Loaded YOLO segmentation model from {seg_weights}")
    else:
        print("Warning: Custom seg weights missing — loading yolov8n-seg.pt pretrained fallback")
        seg_model = YOLO("yolov8n-seg.pt")

    if det_weights:
        det_model = YOLO(det_weights)
        print(f"Loaded YOLO detection model from {det_weights}")
    else:
        print("Warning: No detection weights found; using yolov8n.pt fallback")
        det_model = YOLO("yolov8n.pt")


load_models()
