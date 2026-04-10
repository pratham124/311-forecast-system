from __future__ import annotations

from app.repositories.threshold_configuration_repository import ThresholdConfigurationRepository
from tests.evaluation_helpers import seed_daily_evaluation_inputs


def test_threshold_alert_evaluation_and_review_contracts(app_client, operational_manager_headers, planner_headers, session) -> None:
    _, forecast_version_id = seed_daily_evaluation_inputs(session, seed_tag="threshold-contract")
    ThresholdConfigurationRepository(session).create_configuration(
        service_category="Roads",
        forecast_window_type="hourly",
        threshold_value=1,
        notification_channels=["email", "dashboard"],
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
    payload = evaluation.json()
    assert payload["status"] == "accepted"
    assert payload["thresholdEvaluationRunId"]
    assert payload["acceptedAt"]

    listing = app_client.get("/api/v1/forecast-alerts/events", headers=planner_headers)
    assert listing.status_code == 200
    items = listing.json()["items"]
    assert items
    first = items[0]
    assert first["notificationEventId"]
    assert first["serviceCategory"] == "Waste" or first["serviceCategory"] == "Roads"
    assert first["forecastWindowType"] == "hourly"
    assert first["overallDeliveryStatus"] in {"delivered", "partial_delivery", "manual_review_required"}

    detail = app_client.get(f"/api/v1/forecast-alerts/events/{first['notificationEventId']}", headers=planner_headers)
    assert detail.status_code == 200
    body = detail.json()
    assert body["channelAttempts"]
    assert body["thresholdEvaluationRunId"] == payload["thresholdEvaluationRunId"]


def test_threshold_alert_api_requires_auth(app_client, viewer_headers) -> None:
    assert app_client.get("/api/v1/forecast-alerts/events").status_code == 401
    assert app_client.get("/api/v1/forecast-alerts/events", headers=viewer_headers).status_code == 403


def test_threshold_configuration_create_and_list_contract(app_client, operational_manager_headers, planner_headers) -> None:
    create = app_client.post(
        "/api/v1/forecast-alerts/thresholds",
        json={
            "serviceCategory": "Roads",
            "forecastWindowType": "hourly",
            "thresholdValue": 15,
            "notificationChannels": ["email", "dashboard"],
        },
        headers=operational_manager_headers,
    )
    assert create.status_code == 201
    created = create.json()
    assert created["serviceCategory"] == "Roads"
    assert created["forecastWindowType"] == "hourly"
    assert created["thresholdValue"] == 15
    assert created["notificationChannels"] == ["email", "dashboard"]

    listing = app_client.get("/api/v1/forecast-alerts/thresholds", headers=planner_headers)
    assert listing.status_code == 200
    assert any(item["thresholdConfigurationId"] == created["thresholdConfigurationId"] for item in listing.json()["items"])

    update = app_client.patch(
        f"/api/v1/forecast-alerts/thresholds/{created['thresholdConfigurationId']}",
        json={
            "serviceCategory": "Waste",
            "forecastWindowType": "daily",
            "thresholdValue": 22,
            "notificationChannels": ["dashboard"],
        },
        headers=operational_manager_headers,
    )
    assert update.status_code == 200
    updated = update.json()
    assert updated["serviceCategory"] == "Waste"
    assert updated["forecastWindowType"] == "daily"
    assert updated["thresholdValue"] == 22
    assert updated["notificationChannels"] == ["dashboard"]

    delete = app_client.delete(
        f"/api/v1/forecast-alerts/thresholds/{created['thresholdConfigurationId']}",
        headers=operational_manager_headers,
    )
    assert delete.status_code == 204

    listing_after_delete = app_client.get("/api/v1/forecast-alerts/thresholds", headers=planner_headers)
    assert listing_after_delete.status_code == 200
    deleted = next(item for item in listing_after_delete.json()["items"] if item["thresholdConfigurationId"] == created["thresholdConfigurationId"])
    assert deleted["status"] == "inactive"


def test_threshold_service_categories_contract(app_client, planner_headers, session) -> None:
    seed_daily_evaluation_inputs(session, extra_forecast_categories=["Transit"], seed_tag="threshold-categories")

    response = app_client.get("/api/v1/forecast-alerts/service-categories", headers=planner_headers)
    assert response.status_code == 200
    assert response.json()["items"] == ["Roads", "Transit", "Waste"]
