from __future__ import annotations

import pandas as pd


def clean_news(df: pd.DataFrame) -> pd.DataFrame:
    """Basic standardization for collected news."""
    if df.empty:
        return df
    out = df.copy()
    out["title"] = out["title"].fillna("").astype(str).str.strip()
    out["url"] = out["url"].fillna("").astype(str).str.strip()
    out = out[out["title"] != ""]
    out = out[out["url"] != ""]
    return out.reset_index(drop=True)
