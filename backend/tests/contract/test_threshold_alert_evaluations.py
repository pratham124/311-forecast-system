from __future__ import annotations


def test_trigger_threshold_evaluation_endpoint_accepts_request(app_client, operational_manager_headers) -> None:
    response = app_client.post(
        "/api/v1/forecast-alerts/evaluations",
        headers=operational_manager_headers,
        json={
            "forecastReferenceId": "forecast-version-1",
            "forecastProduct": "daily",
            "triggerSource": "manual_replay",
        },
    )

    assert response.status_code == 202
    payload = response.json()
    assert payload["status"] == "accepted"
    assert isinstance(payload["thresholdEvaluationRunId"], str)


def test_operational_manager_can_update_threshold_configuration(app_client, operational_manager_headers) -> None:
    response = app_client.put(
        "/api/v1/forecast-alerts/threshold-configurations",
        headers=operational_manager_headers,
        json={
            "thresholdValue": 33.5,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["serviceCategory"] == "ALL"
    assert payload["forecastWindowType"] == "global"
    assert payload["thresholdValue"] == 33.5


def test_reader_can_list_daily_threshold_configurations(app_client, planner_headers, operational_manager_headers) -> None:
    app_client.put(
        "/api/v1/forecast-alerts/threshold-configurations",
        headers=operational_manager_headers,
        json={
            "thresholdValue": 22.0,
        },
    )
    response = app_client.get(
        "/api/v1/forecast-alerts/threshold-configurations?forecastWindowType=daily",
        headers=planner_headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["items"]
    assert payload["items"][0]["serviceCategory"] == "ALL"
    assert payload["items"][0]["thresholdValue"] == 22.0
