from __future__ import annotations

import base64
import io
from dataclasses import dataclass

import cv2
import numpy as np
from PIL import Image


@dataclass
class BaselineResult:
    mask01: np.ndarray  # uint8 {0,1}
    mask_png_base64: str
    overlay_png_base64: str


def _to_base64_png(pil_img: Image.Image) -> str:
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def _overlay(image: Image.Image, mask01: np.ndarray, alpha: float = 0.5) -> Image.Image:
    img = np.asarray(image.convert("RGB")).copy()
    m = (mask01.astype(bool))
    tint = img.copy()
    tint[m] = (255, 40, 70)
    out = (img * (1 - alpha) + tint * alpha).astype(np.uint8)
    return Image.fromarray(out)


def baseline_segment(image: Image.Image, image_size: int = 448) -> BaselineResult:
    """
    Ready-to-run fallback when no model weights exist.
    Not as accurate as U-Net, but produces a reasonable crack-like mask for demos.
    """
    pil = image.convert("RGB").resize((image_size, image_size))
    bgr = cv2.cvtColor(np.asarray(pil), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

    # Enhance thin dark structures
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    blackhat = cv2.morphologyEx(blur, cv2.MORPH_BLACKHAT, cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9)))
    blackhat = cv2.normalize(blackhat, None, 0, 255, cv2.NORM_MINMAX)

    # Edge + threshold
    edges = cv2.Canny(blackhat, 40, 120)
    _, th = cv2.threshold(blackhat, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    mask = cv2.bitwise_or(edges, th)

    # Clean up
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)), iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)), iterations=1)

    mask01 = (mask > 0).astype(np.uint8)
    mask_img = Image.fromarray(mask01 * 255)
    overlay_img = _overlay(pil, mask01)

    return BaselineResult(
        mask01=mask01,
        mask_png_base64=_to_base64_png(mask_img),
        overlay_png_base64=_to_base64_png(overlay_img),
    )

