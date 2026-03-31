from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.historical_demand import HistoricalDemandQueryRequest, HistoricalDemandRenderEvent


@pytest.mark.unit
def test_query_request_rejects_naive_time_range_start() -> None:
    with pytest.raises(ValidationError):
        HistoricalDemandQueryRequest(
            time_range_start=datetime(2026, 1, 1),
            time_range_end=datetime(2026, 1, 31, tzinfo=timezone.utc),
        )


@pytest.mark.unit
def test_query_request_rejects_naive_time_range_end() -> None:
    with pytest.raises(ValidationError):
        HistoricalDemandQueryRequest(
            time_range_start=datetime(2026, 1, 1, tzinfo=timezone.utc),
            time_range_end=datetime(2026, 1, 31),
        )


@pytest.mark.unit
def test_query_request_rejects_end_before_start() -> None:
    with pytest.raises(ValidationError):
        HistoricalDemandQueryRequest(
            time_range_start=datetime(2026, 2, 1, tzinfo=timezone.utc),
            time_range_end=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )


@pytest.mark.unit
def test_query_request_rejects_geography_value_without_level() -> None:
    with pytest.raises(ValidationError):
        HistoricalDemandQueryRequest(
            time_range_start=datetime(2026, 1, 1, tzinfo=timezone.utc),
            time_range_end=datetime(2026, 1, 31, tzinfo=timezone.utc),
            geography_value="Ward 1",
        )


@pytest.mark.unit
def test_render_event_requires_failure_reason_when_failed() -> None:
    with pytest.raises(ValidationError):
        HistoricalDemandRenderEvent(render_status="render_failed", failure_reason=None)
