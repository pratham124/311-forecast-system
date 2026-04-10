from __future__ import annotations

from datetime import datetime, timezone

from tests.forecast_accuracy_test_helpers import seed_forecast_accuracy_data
from app.models import ForecastAccuracyComparisonResult, ForecastAccuracyMetricResolution


def test_forecast_accuracy_metrics_fallback_persists_unavailable_status(app_client, planner_headers, session) -> None:
    seed_forecast_accuracy_data(
        session,
        actual_records=[
            {"service_request_id": "actual-1", "requested_at": "2026-03-01T00:10:00Z", "category": "Roads"},
        ],
        forecast_buckets=[
            {
                "bucket_start": datetime(2026, 3, 1, 0, tzinfo=timezone.utc),
                "bucket_end": datetime(2026, 3, 1, 1, tzinfo=timezone.utc),
                "service_category": "Roads",
                "geography_key": None,
                "point_forecast": 4.0,
                "quantile_p10": 2.0,
                "quantile_p50": 4.0,
                "quantile_p90": 6.0,
                "baseline_value": 3.0,
            }
        ],
    )
    response = app_client.get(
        "/api/v1/forecast-accuracy",
        params={
            "timeRangeStart": "2026-03-01T00:00:00Z",
            "timeRangeEnd": "2026-03-01T01:00:00Z",
            "serviceCategory": "Roads",
        },
        headers=planner_headers,
    )
    assert response.status_code == 200
    payload = response.json()
    resolution = session.query(ForecastAccuracyMetricResolution).one()
    result = session.query(ForecastAccuracyComparisonResult).one()
    assert payload["correlationId"] == payload["forecastAccuracyRequestId"]
    assert resolution.resolution_status == "unavailable"
    assert result.view_status == "rendered_without_metrics"
