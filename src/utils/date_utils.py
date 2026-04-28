from __future__ import annotations

from datetime import datetime, timedelta, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def get_week_window(days: int = 7) -> tuple[datetime, datetime]:
    end_dt = utc_now()
    start_dt = end_dt - timedelta(days=days)
    return start_dt, end_dt


def week_id(dt: datetime | None = None) -> str:
    target = dt or utc_now()
    iso_year, iso_week, _ = target.isocalendar()
    return f"{iso_year}-{iso_week:02d}"
