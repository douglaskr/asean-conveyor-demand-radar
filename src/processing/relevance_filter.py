from __future__ import annotations

import pandas as pd


def filter_relevant_news(df: pd.DataFrame, keywords: list[str]) -> pd.DataFrame:
    if df.empty:
        return df

    pat = "|".join([k.replace(" ", r"\\s+") for k in keywords])
    mask = df["title"].str.lower().str.contains(pat, regex=True, na=False)
    out = df[mask].copy()

    def _matched_keywords(title: str) -> str:
        lower = title.lower()
        hits = [k for k in keywords if k.lower() in lower]
        return ", ".join(hits)

    out["matched_keywords"] = out["title"].astype(str).apply(_matched_keywords)
    out["relevance"] = out["title"].str.lower().apply(lambda t: sum(1 for k in keywords if k.lower() in t))
    return out.reset_index(drop=True)
