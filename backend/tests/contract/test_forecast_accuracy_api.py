from __future__ import annotations

from tests.forecast_accuracy_test_helpers import seed_forecast_accuracy_data


def test_forecast_accuracy_contract_success(app_client, planner_headers, session) -> None:
    seed_forecast_accuracy_data(session)
    response = app_client.get(
        "/api/v1/forecast-accuracy",
        params={
            "timeRangeStart": "2026-03-01T00:00:00Z",
            "timeRangeEnd": "2026-03-02T00:00:00Z",
            "serviceCategory": "Roads",
        },
        headers=planner_headers,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["viewStatus"] == "rendered_with_metrics"
    assert len(payload["alignedBuckets"]) == 2

    render_response = app_client.post(
        f"/api/v1/forecast-accuracy/{payload['forecastAccuracyRequestId']}/render-events",
        json={"renderStatus": "rendered"},
        headers=planner_headers,
    )
    assert render_response.status_code == 202
    assert render_response.json()["recordedOutcomeStatus"] == "rendered"


def test_forecast_accuracy_contract_auth_and_validation(app_client, planner_headers, viewer_headers) -> None:
    unauthenticated = app_client.get("/api/v1/forecast-accuracy")
    assert unauthenticated.status_code == 401

    forbidden = app_client.get("/api/v1/forecast-accuracy", headers=viewer_headers)
    assert forbidden.status_code == 403

    invalid = app_client.get(
        "/api/v1/forecast-accuracy",
        params={
            "timeRangeStart": "2026-03-02T00:00:00Z",
            "timeRangeEnd": "2026-03-01T00:00:00Z",
        },
        headers=planner_headers,
    )
    assert invalid.status_code == 422
