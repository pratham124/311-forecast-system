from __future__ import annotations

from tests.forecast_accuracy_test_helpers import seed_forecast_accuracy_data
from app.models import ForecastAccuracyRenderEvent, ForecastAccuracyRequest


def test_forecast_accuracy_missing_forecast_and_render_failure_flow(app_client, planner_headers, session) -> None:
    response = app_client.get(
        "/api/v1/forecast-accuracy",
        params={"timeRangeStart": "2026-03-01T00:00:00Z", "timeRangeEnd": "2026-03-02T00:00:00Z"},
        headers=planner_headers,
    )
    assert response.status_code == 200
    payload = response.json()
    request = session.get(ForecastAccuracyRequest, payload["forecastAccuracyRequestId"])
    assert request is not None
    assert request.status == "forecast_missing"

    seeded = seed_forecast_accuracy_data(session)
    success = app_client.get(
        "/api/v1/forecast-accuracy",
        params={
            "timeRangeStart": "2026-03-01T00:00:00Z",
            "timeRangeEnd": "2026-03-02T00:00:00Z",
            "serviceCategory": "Roads",
        },
        headers=planner_headers,
    )
    assert success.status_code == 200
    request_id = success.json()["forecastAccuracyRequestId"]
    render = app_client.post(
        f"/api/v1/forecast-accuracy/{request_id}/render-events",
        json={"renderStatus": "render_failed", "failureReason": "chart crashed"},
        headers=planner_headers,
    )
    assert render.status_code == 202
    session.expire_all()
    updated = session.get(ForecastAccuracyRequest, request_id)
    assert updated is not None
    assert updated.status == "render_failed"
    assert session.query(ForecastAccuracyRenderEvent).count() == 1
    assert seeded["forecast_version_id"]
