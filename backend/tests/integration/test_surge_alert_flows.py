from __future__ import annotations

from app.repositories.surge_configuration_repository import SurgeConfigurationRepository
from app.repositories.surge_evaluation_repository import SurgeEvaluationRepository
from app.repositories.surge_notification_event_repository import SurgeNotificationEventRepository
from app.repositories.forecast_repository import ForecastRepository
from app.services.surge_alert_trigger_service import run_surge_alert_evaluation_for_forecast
from tests.contract.test_surge_alert_api import seed_surge_inputs


def _run_auto_surge(session) -> str:
    forecast_version_id = ForecastRepository(session).get_current_marker("daily_1_day_demand").forecast_version_id
    run = run_surge_alert_evaluation_for_forecast(session, forecast_version_id=forecast_version_id)
    session.commit()
    return run.surge_evaluation_run_id


def test_confirmed_surge_creates_one_notification_and_suppresses_duplicate(session) -> None:
    SurgeConfigurationRepository(session).create_configuration(
        service_category="Roads",
        z_score_threshold=2.0,
        percent_above_forecast_floor=100.0,
        rolling_baseline_window_count=7,
        notification_channels=["email"],
        operational_manager_id="manager-1",
    )
    session.commit()
    seed_surge_inputs(session, current_count=6)
    first_evaluation_run_id = _run_auto_surge(session)
    seed_surge_inputs(session, current_count=7)

    second_evaluation_run_id = run_surge_alert_evaluation_for_forecast(
        session,
        forecast_version_id=ForecastRepository(session).get_current_marker("daily_1_day_demand").forecast_version_id,
    ).surge_evaluation_run_id
    session.commit()

    events = SurgeNotificationEventRepository(session).list_events(service_category="Roads")
    assert len(events) == 1

    assert second_evaluation_run_id != first_evaluation_run_id
    second_detail = SurgeEvaluationRepository(session).get_run_detail(second_evaluation_run_id)
    assert second_detail is not None
    assert second_detail.candidates[0].confirmation is not None
    assert second_detail.candidates[0].confirmation.outcome == "suppressed_active_surge"


def test_filtered_candidate_creates_no_notification(session) -> None:
    seed_surge_inputs(session, current_count=6)
    SurgeConfigurationRepository(session).create_configuration(
        service_category="Roads",
        z_score_threshold=2.0,
        percent_above_forecast_floor=300.0,
        rolling_baseline_window_count=7,
        notification_channels=["email"],
        operational_manager_id="manager-1",
    )
    session.commit()

    run_id = _run_auto_surge(session)

    events = SurgeNotificationEventRepository(session).list_events(service_category="Roads")
    assert events == []

    detail = SurgeEvaluationRepository(session).get_run_detail(run_id)
    assert detail is not None
    assert detail.candidates[0].confirmation is not None
    assert detail.candidates[0].confirmation.outcome == "filtered"


def test_detector_failure_is_reviewable(session) -> None:
    seed_surge_inputs(session, history_count=0, current_count=6)
    SurgeConfigurationRepository(session).create_configuration(
        service_category="Roads",
        z_score_threshold=2.0,
        percent_above_forecast_floor=100.0,
        rolling_baseline_window_count=7,
        notification_channels=["email"],
        operational_manager_id="manager-1",
    )
    session.commit()

    run_id = _run_auto_surge(session)

    detail = SurgeEvaluationRepository(session).get_run_detail(run_id)
    assert detail is not None
    assert detail.run.status == "completed_with_failures"
    assert detail.candidates[0].candidate.candidate_status == "detector_failed"
    assert detail.candidates[0].confirmation is not None
    assert detail.candidates[0].confirmation.outcome == "failed"
