from __future__ import annotations

import logging
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any
from urllib.parse import quote_plus

import pandas as pd
import requests


class RSSNewsCollector:
    """Collect public signals from Google News RSS search feeds."""

    GOOGLE_RSS_TEMPLATE = "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"

    def __init__(self, timeout: int = 25, min_interval_seconds: float = 2.0):
        self.timeout = timeout
        self.min_interval_seconds = min_interval_seconds
        self.logger = logging.getLogger(__name__)
        self._last_request_at = 0.0

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        remain = self.min_interval_seconds - elapsed
        if remain > 0:
            time.sleep(remain)

    def _fetch_feed(self, query_text: str) -> str:
        url = self.GOOGLE_RSS_TEMPLATE.format(query=quote_plus(query_text))
        self._throttle()
        resp = requests.get(url, timeout=self.timeout)
        self._last_request_at = time.monotonic()
        resp.raise_for_status()
        return resp.text

    def _parse_feed(self, xml_text: str) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        root = ET.fromstring(xml_text)
        for item in root.findall("./channel/item"):
            title = (item.findtext("title") or "").strip()
            url = (item.findtext("link") or "").strip()
            published = (item.findtext("pubDate") or "").strip()
            description = (item.findtext("description") or "").strip()
            source = (item.findtext("source") or "").strip()
            rows.append(
                {
                    "title": title,
                    "url": url,
                    "domain": source,
                    "seendate": published,
                    "snippet": description,
                    "sourcecountry": "",
                    "language": "en",
                    "collected_at": datetime.utcnow().isoformat(),
                }
            )
        return rows

    def fetch_query_pack(self, query_pack: list[dict[str, str]]) -> pd.DataFrame:
        frames: list[pd.DataFrame] = []
        for q in query_pack:
            query_text = q["query_text"]
            query_name = q["query_name"]
            try:
                xml_text = self._fetch_feed(query_text)
                rows = self._parse_feed(xml_text)
                df = pd.DataFrame(rows)
                if df.empty:
                    self.logger.warning("RSS query returned no rows: %s", query_name)
                    continue
                df["source_type"] = "rss"
                df["query_group"] = q["query_group"]
                df["query_name"] = query_name
                df["query_text"] = query_text
                frames.append(df)
            except Exception as exc:
                self.logger.warning("RSS query failed (%s): %s", query_name, exc)
                continue

        if not frames:
            return pd.DataFrame(columns=["title", "url", "domain", "seendate", "snippet", "query_name"])
        return pd.concat(frames, ignore_index=True)
