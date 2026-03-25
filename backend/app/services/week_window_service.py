from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class WeekWindow:
    week_start_local: datetime
    week_end_local: datetime


class WeekWindowService:
    def __init__(self, timezone_name: str) -> None:
        self.timezone = ZoneInfo(timezone_name)

    def get_week_window(self, now: datetime | None = None) -> WeekWindow:
        current = now or datetime.now(self.timezone)
        if current.tzinfo is None:
            current = current.replace(tzinfo=self.timezone)
        local_now = current.astimezone(self.timezone)
        week_start = (local_now - timedelta(days=local_now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)
        return WeekWindow(week_start_local=week_start, week_end_local=week_end)
