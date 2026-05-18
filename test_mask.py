import cv2
import numpy as np

img = np.ones((100, 100, 3), dtype=np.uint8) * 100
mask = np.zeros((100, 100), dtype=np.uint8)
mask[40:60, 40:60] = 1

overlay = img.copy()
crack_color = np.array([0, 80, 255], dtype=np.float32)
overlay_region = overlay[mask == 1].astype(np.float32) * 0.3 + crack_color * 0.7
overlay[mask == 1] = np.clip(overlay_region, 0, 255).astype(np.uint8)

print("Original pixel:", img[50, 50])
print("Overlay pixel:", overlay[50, 50])
