from __future__ import annotations

import pandas as pd


def classify_industry(df: pd.DataFrame, industries: dict) -> pd.DataFrame:
    if df.empty:
        df["industry"] = []
        return df

    def pick_industry(text: str) -> str:
        lower = text.lower()
        for industry, cfg in industries.items():
            if any(k.lower() in lower for k in cfg.get("keywords", [])):
                return industry
        return "other"

    out = df.copy()
    out["industry"] = out["title"].apply(pick_industry)
    return out
