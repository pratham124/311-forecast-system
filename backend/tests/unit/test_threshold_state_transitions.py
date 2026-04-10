"""T025 – Unit tests for threshold-state transitions after threshold changes."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.repositories.threshold_configuration_repository import ThresholdConfigurationRepository
from app.repositories.threshold_state_repository import ThresholdStateRepository
from app.services.threshold_alert_service import ThresholdAlertService


_START = datetime(2026, 4, 1, 8, 0, tzinfo=timezone.utc)
_END = _START + timedelta(hours=1)


# ── ThresholdAlertService state machine tests ──────────────────────────────


def test_first_exceedance_transitions_to_above_alerted() -> None:
    decision = ThresholdAlertService().evaluate(
        forecast_value=120, threshold_value=100, current_state=None,
    )
    assert decision.exceeded is True
    assert decision.should_create_alert is True
    assert decision.next_state == "above_threshold_alerted"
    assert decision.outcome == "exceeded_alert_created"


def test_still_above_suppresses_duplicate() -> None:
    decision = ThresholdAlertService().evaluate(
        forecast_value=130, threshold_value=100, current_state="above_threshold_alerted",
    )
    assert decision.exceeded is True
    assert decision.should_create_alert is False
    assert decision.next_state == "above_threshold_alerted"
    assert decision.outcome == "exceeded_suppressed"


def test_return_below_rearms() -> None:
    decision = ThresholdAlertService().evaluate(
        forecast_value=90, threshold_value=100, current_state="above_threshold_alerted",
    )
    assert decision.exceeded is False
    assert decision.should_create_alert is False
    assert decision.next_state == "below_or_equal"
    assert decision.outcome == "below_or_equal"


def test_rearm_then_exceed_creates_new_alert() -> None:
    svc = ThresholdAlertService()
    # Step 1: cross above
    d1 = svc.evaluate(forecast_value=120, threshold_value=100, current_state=None)
    assert d1.should_create_alert is True
    # Step 2: return below
    d2 = svc.evaluate(forecast_value=80, threshold_value=100, current_state=d1.next_state)
    assert d2.should_create_alert is False
    assert d2.next_state == "below_or_equal"
    # Step 3: cross above again
    d3 = svc.evaluate(forecast_value=110, threshold_value=100, current_state=d2.next_state)
    assert d3.should_create_alert is True
    assert d3.outcome == "exceeded_alert_created"


def test_equal_to_threshold_is_not_exceedance() -> None:
    decision = ThresholdAlertService().evaluate(
        forecast_value=100, threshold_value=100, current_state=None,
    )
    assert decision.exceeded is False
    assert decision.should_create_alert is False
    assert decision.next_state == "below_or_equal"


def test_below_threshold_stays_below() -> None:
    decision = ThresholdAlertService().evaluate(
        forecast_value=50, threshold_value=100, current_state="below_or_equal",
    )
    assert decision.exceeded is False
    assert decision.should_create_alert is False
    assert decision.next_state == "below_or_equal"


# ── FR-011b: threshold value changes between evaluations ──────────────────


def test_threshold_change_uses_new_value(session) -> None:
    """After threshold changes, next evaluation uses the new threshold."""
    config_repo = ThresholdConfigurationRepository(session)
    state_repo = ThresholdStateRepository(session)
    svc = ThresholdAlertService()

    # Initial threshold = 100, forecast = 90 → below
    d1 = svc.evaluate(forecast_value=90, threshold_value=100, current_state=None)
    assert d1.should_create_alert is False

    state_repo.upsert_state(
        threshold_configuration_id="cfg-old",
        service_category="Roads",
        geography_type=None,
        geography_value=None,
        forecast_window_type="hourly",
        forecast_window_start=_START,
        forecast_window_end=_END,
        current_state=d1.next_state,
        last_forecast_bucket_value=90,
        last_threshold_value=100,
        last_notification_event_id=None,
    )
    session.flush()

    # Threshold lowered to 80, same forecast = 90 → now exceeds
    d2 = svc.evaluate(forecast_value=90, threshold_value=80, current_state=d1.next_state)
    assert d2.should_create_alert is True
    assert d2.outcome == "exceeded_alert_created"


def test_threshold_raise_suppresses_previously_alerting_value(session) -> None:
    """If threshold raised above current forecast, value returns below → no alert."""
    svc = ThresholdAlertService()
    # Was above old threshold (100), got alerted
    d1 = svc.evaluate(forecast_value=110, threshold_value=100, current_state=None)
    assert d1.should_create_alert is True

    # Threshold raised to 120, forecast 110 is now below → below_or_equal
    d2 = svc.evaluate(forecast_value=110, threshold_value=120, current_state=d1.next_state)
    assert d2.should_create_alert is False
    assert d2.next_state == "below_or_equal"
