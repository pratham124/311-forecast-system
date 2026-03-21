from __future__ import annotations

from datetime import datetime


class ValidationMetricsService:
    completion_target_seconds = 15 * 60

    def completed_within_target(self, started_at: datetime, completed_at: datetime) -> bool:
        return (completed_at - started_at).total_seconds() <= self.completion_target_seconds
