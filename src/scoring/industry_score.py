from __future__ import annotations

import pandas as pd


def aggregate_industry_score(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["industry", "industry_score", "article_count"])

    agg = (
        df.groupby("industry", dropna=False)
        .agg(industry_score=("signal_score", "mean"), article_count=("url", "count"))
        .reset_index()
        .sort_values("industry_score", ascending=False)
    )
    return agg
