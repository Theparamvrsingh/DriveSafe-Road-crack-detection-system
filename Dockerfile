# ============================================
# DriveSafe Road Crack Detection System — Hugging Face Spaces Docker
# ============================================
FROM python:3.11-slim

# System dependencies for OpenCV + curl for weight downloads
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
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

# Create necessary directories with proper permissions
RUN mkdir -p weights backend/storage/uploads && \
    chown -R appuser:appuser /app

# Download model weights from GitHub Release at build time
# These URLs will work once you upload weights to GitHub Releases
ARG WEIGHTS_URL_SEG="https://github.com/theparamvrsingh/DriveSafe-Road-crack-detection-system/releases/download/v1.0.0/best_segmentation.pt"
ARG WEIGHTS_URL_DET="https://github.com/theparamvrsingh/DriveSafe-Road-crack-detection-system/releases/download/v1.0.0/best_detection.pt"

RUN curl -fSL -o weights/best_segmentation.pt "$WEIGHTS_URL_SEG" 2>/dev/null || \
    echo "⚠ Segmentation weights not available — will use fallback"
RUN curl -fSL -o weights/best_detection.pt "$WEIGHTS_URL_DET" 2>/dev/null || \
    echo "⚠ Detection weights not available — will use fallback"

# Validate downloaded weights (remove if they're HTML error pages)
RUN python -c "\
import os;\
for f in ['weights/best_segmentation.pt', 'weights/best_detection.pt']:\
    if os.path.exists(f) and os.path.getsize(f) < 10000:\
        os.remove(f); print(f'Removed invalid: {f}')\
    elif os.path.exists(f):\
        print(f'Valid: {f} ({os.path.getsize(f)/1e6:.1f} MB)')\
"

RUN chown -R appuser:appuser /app

USER appuser

# HF Spaces expects port 7860
EXPOSE 7860

# Start from backend/ directory (where app.main is importable)
WORKDIR /app/backend

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
