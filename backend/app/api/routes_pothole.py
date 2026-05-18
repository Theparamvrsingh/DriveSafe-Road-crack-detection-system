import os
import uuid
import sqlite3
import numpy as np
import cv2
from typing import Optional

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import JSONResponse

import sys
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from backend.app.services import model_loader
from backend.app.services.emailer import trigger_pothole_report
from backend.app.core.config import settings

router = APIRouter()
DB_PATH = settings.db_path
UPLOADS_DIR = os.path.join(BASE_DIR, "backend", "storage", "uploads")

@router.post("/report-pothole")
async def report_pothole(
    file: UploadFile = File(...),
    lat: Optional[float] = Form(None),
    lon: Optional[float] = Form(None)
):
    if not lat or not lon:
        return JSONResponse({"error": "GPS coordinates are required to report a pothole"}, status_code=400)
    
    # Save the file
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    file_id = str(uuid.uuid4())[:8]
    ext = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
    img_filename = f"pothole_{file_id}.{ext}"
    img_path = os.path.join(UPLOADS_DIR, img_filename)
    
    contents = await file.read()
    with open(img_path, "wb") as f:
        f.write(contents)
        
    # Analyze image using BOTH AI models for robust severity scoring
    import torch
    severity = "medium"
    severity_percent = 0.0
    
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    img_area = img.shape[0] * img.shape[1]
    
    det_percent = 0.0
    seg_percent = 0.0
    
    # Method 1: YOLO Detection — bounding box area ratio
    if model_loader.det_model:
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = model_loader.det_model(img_rgb)
        total_damage_area = 0
        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                total_damage_area += (x2 - x1) * (y2 - y1)
        det_percent = round((total_damage_area / img_area) * 100, 1) if img_area > 0 else 0.0
    
    # Method 2: Segmentation — crack pixel density
    if model_loader.seg_model:
        try:
            results = model_loader.seg_model(img)
            result = results[0]
            if result.masks is not None:
                masks = result.masks.data.cpu().numpy()
                mask_binary = np.zeros((img.shape[0], img.shape[1]), dtype=np.uint8)
                for m in masks:
                    mask_resized = cv2.resize(m, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_NEAREST)
                    mask_binary = np.logical_or(mask_binary, mask_resized > 0.5).astype(np.uint8)
                crack_density = np.sum(mask_binary) / mask_binary.size
                seg_percent = round(crack_density * 100, 1)
        except Exception as e:
            print(f"Pothole segmentation failed: {e}")
            seg_percent = 0.0
    
    # Use whichever model gave a higher damage reading
    severity_percent = round(max(det_percent, seg_percent), 1)
    
    if severity_percent > 25:
        severity = "high"
    elif severity_percent > 15:
        severity = "medium"
    elif severity_percent < 10:
        severity = "low"
            
    # Check for duplicates (within roughly 50 meters, approx 0.0005 degrees)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id FROM pothole_reports 
        WHERE abs(lat - ?) < 0.0005 AND abs(lon - ?) < 0.0005
        AND datetime(timestamp) > datetime('now', '-1 day')
    """, (lat, lon))
    duplicate = cursor.fetchone()
    
    if duplicate:
        conn.close()
        return {"status": "duplicate", "message": "A pothole was already reported here recently."}
        
    # Insert to DB
    cursor.execute("""
        INSERT INTO pothole_reports (image_path, lat, lon, severity)
        VALUES (?, ?, ?, ?)
    """, (img_path, lat, lon, severity))
    conn.commit()
    conn.close()
    
    # Trigger automated email
    trigger_pothole_report(lat, lon, severity, img_path)
    
    return {"status": "success", "severity": severity, "severity_percent": severity_percent, "message": "Pothole reported to municipal authority successfully."}



@router.get("/get-potholes")
def get_potholes():
    if not os.path.exists(DB_PATH):
        return {"data": []}
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT image_path, lat, lon, severity, timestamp FROM pothole_reports")
        rows = cursor.fetchall()
        data = [{
            "image": os.path.basename(r[0]) if r[0] else None, 
            "lat": r[1], 
            "lon": r[2], 
            "severity": r[3],
            "timestamp": r[4]
        } for r in rows]
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
