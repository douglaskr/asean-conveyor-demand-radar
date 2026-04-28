from __future__ import annotations

import pandas as pd


def filter_relevant_news(df: pd.DataFrame, keywords: list[str]) -> pd.DataFrame:
    if df.empty:
        return df

    pat = "|".join([k.replace(" ", r"\\s+") for k in keywords])
    mask = df["title"].str.lower().str.contains(pat, regex=True, na=False)
    out = df[mask].copy()
    out["relevance"] = out["title"].str.lower().apply(lambda t: sum(1 for k in keywords if k.lower() in t))
    return out.reset_index(drop=True)
