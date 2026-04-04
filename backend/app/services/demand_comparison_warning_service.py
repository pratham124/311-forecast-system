from __future__ import annotations

from datetime import datetime

from app.schemas.demand_comparison_api import HighVolumeWarning


class DemandComparisonWarningService:
    def evaluate(
        self,
        *,
        service_category_count: int,
        geography_count: int,
        time_range_start: datetime,
        time_range_end: datetime,
        proceed_after_warning: bool,
    ) -> HighVolumeWarning | None:
        combination_count = service_category_count * max(geography_count, 1)
        span_days = max((time_range_end.date() - time_range_start.date()).days, 0) + 1
        if span_days <= 366 and combination_count <= 10:
            return None
        message = (
            "Retrieval has not started because this request spans a large scope and may take longer to load."
        )
        return HighVolumeWarning(
            shown=True,
            acknowledged=proceed_after_warning,
            message=message,
        )
