from __future__ import annotations

import pandas as pd


def classify_country(df: pd.DataFrame, countries: list[str]) -> pd.DataFrame:
    if df.empty:
        df["country"] = []
        return df

    def guess_country(text: str) -> str:
        lower = text.lower()
        for c in countries:
            if c.lower() in lower:
                return c
        return "Unknown"

    out = df.copy()
    out["country"] = out["title"].apply(guess_country)
    return out
