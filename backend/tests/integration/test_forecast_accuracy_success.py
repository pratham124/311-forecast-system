from __future__ import annotations

from tests.forecast_accuracy_test_helpers import seed_forecast_accuracy_data
from app.models import ForecastAccuracyAlignedBucket, ForecastAccuracyComparisonResult, ForecastAccuracyMetricResolution, ForecastAccuracyRequest


def test_forecast_accuracy_success_persists_request_and_result(app_client, planner_headers, session) -> None:
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
    request = session.get(ForecastAccuracyRequest, payload["forecastAccuracyRequestId"])
    result = session.get(ForecastAccuracyComparisonResult, payload["forecastAccuracyResultId"])
    assert request is not None
    assert result is not None
    assert request.status == "rendered_with_metrics"
    assert payload["correlationId"] == payload["forecastAccuracyRequestId"]
    assert request.correlation_id == payload["correlationId"]
    assert result.view_status == "rendered_with_metrics"
    assert session.query(ForecastAccuracyMetricResolution).count() == 1
    assert session.query(ForecastAccuracyAlignedBucket).count() == 2
