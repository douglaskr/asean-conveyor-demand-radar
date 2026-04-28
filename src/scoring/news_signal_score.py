from __future__ import annotations

import pandas as pd


def compute_news_signal_score(df: pd.DataFrame, weights: dict) -> pd.DataFrame:
    if df.empty:
        df["signal_score"] = []
        return df

    out = df.copy()
    max_rel = max(out.get("relevance", pd.Series([1])).max(), 1)
    out["relevance_norm"] = out.get("relevance", 1) / max_rel
    out["sentiment_stub"] = 0.5
    out["risk_intensity_stub"] = out["risk_topic"].apply(lambda x: 1.0 if x != "none" else 0.2)
    out["volume_stub"] = 0.5
    out["recency_stub"] = 0.8

    w = weights["weights"]
    out["signal_score"] = (
        out["relevance_norm"] * w["relevance"]
        + out["sentiment_stub"] * w["sentiment"]
        + out["risk_intensity_stub"] * w["risk_intensity"]
        + out["volume_stub"] * w["volume"]
        + out["recency_stub"] * w["recency"]
    )
    return out
