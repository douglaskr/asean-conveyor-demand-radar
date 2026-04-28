from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path("data/radar_history.db")


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS weekly_scores (
            week_id TEXT,
            country TEXT,
            industry TEXT,
            demand_pressure REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()
