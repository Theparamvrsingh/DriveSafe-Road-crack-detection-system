import os
import shutil
from ultralytics import YOLO

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_YAML = os.path.join(BASE_DIR, 'data', 'detection', 'data.yaml')
WEIGHTS_DIR = os.path.join(BASE_DIR, 'weights')
os.makedirs(WEIGHTS_DIR, exist_ok=True)

def train():
    if not os.path.exists(DATA_YAML):
        print(f"Data yaml not found at {DATA_YAML}. Ensure Phase 1 is completed.")
        return

    # Initialize YOLO model
    model = YOLO("yolov8n.pt")

    # Train the model
    results = model.train(
        data=DATA_YAML,
        epochs=50,
        imgsz=640,
        batch=8,
        project=os.path.join(BASE_DIR, 'runs'),
        name='detect_train'
    )

    # After training, YOLO saves the best weights to runs/detect_train/weights/best.pt
    # We will copy it to weights/best_detection.pt
    best_weights_path = os.path.join(BASE_DIR, 'runs', 'detect_train', 'weights', 'best.pt')
    if os.path.exists(best_weights_path):
        shutil.copy(best_weights_path, os.path.join(WEIGHTS_DIR, 'best_detection.pt'))
        print("Moved best weights to weights/best_detection.pt")
    else:
        print(f"Could not find {best_weights_path}. Training might have failed.")

if __name__ == '__main__':
    train()
