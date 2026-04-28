from __future__ import annotations

import pandas as pd


def aggregate_country_score(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["country", "country_score", "article_count"])

    agg = (
        df.groupby("country", dropna=False)
        .agg(country_score=("signal_score", "mean"), article_count=("url", "count"))
        .reset_index()
        .sort_values("country_score", ascending=False)
    )
    return agg
