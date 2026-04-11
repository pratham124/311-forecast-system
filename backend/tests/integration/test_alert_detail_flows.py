from __future__ import annotations

import pytest

from app.repositories.alert_detail_repository import AlertDetailRepository
from app.repositories.forecast_repository import ForecastRepository
from app.repositories.notification_event_repository import NotificationEventRepository
from app.repositories.surge_configuration_repository import SurgeConfigurationRepository
from app.repositories.surge_notification_event_repository import SurgeNotificationEventRepository
from app.repositories.threshold_configuration_repository import ThresholdConfigurationRepository
from tests.contract.test_surge_alert_api import seed_surge_inputs
from tests.evaluation_helpers import seed_daily_evaluation_inputs


pytestmark = pytest.mark.integration


def _seed_threshold_event(app_client, operational_manager_headers, session) -> tuple[str, str]:
    _, forecast_version_id = seed_daily_evaluation_inputs(session, seed_tag="alert-detail-threshold")
    ThresholdConfigurationRepository(session).create_configuration(
        service_category="Roads",
        forecast_window_type="hourly",
        threshold_value=1,
        notification_channels=["dashboard"],
        operational_manager_id="manager-1",
    )
    session.commit()

    evaluation = app_client.post(
        "/api/v1/forecast-alerts/evaluations",
        json={
            "forecastReferenceId": forecast_version_id,
            "forecastProduct": "daily",
            "triggerSource": "manual_replay",
        },
        headers=operational_manager_headers,
    )
    assert evaluation.status_code == 202
    run_id = evaluation.json()["thresholdEvaluationRunId"]

    event = NotificationEventRepository(session).list_events(service_category="Roads")[0]
    return event.notification_event_id, run_id


def _seed_surge_event(app_client, operational_manager_headers, session) -> tuple[str, str, str]:
    seed_surge_inputs(session)
    SurgeConfigurationRepository(session).create_configuration(
        service_category="Roads",
        z_score_threshold=2.0,
        percent_above_forecast_floor=100.0,
        rolling_baseline_window_count=7,
        notification_channels=["dashboard"],
        operational_manager_id="manager-1",
    )
    session.commit()

    forecast_version_id = ForecastRepository(session).get_current_marker("daily_1_day_demand").forecast_version_id
    evaluation = app_client.post(
        "/api/v1/surge-alerts/evaluations",
        json={
            "forecastReferenceId": forecast_version_id,
            "triggerSource": "manual_replay",
        },
        headers=operational_manager_headers,
    )
    assert evaluation.status_code == 202
    run_id = evaluation.json()["surgeEvaluationRunId"]

    event = SurgeNotificationEventRepository(session).list_events(service_category="Roads")[0]
    return event.surge_notification_event_id, run_id, event.surge_candidate_id


def test_threshold_alert_detail_flow_persists_load(app_client, operational_manager_headers, planner_headers, session) -> None:
    event_id, threshold_run_id = _seed_threshold_event(app_client, operational_manager_headers, session)

    response = app_client.get(
        f"/api/v1/alert-details/threshold_alert/{event_id}",
        headers=planner_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["alertSource"] == "threshold_alert"
    assert body["alertId"] == event_id
    assert body["forecastProduct"] == "daily"
    assert body["scope"]["serviceCategory"] == "Roads"
    assert body["distribution"]["status"] == "available"
    assert body["drivers"]["status"] == "unavailable"
    assert body["anomalies"]["status"] == "unavailable"
    assert body["viewStatus"] == "partial"

    session.expire_all()
    record = AlertDetailRepository(session).require_load(body["alertDetailLoadId"])
    assert record.alert_source == "threshold_alert"
    assert record.alert_id == event_id
    assert record.view_status == "partial"
    assert record.distribution_status == "available"
    assert record.drivers_status == "unavailable"
    assert record.anomalies_status == "unavailable"
    assert record.preparation_status == "completed"
    assert record.source_threshold_evaluation_run_id == threshold_run_id
    assert record.source_forecast_version_id == body["forecastReferenceId"]
    assert record.correlation_id == event_id


def test_surge_alert_detail_flow_and_render_failure_persistence(
    app_client,
    operational_manager_headers,
    planner_headers,
    session,
) -> None:
    event_id, surge_run_id, surge_candidate_id = _seed_surge_event(app_client, operational_manager_headers, session)

    response = app_client.get(
        f"/api/v1/alert-details/surge_alert/{event_id}",
        headers=planner_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["alertSource"] == "surge_alert"
    assert body["alertId"] == event_id
    assert body["primaryMetricLabel"] == "Actual demand"
    assert body["secondaryMetricLabel"] == "Forecast P50"
    assert body["distribution"]["status"] == "available"
    assert body["drivers"]["status"] == "unavailable"
    assert body["anomalies"]["status"] == "available"
    assert any(item["isSelectedAlert"] for item in body["anomalies"]["items"])
    assert body["viewStatus"] == "partial"

    record = AlertDetailRepository(session).require_load(body["alertDetailLoadId"])
    assert record.alert_source == "surge_alert"
    assert record.source_surge_evaluation_run_id == surge_run_id
    assert record.source_surge_candidate_id == surge_candidate_id
    assert record.source_forecast_version_id == body["forecastReferenceId"]

    render_failed = app_client.post(
        f"/api/v1/alert-details/{body['alertDetailLoadId']}/render-events",
        json={"renderStatus": "render_failed", "failureReason": "chart boundary failed"},
        headers=operational_manager_headers,
    )
    assert render_failed.status_code == 202
    assert render_failed.json()["recordedOutcomeStatus"] == "render_failed"

    session.expire_all()
    updated = AlertDetailRepository(session).require_load(body["alertDetailLoadId"])
    assert updated.render_status == "render_failed"
    assert updated.render_failure_reason == "chart boundary failed"
    assert updated.view_status == "error"
    assert updated.failure_reason == "chart boundary failed"
