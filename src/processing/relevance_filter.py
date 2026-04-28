from __future__ import annotations

import pandas as pd


def filter_relevant_news(df: pd.DataFrame, keywords: list[str], min_relevance_score: int = 1) -> pd.DataFrame:
    if df.empty:
        return df

    out = df.copy()
    text = (out["title"].fillna("") + " " + out.get("snippet", pd.Series("", index=out.index)).fillna(""))

    def _hits(raw_text: str) -> list[str]:
        lower = raw_text.lower()
        return [k for k in keywords if k.lower() in lower]

    out["matched_keywords"] = text.astype(str).apply(lambda t: ", ".join(_hits(t)))
    out["relevance"] = text.astype(str).apply(lambda t: len(_hits(t)))

    broad_groups = out.get("query_group", pd.Series("", index=out.index)).isin(["global_risk", "macro_supply_chain"])
    mask = (out["relevance"] >= min_relevance_score) | broad_groups
    return out[mask].reset_index(drop=True)
