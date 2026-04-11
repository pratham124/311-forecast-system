from __future__ import annotations

from app.services.surge_confirmation_service import SurgeConfirmationService
from app.services.surge_detection_service import SurgeMetrics


def _metrics(*, actual: float, forecast: float, z_score: float, percent: float | None) -> SurgeMetrics:
    return SurgeMetrics(
        actual_demand_value=actual,
        forecast_p50_value=forecast,
        residual_value=actual - forecast,
        residual_z_score=z_score,
        percent_above_forecast=percent,
        rolling_baseline_mean=0.0,
        rolling_baseline_stddev=1.0,
    )


def test_confirmation_requires_both_thresholds() -> None:
    service = SurgeConfirmationService()

    confirmed = service.evaluate(
        metrics=_metrics(actual=6, forecast=2, z_score=5.0, percent=200.0),
        z_score_threshold=2.0,
        percent_above_forecast_floor=100.0,
        active_surge=False,
    )
    assert confirmed.outcome == "confirmed"

    filtered = service.evaluate(
        metrics=_metrics(actual=6, forecast=2, z_score=5.0, percent=80.0),
        z_score_threshold=2.0,
        percent_above_forecast_floor=100.0,
        active_surge=False,
    )
    assert filtered.outcome == "filtered"
    assert filtered.z_score_check_passed is True
    assert filtered.percent_floor_check_passed is False


def test_confirmation_suppresses_active_surge_and_handles_zero_forecast() -> None:
    service = SurgeConfirmationService()

    suppressed = service.evaluate(
        metrics=_metrics(actual=3, forecast=0, z_score=3.0, percent=None),
        z_score_threshold=2.0,
        percent_above_forecast_floor=100.0,
        active_surge=True,
    )
    assert suppressed.outcome == "suppressed_active_surge"
    assert suppressed.percent_floor_check_passed is True
