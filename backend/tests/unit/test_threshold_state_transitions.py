from __future__ import annotations

from datetime import datetime, timezone

from app.repositories.threshold_state_repository import ThresholdStateRepository


def test_threshold_state_reconciles_threshold_changes(session) -> None:
    repository = ThresholdStateRepository(session)
    start = datetime(2026, 3, 20, tzinfo=timezone.utc)
    end = datetime(2026, 3, 20, 1, tzinfo=timezone.utc)

    original = repository.reconcile_state(
        threshold_configuration_id="config-a",
        service_category="Roads",
        geography_type=None,
        geography_value=None,
        forecast_window_type="hourly",
        forecast_window_start=start,
        forecast_window_end=end,
        current_state="above_threshold_alerted",
        last_forecast_bucket_value=9,
        last_threshold_value=8,
        last_evaluated_at=start,
        last_notification_event_id="event-a",
    )
    updated = repository.reconcile_state(
        threshold_configuration_id="config-b",
        service_category="Roads",
        geography_type=None,
        geography_value=None,
        forecast_window_type="hourly",
        forecast_window_start=start,
        forecast_window_end=end,
        current_state="below_or_equal",
        last_forecast_bucket_value=9,
        last_threshold_value=10,
        last_evaluated_at=end,
        last_notification_event_id=None,
    )

    assert original.threshold_state_id == updated.threshold_state_id
    assert updated.threshold_configuration_id == "config-b"
    assert float(updated.last_threshold_value) == 10.0
    assert updated.current_state == "below_or_equal"
