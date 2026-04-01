from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.schemas.historical_demand import HighVolumeWarningRead


@dataclass
class HistoricalWarningService:
    record_threshold: int = 500
    long_range_days: int = 366

    def evaluate(
        self,
        *,
        candidate_record_count: int,
        time_range_start: datetime,
        time_range_end: datetime,
        service_category: str | None,
        geography_level: str | None,
        proceed_after_warning: bool,
    ) -> HighVolumeWarningRead | None:
        span_days = max((time_range_end - time_range_start).days, 0)
        large_unscoped_request = span_days >= self.long_range_days and not service_category and not geography_level
        high_volume = candidate_record_count >= self.record_threshold or large_unscoped_request
        if not high_volume:
            return None
        return HighVolumeWarningRead(
            shown=True,
            acknowledged=proceed_after_warning,
            message="This request spans a large historical scope and may take longer to load.",
        )
