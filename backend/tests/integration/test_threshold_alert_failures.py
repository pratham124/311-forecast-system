from __future__ import annotations

from app.api.routes import forecast_alerts as forecast_alerts_route
from app.clients.notification_service import NotificationAttemptResult
from app.models import ThresholdScopeEvaluation
from app.repositories.notification_event_repository import NotificationEventRepository
from app.repositories.threshold_configuration_repository import ThresholdConfigurationRepository
from tests.evaluation_helpers import seed_daily_evaluation_inputs


def test_missing_threshold_suppressed_duplicate_and_total_failure_outcomes(app_client, operational_manager_headers, session) -> None:
    _, forecast_version_id = seed_daily_evaluation_inputs(session, seed_tag="threshold-failures")

    missing_threshold = app_client.post(
        "/api/v1/forecast-alerts/evaluations",
        json={"forecastReferenceId": forecast_version_id, "forecastProduct": "daily", "triggerSource": "manual_replay"},
        headers=operational_manager_headers,
    )
    assert missing_threshold.status_code == 202
    missing_run_id = missing_threshold.json()["thresholdEvaluationRunId"]
    evaluations = session.query(ThresholdScopeEvaluation).all()
    assert any(item.threshold_evaluation_run_id == missing_run_id and item.outcome == "configuration_missing" for item in evaluations)

    ThresholdConfigurationRepository(session).create_configuration(
        service_category="Roads",
        forecast_window_type="hourly",
        threshold_value=1,
        notification_channels=["email"],
        operational_manager_id="manager-1",
    )
    session.commit()

    first = app_client.post(
        "/api/v1/forecast-alerts/evaluations",
        json={"forecastReferenceId": forecast_version_id, "forecastProduct": "daily", "triggerSource": "forecast_publish"},
        headers=operational_manager_headers,
    )
    second = app_client.post(
        "/api/v1/forecast-alerts/evaluations",
        json={"forecastReferenceId": forecast_version_id, "forecastProduct": "daily", "triggerSource": "forecast_refresh"},
        headers=operational_manager_headers,
    )
    assert first.status_code == 202
    assert second.status_code == 202

    ThresholdConfigurationRepository(session).create_configuration(
        service_category="Waste",
        forecast_window_type="hourly",
        threshold_value=1,
        notification_channels=["email"],
        operational_manager_id="manager-1",
    )
    session.commit()

    original = forecast_alerts_route.NotificationDeliveryClient.deliver
    forecast_alerts_route.NotificationDeliveryClient.deliver = lambda self, *, channel_type, payload: NotificationAttemptResult(  # type: ignore[method-assign]
        channel_type=channel_type,
        status="failed",
        failure_reason="manual review required",
    )
    try:
        failed = app_client.post(
            "/api/v1/forecast-alerts/evaluations",
            json={"forecastReferenceId": forecast_version_id, "forecastProduct": "daily", "triggerSource": "scheduled_recheck"},
            headers=operational_manager_headers,
        )
        assert failed.status_code == 202
    finally:
        forecast_alerts_route.NotificationDeliveryClient.deliver = original  # type: ignore[method-assign]

    repository = NotificationEventRepository(session)
    events = repository.list_events()
    assert events
    assert any(event.overall_delivery_status == "manual_review_required" for event in events)
