import os
import uuid
import sqlite3
import numpy as np
import cv2
from typing import Optional

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import JSONResponse

import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from app.services import model_loader
from app.services.emailer import trigger_pothole_report, get_email_status
from app.core.config import settings

router = APIRouter()
DB_PATH = settings.db_path
UPLOADS_DIR = os.path.join(BASE_DIR, "backend", "storage", "uploads")


def _quick_severity(img: np.ndarray) -> tuple[str, float]:
    """Fast severity estimate using detection boxes only."""
    img_area = img.shape[0] * img.shape[1]
    det_percent = 0.0

    if model_loader.det_model is not None:
        results = model_loader.det_model.predict(img, imgsz=320, conf=0.25, verbose=False)
        total_damage_area = 0.0
        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                total_damage_area += (x2 - x1) * (y2 - y1)
        det_percent = round((total_damage_area / img_area) * 100, 1) if img_area > 0 else 0.0

    if det_percent > 25:
        severity = "high"
    elif det_percent > 10:
        severity = "medium"
    else:
        severity = "low"

    return severity, det_percent


@router.post("/report-pothole")
async def report_pothole(
    file: UploadFile = File(...),
    lat: Optional[float] = Form(None),
    lon: Optional[float] = Form(None),
):
    if lat is None or lon is None:
        return JSONResponse(
            {"error": "GPS coordinates are required to report a pothole"},
            status_code=400,
        )

    model_loader.ensure_models()
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    file_id = str(uuid.uuid4())[:8]
    ext = file.filename.split(".")[-1] if file.filename and "." in file.filename else "jpg"
    img_filename = f"pothole_{file_id}.{ext}"
    img_path = os.path.join(UPLOADS_DIR, img_filename)

    contents = await file.read()
    with open(img_path, "wb") as f:
        f.write(contents)

    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        return JSONResponse({"error": "Invalid image file"}, status_code=400)

    severity, severity_percent = _quick_severity(img)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id FROM pothole_reports
        WHERE abs(lat - ?) < 0.0005 AND abs(lon - ?) < 0.0005
        AND datetime(timestamp) > datetime('now', '-1 day')
        """,
        (lat, lon),
    )
    if cursor.fetchone():
        conn.close()
        return {
            "status": "duplicate",
            "message": "A pothole was already reported here recently.",
            "email": get_email_status(),
        }

    cursor.execute(
        """
        INSERT INTO pothole_reports (image_path, lat, lon, severity)
        VALUES (?, ?, ?, ?)
        """,
        (img_path, lat, lon, severity),
    )
    conn.commit()
    conn.close()

    trigger_pothole_report(lat, lon, severity, img_path)

    email_status = get_email_status()
    if email_status["configured"]:
        msg = f"Incident reported. Alert email is being sent to {email_status['recipient']}."
    else:
        msg = (
            f"Incident saved. Email is NOT configured on the server — set SMTP_PASSWORD "
            f"to deliver alerts to {email_status['recipient']}."
        )

    return {
        "status": "success",
        "severity": severity,
        "severity_percent": severity_percent,
        "message": msg,
        "email": email_status,
    }


@router.get("/get-potholes")
def get_potholes():
    if not os.path.exists(DB_PATH):
        return {"data": []}

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT image_path, lat, lon, severity, timestamp FROM pothole_reports ORDER BY id DESC"
        )
        rows = cursor.fetchall()
        data = [
            {
                "image": os.path.basename(r[0]) if r[0] else None,
                "lat": r[1],
                "lon": r[2],
                "severity": r[3],
                "timestamp": r[4],
            }
            for r in rows
        ]
    except Exception:
        data = []
    finally:
        conn.close()

    return {"data": data}


@router.delete("/clear-potholes")
def clear_potholes():
    if not os.path.exists(DB_PATH):
        return {"status": "ok"}
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM pothole_reports")
    conn.commit()
    conn.close()
    return {"status": "ok"}
