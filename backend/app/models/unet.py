"""
Backend-local import shim.

The canonical model implementation is kept at repo root in `models/unet.py`
to match the required project layout. Backend services import from there.
"""

from models.unet import UNet  # type: ignore[F401]

