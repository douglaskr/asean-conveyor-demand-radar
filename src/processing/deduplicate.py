from __future__ import annotations

import pandas as pd


def deduplicate_articles(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    out["title_key"] = out["title"].str.lower().str.replace(r"\W+", " ", regex=True).str.strip()
    out = out.drop_duplicates(subset=["url"]).drop_duplicates(subset=["title_key"])
    return out.drop(columns=["title_key"], errors="ignore").reset_index(drop=True)
