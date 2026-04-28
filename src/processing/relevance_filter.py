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

    query_group = out.get("query_group", pd.Series("", index=out.index))
    broad_groups = query_group.isin(["global_risk", "macro_supply_chain", "risk_queries"])
    investigation_groups = query_group.isin(["core_queries", "country_queries", "industry_queries"])
    non_trivial_text = text.astype(str).str.len() >= 25
    mask = (out["relevance"] >= min_relevance_score) | broad_groups | (investigation_groups & non_trivial_text)
    return out[mask].reset_index(drop=True)
