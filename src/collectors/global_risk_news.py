from __future__ import annotations

import logging
from typing import Iterable

import pandas as pd

from src.collectors.news_gdelt import GDELTNewsCollector


class GlobalRiskCollector:
    """Fetch global risk/disaster stories from GDELT using risk-topic queries."""

    def __init__(self, gdelt_collector: GDELTNewsCollector):
        self.gdelt = gdelt_collector
        self.logger = logging.getLogger(__name__)

    def fetch_by_topics(self, topics: Iterable[dict], window_days: int = 7) -> pd.DataFrame:
        frames: list[pd.DataFrame] = []
        for t in topics:
            name = t["name"]
            query = " OR ".join(f'"{k}"' for k in t["keywords"])
            df = self.gdelt.fetch(query=query, max_records=60, timespan_days=window_days)
            if df.empty:
                self.logger.warning("No global risk data collected for topic: %s", name)
                continue

            df["risk_topic"] = name
            frames.append(df)

        if not frames:
            return pd.DataFrame(columns=["title", "url", "domain", "risk_topic"])
        return pd.concat(frames, ignore_index=True)
