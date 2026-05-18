# ============================================
# DriveSafe Road Crack Detection System — Hugging Face Spaces Docker
# ============================================
FROM python:3.11-slim

# System dependencies for OpenCV + curl for weight downloads
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user (HF Spaces requirement)
RUN useradd -m -u 1000 appuser

WORKDIR /app

# ---- Install Python dependencies (cached layer) ----

# Install CPU-only PyTorch FIRST (saves ~1.5GB vs CUDA version)
RUN pip install --no-cache-dir \
    torch torchvision \
    --index-url https://download.pytorch.org/whl/cpu

# Copy and install root requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy and install backend requirements
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Install ultralytics (YOLOv8)
RUN pip install --no-cache-dir ultralytics

# ---- Copy application code ----
COPY . .

# Pre-download YOLO weights so live inference works without cold-start download
RUN python -c "from ultralytics import YOLO; YOLO('yolov8n-seg.pt'); YOLO('yolov8n.pt')"

# Create necessary directories with proper permissions
RUN mkdir -p weights backend/storage/uploads backend/storage/outputs && \
    chown -R appuser:appuser /app

# Weights are copied from the repository by the 'COPY . .' command


RUN chown -R appuser:appuser /app

USER appuser

# Render/Web Services expect port 8000
EXPOSE 8000

# Start from backend/ directory (where app.main is importable)
WORKDIR /app/backend

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
