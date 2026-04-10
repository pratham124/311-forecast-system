from __future__ import annotations

from tests.forecast_accuracy_test_helpers import seed_forecast_accuracy_data


def test_forecast_accuracy_contract_metrics_fallback(app_client, planner_headers, session) -> None:
    seed_forecast_accuracy_data(
        session,
        actual_records=[
            {"service_request_id": "actual-1", "requested_at": "2026-03-01T00:10:00Z", "category": "Roads"},
        ],
        forecast_buckets=[
            {
                "bucket_start": __import__("datetime").datetime(2026, 3, 1, 0, tzinfo=__import__("datetime").timezone.utc),
                "bucket_end": __import__("datetime").datetime(2026, 3, 1, 1, tzinfo=__import__("datetime").timezone.utc),
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
    assert payload["viewStatus"] == "rendered_without_metrics"
    assert payload["metricResolutionStatus"] == "unavailable"
    assert payload["alignedBuckets"]
