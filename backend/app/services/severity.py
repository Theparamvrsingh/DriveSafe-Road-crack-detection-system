from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import cv2


SeverityLevel = Literal["Low", "Medium", "High"]


@dataclass(frozen=True)
class SeverityMetrics:
    crack_area_px: int
    crack_density: float
    crack_length_px: float
    crack_width_mean_px: float
    crack_width_p95_px: float


def _skeletonize(mask01: np.ndarray) -> np.ndarray:
    """
    Lightweight morphological skeletonization (no skimage dependency).
    Returns uint8 {0,1}.
    """
    img = (mask01.astype(np.uint8) * 255)
    skel = np.zeros_like(img)
    element = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))

    while True:
        eroded = cv2.erode(img, element)
        temp = cv2.dilate(eroded, element)
        temp = cv2.subtract(img, temp)
        skel = cv2.bitwise_or(skel, temp)
        img = eroded
        if cv2.countNonZero(img) == 0:
            break

    return (skel > 0).astype(np.uint8)


def compute_metrics(mask01: np.ndarray) -> SeverityMetrics:
    mask01 = (mask01 > 0).astype(np.uint8)
    h, w = mask01.shape[:2]
    total = float(h * w)

    area_px = int(mask01.sum())
    density = float(area_px / total) if total > 0 else 0.0

    # Crack length proxy: number of skeleton pixels (in px)
    skel01 = _skeletonize(mask01)
    length_px = float(skel01.sum())

    # Crack width proxy: 2 * distance-to-background on skeleton pixels
    dist = cv2.distanceTransform(mask01 * 255, cv2.DIST_L2, 3)
    widths = (dist[skel01.astype(bool)] * 2.0).astype(np.float32)
    if widths.size == 0:
        width_mean = 0.0
        width_p95 = 0.0
    else:
        width_mean = float(widths.mean())
        width_p95 = float(np.percentile(widths, 95))

    return SeverityMetrics(
        crack_area_px=area_px,
        crack_density=density,
        crack_length_px=length_px,
        crack_width_mean_px=width_mean,
        crack_width_p95_px=width_p95,
    )


def classify_severity(m: SeverityMetrics) -> SeverityLevel:
    """
    Rule-based severity (tune thresholds after calibrating with RDD2020/SUT-Crack).
    - High: dense + long or very wide
    - Medium: moderate density/length/width
    - Low: sparse/thin/short
    """
    if m.crack_density >= 0.03 or m.crack_width_p95_px >= 10 or m.crack_length_px >= 8000:
        return "High"
    if m.crack_density >= 0.01 or m.crack_width_p95_px >= 5 or m.crack_length_px >= 3000:
        return "Medium"
    return "Low"

