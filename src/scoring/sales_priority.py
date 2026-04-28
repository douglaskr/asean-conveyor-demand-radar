from __future__ import annotations

import pandas as pd


def build_sales_priority(demand_df: pd.DataFrame, product_mapping: dict) -> pd.DataFrame:
    if demand_df.empty:
        return pd.DataFrame(columns=["country", "industry", "demand_pressure", "recommended_products"])

    out = demand_df.head(20).copy()
    out["recommended_products"] = out["industry"].map(lambda ind: ", ".join(product_mapping.get(ind, [])))
    return out
