from __future__ import annotations

from datetime import datetime


class OperatorVisibilityMetricsService:
    visibility_target_seconds = 2 * 60

    def visible_within_target(self, started_at: datetime, observed_at: datetime) -> bool:
        return (observed_at - started_at).total_seconds() <= self.visibility_target_seconds
