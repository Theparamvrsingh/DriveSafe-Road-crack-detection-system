from __future__ import annotations

import os
import sqlite3
from typing import Optional, Any

from app.core.config import settings


def _connect() -> sqlite3.Connection:
    os.makedirs(settings.storage_dir, exist_ok=True)
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS crack_records (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              created_at TEXT NOT NULL DEFAULT (datetime('now')),
              lat REAL NULL,
              lon REAL NULL,

              crack_area_px INTEGER NOT NULL,
              crack_density REAL NOT NULL,
              crack_length_px REAL NOT NULL,
              crack_width_mean_px REAL NOT NULL,
              crack_width_p95_px REAL NOT NULL,

              severity TEXT NOT NULL,
              action TEXT NOT NULL,
              rationale TEXT NOT NULL,

              image_path TEXT NULL,
              mask_path TEXT NULL,
              overlay_path TEXT NULL
            );

            CREATE TABLE IF NOT EXISTS crack_predictions (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              created_at TEXT NOT NULL DEFAULT (datetime('now')),
              record_id INTEGER NULL,
              lat REAL NULL,
              lon REAL NULL,

              horizon_days INTEGER NOT NULL,
              predicted_severity TEXT NOT NULL,
              predicted_score REAL NOT NULL,
              slope_per_day REAL NOT NULL,
              risk TEXT NOT NULL,
              alert INTEGER NOT NULL,
              rationale TEXT NOT NULL,

              FOREIGN KEY(record_id) REFERENCES crack_records(id)
            );
            
            CREATE TABLE IF NOT EXISTS pothole_reports (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              image_path TEXT,
              lat REAL,
              lon REAL,
              severity TEXT,
              timestamp TEXT DEFAULT (datetime('now')),
              reported INTEGER DEFAULT 0
            );
            """
        )


def _count_records(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT COUNT(1) AS n FROM crack_records").fetchone()
    return int(row["n"]) if row else 0


def seed_demo_history_if_empty() -> None:
    """
    Ensure prediction works on first run.

    The prediction endpoint requires at least 3 historical records at the same GPS
    location. When the DB is empty, we insert a tiny synthetic history at a fixed
    point (Delhi by default) with timestamps spread across prior days.
    """
    with _connect() as conn:
        # A minimal, deterministic location users can immediately test.
        lat = 28.6139
        lon = 77.2090
        lat_r = round(float(lat), 5)
        lon_r = round(float(lon), 5)

        # Ensure at least 3 records exist for this location so `/api/predict`
        # works right away, even if the user already generated 1–2 records.
        row = conn.execute(
            """
            SELECT COUNT(1) AS n
            FROM crack_records
            WHERE lat IS NOT NULL AND lon IS NOT NULL
              AND round(lat, 5) = ? AND round(lon, 5) = ?
            """,
            (lat_r, lon_r),
        ).fetchone()
        n_loc = int(row["n"]) if row else 0
        if n_loc >= 3:
            return

        samples = [
            # created_at, severity, action, rationale, metrics
            ("datetime('now','-60 days')", "Low", "Crack sealing", "Seed history (low).", 1200, 0.006, 1200.0, 2.0, 3.5),
            ("datetime('now','-30 days')", "Medium", "Patching", "Seed history (medium).", 4200, 0.015, 3600.0, 3.5, 7.5),
            ("datetime('now','-7 days')", "High", "Full resurfacing", "Seed history (high).", 12000, 0.045, 9200.0, 6.0, 12.5),
        ]

        # Insert only as many as needed to reach 3.
        for created_at_sql, sev, action, rationale, area_px, density, length_px, w_mean, w_p95 in samples[: max(0, 3 - n_loc)]:
            conn.execute(
                f"""
                INSERT INTO crack_records (
                  created_at, lat, lon,
                  crack_area_px, crack_density, crack_length_px, crack_width_mean_px, crack_width_p95_px,
                  severity, action, rationale,
                  image_path, mask_path, overlay_path
                ) VALUES ({created_at_sql}, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL)
                """,
                (
                    float(lat),
                    float(lon),
                    int(area_px),
                    float(density),
                    float(length_px),
                    float(w_mean),
                    float(w_p95),
                    str(sev),
                    str(action),
                    str(rationale),
                ),
            )

        # Seed pothole history if empty
        row_pot = conn.execute("SELECT COUNT(1) AS n FROM pothole_reports").fetchone()
        n_pots = int(row_pot["n"]) if row_pot else 0
        if n_pots == 0:
            pot_samples = [
                ("high", 28.6145, 77.2095),
                ("medium", 28.6130, 77.2080),
                ("low", 28.6150, 77.2100),
                ("medium", 28.6120, 77.2070),
                ("high", 28.6160, 77.2110),
            ]
            for sev, plat, plon in pot_samples:
                conn.execute(
                    """
                    INSERT INTO pothole_reports (image_path, lat, lon, severity)
                    VALUES (?, ?, ?, ?)
                    """,
                    ("dummy_pothole.jpg", plat, plon, sev)
                )


def insert_record(
    *,
    lat: Optional[float],
    lon: Optional[float],
    metrics: dict[str, Any],
    recommendation: dict[str, Any],
    image_path: Optional[str],
    mask_path: Optional[str],
    overlay_path: Optional[str],
) -> int:
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO crack_records (
              lat, lon,
              crack_area_px, crack_density, crack_length_px, crack_width_mean_px, crack_width_p95_px,
              severity, action, rationale,
              image_path, mask_path, overlay_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                lat,
                lon,
                int(metrics["crack_area_px"]),
                float(metrics["crack_density"]),
                float(metrics["crack_length_px"]),
                float(metrics["crack_width_mean_px"]),
                float(metrics["crack_width_p95_px"]),
                str(recommendation["severity"]),
                str(recommendation["action"]),
                str(recommendation["rationale"]),
                image_path,
                mask_path,
                overlay_path,
            ),
        )
        return int(cur.lastrowid)


def list_records(limit: int = 200) -> list[dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM crack_records ORDER BY id DESC LIMIT ?",
            (int(limit),),
        ).fetchall()
        return [dict(r) for r in rows]


def get_record(record_id: int) -> Optional[dict[str, Any]]:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM crack_records WHERE id = ?", (int(record_id),)).fetchone()
        return dict(row) if row else None


def list_records_for_location(*, lat: float, lon: float, limit: int = 500) -> list[dict[str, Any]]:
    """
    Location lookup is intentionally tolerant: uses rounded coordinates so mobile GPS noise
    still groups into the same road point.
    """
    lat_r = round(float(lat), 5)
    lon_r = round(float(lon), 5)
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM crack_records
            WHERE lat IS NOT NULL AND lon IS NOT NULL
              AND round(lat, 5) = ? AND round(lon, 5) = ?
            ORDER BY datetime(created_at) ASC
            LIMIT ?
            """,
            (lat_r, lon_r, int(limit)),
        ).fetchall()
        return [dict(r) for r in rows]


def insert_prediction(
    *,
    record_id: Optional[int],
    lat: Optional[float],
    lon: Optional[float],
    prediction: dict[str, Any],
) -> int:
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO crack_predictions (
              record_id, lat, lon,
              horizon_days, predicted_severity, predicted_score, slope_per_day, risk, alert, rationale
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record_id,
                lat,
                lon,
                int(prediction["horizon_days"]),
                str(prediction["predicted_severity"]),
                float(prediction["predicted_score"]),
                float(prediction["slope_per_day"]),
                str(prediction["risk"]),
                1 if bool(prediction["alert"]) else 0,
                str(prediction["rationale"]),
            ),
        )
        return int(cur.lastrowid)


def list_predictions(limit: int = 200) -> list[dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM crack_predictions ORDER BY id DESC LIMIT ?",
            (int(limit),),
        ).fetchall()
        return [dict(r) for r in rows]

