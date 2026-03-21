from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from app.services.validation_metrics_service import ValidationMetricsService


@pytest.mark.integration
def test_validation_completion_target_is_fifteen_minutes() -> None:
    started_at = datetime.utcnow()
    completed_at = started_at + timedelta(minutes=14, seconds=59)

    assert ValidationMetricsService().completed_within_target(started_at, completed_at) is True
