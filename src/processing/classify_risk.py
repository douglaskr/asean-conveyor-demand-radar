from __future__ import annotations

import pandas as pd


def classify_risk(df: pd.DataFrame, risk_topics: list[dict]) -> pd.DataFrame:
    if df.empty:
        df["risk_topic"] = []
        return df

    def pick_risk(text: str) -> str:
        lower = text.lower()
        for topic in risk_topics:
            if any(k.lower() in lower for k in topic.get("keywords", [])):
                return topic["name"]
        return "none"

    out = df.copy()
    out["risk_topic"] = out["title"].apply(pick_risk)
    return out
