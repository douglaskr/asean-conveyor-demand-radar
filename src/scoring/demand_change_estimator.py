from __future__ import annotations

import pandas as pd


def estimate_demand_pressure(country_scores: pd.DataFrame, industry_scores: pd.DataFrame) -> pd.DataFrame:
    """Simple demand pressure proxy from current week score levels."""
    if country_scores.empty or industry_scores.empty:
        return pd.DataFrame(columns=["country", "industry", "demand_pressure"])

    rows = []
    for _, c in country_scores.iterrows():
        for _, i in industry_scores.iterrows():
            pressure = (c["country_score"] * 0.55) + (i["industry_score"] * 0.45)
            rows.append({"country": c["country"], "industry": i["industry"], "demand_pressure": round(float(pressure), 3)})
    return pd.DataFrame(rows).sort_values("demand_pressure", ascending=False)
