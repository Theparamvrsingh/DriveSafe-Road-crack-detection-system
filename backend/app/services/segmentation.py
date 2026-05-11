from __future__ import annotations

import base64
import io
import os
import sys
from dataclasses import dataclass
from typing import Optional

import numpy as np
from PIL import Image

import torch

# Ensure repo root is importable when running from `backend/`.
from app.core.config import settings

if settings.repo_root not in sys.path:
    sys.path.insert(0, settings.repo_root)

# Reuse the canonical model definition from repo root.
from models import UNet  # type: ignore  # noqa: E402


@dataclass
class SegmentationResult:
    mask: np.ndarray  # uint8 {0,1} shape (H,W)
    mask_png_base64: str
    overlay_png_base64: str


def _pil_to_chw_float01(image: Image.Image) -> torch.Tensor:
    arr = np.asarray(image)
    if arr.ndim == 2:
        arr = np.stack([arr, arr, arr], axis=-1)
    arr = arr[..., :3]
    chw = arr.transpose(2, 0, 1).astype(np.float32) / 255.0
    return torch.from_numpy(chw)


def _to_base64_png(pil_img: Image.Image) -> str:
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def _overlay(image: Image.Image, mask01: np.ndarray, alpha: float = 0.5) -> Image.Image:
    img = image.convert("RGB")
    mask = (mask01.astype(np.uint8) * 255)
    mask_rgb = Image.fromarray(mask).convert("RGB")
    # red tint on crack pixels
    r, g, b = mask_rgb.split()
    tint = Image.merge("RGB", (r, Image.new("L", r.size, 0), Image.new("L", r.size, 0)))
    return Image.blend(img, tint, alpha=alpha)


class Segmenter:
    def __init__(self, *, weights_path: str, device: Optional[str] = None, out_channels: int = 2) -> None:
        self.weights_path = weights_path
        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
        self.model = UNet(in_channels=3, out_channels=out_channels).to(self.device)
        self._loaded = False

    def load(self) -> None:
        if self._loaded:
            return
        if not os.path.exists(self.weights_path):
            raise FileNotFoundError(f"Weights not found: {self.weights_path}")
        ckpt = torch.load(self.weights_path, map_location=self.device)
        # Support both formats:
        # - {"model": <nn.Module>} used by this repo's training script
        # - {"model_state_dict": state_dict} common elsewhere
        if isinstance(ckpt, dict) and "model" in ckpt and hasattr(ckpt["model"], "state_dict"):
            self.model.load_state_dict(ckpt["model"].float().state_dict())
        elif isinstance(ckpt, dict) and "model_state_dict" in ckpt:
            self.model.load_state_dict(ckpt["model_state_dict"])
        elif isinstance(ckpt, dict) and "state_dict" in ckpt:
            self.model.load_state_dict(ckpt["state_dict"])
        else:
            # last resort: assume checkpoint itself is a state_dict
            self.model.load_state_dict(ckpt)
        self.model.eval()
        self._loaded = True

    @torch.inference_mode()
    def predict(self, image: Image.Image, *, image_size: int = 448, conf_thresh: float = 0.5) -> SegmentationResult:
        self.load()

        resized = image.convert("RGB").resize((image_size, image_size))
        x = _pil_to_chw_float01(resized).unsqueeze(0).to(self.device)

        out = self.model(x).detach().cpu()
        if self.model.out_channels > 1:
            mask = out.argmax(dim=1)[0].numpy().astype(np.uint8)
            # assume class 1 = crack
            mask01 = (mask == 1).astype(np.uint8)
        else:
            mask01 = (torch.sigmoid(out)[0, 0].numpy() > conf_thresh).astype(np.uint8)

        mask_img = Image.fromarray(mask01 * 255)
        overlay_img = _overlay(resized, mask01)

        return SegmentationResult(
            mask=mask01,
            mask_png_base64=_to_base64_png(mask_img),
            overlay_png_base64=_to_base64_png(overlay_img),
        )

