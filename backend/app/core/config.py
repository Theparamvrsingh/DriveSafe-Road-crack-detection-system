from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    # Paths
    repo_root: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    storage_dir: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "storage"))
    db_path: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "storage", "road_health.sqlite3"))

    # Model
    default_weights: str = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "weights", "best.pt")
    )
    image_size: int = 448
    conf_thresh: float = 0.5


settings = Settings()

