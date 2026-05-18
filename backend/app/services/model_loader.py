import os
import shutil
import threading
from ultralytics import YOLO

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
WEIGHTS_DIR = os.path.join(BASE_DIR, "weights")

seg_model = None
det_model = None
_load_lock = threading.Lock()
_loaded = False


def _resolve_weight(*candidates: str) -> str | None:
    for name in candidates:
        path = os.path.join(WEIGHTS_DIR, name)
        if os.path.exists(path) and os.path.getsize(path) > 10_000:
            return path
    return None


def load_models() -> None:
    global seg_model, det_model, _loaded
    with _load_lock:
        if _loaded:
            return
        try:
            from app.services.weight_downloader import download_weights
            download_weights()
        except Exception as exc:
            print(f"Weight download skipped: {exc}")

        seg_weights = _resolve_weight("best_segmentation_yolo.pt", "best_segmentation.pt")
        if seg_weights:
            try:
                shutil.copy2(seg_weights, os.path.join(WEIGHTS_DIR, "best_segmentation_yolo.pt"))
            except OSError:
                pass

        det_weights = _resolve_weight("best_detection.pt")

        try:
            if seg_weights:
                seg_model = YOLO(seg_weights)
                print(f"Loaded segmentation: {seg_weights}")
            else:
                seg_model = YOLO("yolov8n-seg.pt")
                print("Loaded segmentation fallback: yolov8n-seg.pt")
        except Exception as exc:
            print(f"Segmentation model failed: {exc}")
            seg_model = None

        try:
            if det_weights:
                det_model = YOLO(det_weights)
                print(f"Loaded detection: {det_weights}")
            else:
                det_model = YOLO("yolov8n.pt")
                print("Loaded detection fallback: yolov8n.pt")
        except Exception as exc:
            print(f"Detection model failed: {exc}")
            det_model = None

        _loaded = True


def ensure_models() -> None:
    if not _loaded:
        load_models()
