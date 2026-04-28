from __future__ import annotations

import pandas as pd

from src.storage.database import get_connection


def save_weekly_scores(week_id: str, demand_df: pd.DataFrame) -> None:
    if demand_df.empty:
        return
    out = demand_df[["country", "industry", "demand_pressure"]].copy()
    out.insert(0, "week_id", week_id)
    conn = get_connection()
    out.to_sql("weekly_scores", conn, if_exists="append", index=False)
    conn.close()


def load_previous_week(week_id: str) -> pd.DataFrame:
    conn = get_connection()
    q = "SELECT * FROM weekly_scores WHERE week_id <> ? ORDER BY created_at DESC"
    df = pd.read_sql_query(q, conn, params=[week_id])
    conn.close()
    return df
