from __future__ import annotations

import logging
import random
import time
from datetime import datetime
from typing import Any

import pandas as pd
import requests


class GDELTNewsCollector:
    """Collect news from the GDELT DOC API with rate-limit-safe behavior."""

    BASE_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
    MIN_INTERVAL_SECONDS = 5

    # Class-level timestamp so separate collector instances still respect spacing.
    _last_request_at: float = 0.0

    def __init__(self, timeout: int = 30, max_retries: int = 2):
        self.timeout = timeout
        self.max_retries = max(1, min(max_retries, 2))
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def _empty_frame() -> pd.DataFrame:
        return pd.DataFrame(columns=["title", "url", "domain", "seendate", "sourcecountry", "language"])

    def _wait_for_rate_limit(self) -> None:
        elapsed = time.monotonic() - self.__class__._last_request_at
        remaining = self.MIN_INTERVAL_SECONDS - elapsed
        if remaining > 0:
            self.logger.info("GDELT rate-limit guard: sleeping %.1f seconds before next request.", remaining)
            time.sleep(remaining)

    def _request(self, params: dict[str, Any]) -> requests.Response | None:
        for attempt in range(1, self.max_retries + 1):
            self._wait_for_rate_limit()
            try:
                response = requests.get(self.BASE_URL, params=params, timeout=self.timeout)
                self.__class__._last_request_at = time.monotonic()
            except requests.RequestException as exc:
                self.logger.warning("GDELT request error on attempt %d/%d: %s", attempt, self.max_retries, exc)
                if attempt >= self.max_retries:
                    return None
                backoff = random.uniform(6, 10)
                self.logger.info("Retrying GDELT after request error: sleeping %.1f seconds.", backoff)
                time.sleep(backoff)
                continue

            if response.status_code == 429:
                self.logger.warning("GDELT returned HTTP 429 on attempt %d/%d.", attempt, self.max_retries)
                if attempt >= self.max_retries:
                    return None
                backoff = random.uniform(6, 10)
                self.logger.info("Rate limit encountered. Waiting %.1f seconds before retry.", backoff)
                time.sleep(backoff)
                continue

            if response.status_code >= 400:
                self.logger.warning(
                    "GDELT returned HTTP %d on attempt %d/%d.",
                    response.status_code,
                    attempt,
                    self.max_retries,
                )
                if attempt >= self.max_retries:
                    return None
                backoff = random.uniform(6, 10)
                self.logger.info("Retrying after HTTP error: sleeping %.1f seconds.", backoff)
                time.sleep(backoff)
                continue

            return response

        return None

    def fetch(
        self,
        query: str,
        max_records: int = 80,
        mode: str = "ArtList",
        timespan_days: int | None = 7,
    ) -> pd.DataFrame:
        """
        Fetch articles with conservative request volume.

        - Enforces at least 5 seconds between API requests
        - Retries (max 1-2 attempts total) on 429/HTTP errors
        - Falls back to empty DataFrame on persistent failure
        """
        safe_max_records = max(10, min(max_records, 100))
        params: dict[str, Any] = {
            "query": query,
            "mode": mode,
            "maxrecords": safe_max_records,
            "format": "json",
        }
        if timespan_days:
            params["timespan"] = f"{timespan_days}d"

        response = self._request(params)
        if response is None:
            self.logger.warning("GDELT fetch failed after retries. Returning empty result.")
            return self._empty_frame()

        try:
            payload = response.json()
        except ValueError:
            self.logger.warning("GDELT returned non-JSON response. Returning empty result.")
            return self._empty_frame()

        articles = payload.get("articles", [])
        if not articles:
            return self._empty_frame()

        rows: list[dict[str, Any]] = []
        for a in articles:
            rows.append(
                {
                    "title": a.get("title", ""),
                    "url": a.get("url", ""),
                    "domain": a.get("domain", ""),
                    "seendate": a.get("seendate", ""),
                    "sourcecountry": a.get("sourcecountry", ""),
                    "language": a.get("language", ""),
                }
            )

        df = pd.DataFrame(rows)
        df["collected_at"] = datetime.utcnow().isoformat()
        return df
