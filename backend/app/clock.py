from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

Clock = Callable[[], datetime]


def system_clock() -> datetime:
    return datetime.now(UTC)


def to_iso(dt: datetime) -> str:
    """UTC ISO string with fixed width so lexical order == time order."""
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def is_valid_timezone(name: str) -> bool:
    if not name or len(name) > 64:
        return False
    try:
        ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError):
        return False
    return True


def local_today(now_utc: datetime, timezone: str) -> date:
    return now_utc.astimezone(ZoneInfo(timezone)).date()
