import os
import torch
from ultralytics import YOLO
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.append(BASE_DIR)

from models.unet import UNet

# Auto-download weights if missing (for cloud deployment)
from app.services.weight_downloader import download_weights

seg_model = None
det_model = None

def load_models():
    global seg_model, det_model

    # Ensure weights are available (downloads from GitHub Releases if missing)
    download_weights()
    
    seg_weights = os.path.join(BASE_DIR, "weights", "best_segmentation_yolo.pt")
    det_weights = os.path.join(BASE_DIR, "weights", "best_detection.pt")
    
    # Load Segmentation Model (YOLOv8-Seg from HuggingFace)
    if os.path.exists(seg_weights):
        seg_model = YOLO(seg_weights)
        print(f"Loaded Pretrained YOLO Segmentation Model from {seg_weights}")
    else:
        print(f"Warning: Segmentation weights not found at {seg_weights}")
        seg_model = None
        
    # Load Detection Model (YOLOv8)
    if os.path.exists(det_weights):
        det_model = YOLO(det_weights)
        print(f"Loaded Detection Model from {det_weights}")
    else:
        print(f"Warning: Detection weights not found at {det_weights}. Downloading default yolov8n.pt for testing.")
        det_model = YOLO("yolov8n.pt") # fallback for testing

load_models()
