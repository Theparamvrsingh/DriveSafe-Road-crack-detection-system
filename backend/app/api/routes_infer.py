import os
import io
import base64
import torch
import numpy as np
import cv2
import sqlite3
from typing import Optional

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse
from PIL import Image

# Import models from our services
import sys
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from backend.app.services import model_loader

router = APIRouter()

@router.post("/predict-segmentation")
async def predict_seg(file: UploadFile = File(...)):
    # Read image
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    original_size = (img.shape[1], img.shape[0])

    if model_loader.seg_model is None:
        # ⚠️ FALLBACK: If weights are missing, return a simple darkened version as a 'mock' mask
        # This prevents the app from crashing during demos/interviews
        mock_mask = (img * 0.2).astype(np.uint8)
        _, buffer = cv2.imencode('.png', mock_mask)
        mask_b64 = base64.b64encode(buffer).decode('utf-8')
        return {
            "mask_base64": f"data:image/png;base64,{mask_b64}", 
            "crack_percentage": 0.0,
            "warning": "Weights missing - running in simulation mode"
        }
    
    # Preprocess
    img_resized = cv2.resize(img, (256, 256))
    img_tensor = img_resized.astype(np.float32) / 255.0
    img_tensor = np.transpose(img_tensor, (2, 0, 1))
    img_tensor = np.expand_dims(img_tensor, axis=0)
    img_tensor = torch.tensor(img_tensor).to(next(model_loader.seg_model.parameters()).device)
    
    # Predict
    with torch.no_grad():
        output = model_loader.seg_model(img_tensor)
        output = torch.sigmoid(output)
        output_np = output.cpu().numpy()[0, 0]
        
        # Standard threshold
        mask_binary = (output_np > 0.5).astype(np.uint8)
        
        # Smart inversion (temporary fix for old weights)
        crack_density = np.sum(mask_binary) / mask_binary.size
        if crack_density > 0.5:
            mask_binary = 1 - mask_binary
            
    # Postprocess mask to original size
    mask_resized = cv2.resize(mask_binary, original_size, interpolation=cv2.INTER_NEAREST)
    
    # Color the mask using Viridis colormap style
    # Purple background: RGB(68, 1, 84) -> BGR(84, 1, 68)
    # Yellow cracks: RGB(253, 231, 37) -> BGR(37, 231, 253)
    colored_mask = np.zeros((original_size[1], original_size[0], 3), dtype=np.uint8)
    colored_mask[mask_resized == 0] = [84, 1, 68]
    colored_mask[mask_resized == 1] = [37, 231, 253]
    
    # Create opaque mask
    _, buffer = cv2.imencode('.png', colored_mask)
    mask_b64 = base64.b64encode(buffer).decode('utf-8')
    
    # Metrics
    crack_pixels = np.sum(mask_resized)
    crack_percentage = float((crack_pixels / (original_size[0] * original_size[1])) * 100)
    
    return {"mask_base64": f"data:image/png;base64,{mask_b64}", "crack_percentage": crack_percentage}

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
    from backend.app.core.config import settings
    db_path = settings.db_path
    if not os.path.exists(db_path):
        return {"data": []}
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT image, lat, lon, severity FROM map_data")
        rows = cursor.fetchall()
        data = [{"image": r[0], "lat": r[1], "lon": r[2], "severity": r[3]} for r in rows]
    except Exception as e:
        data = []
    finally:
        conn.close()
        
    return {"data": data}
