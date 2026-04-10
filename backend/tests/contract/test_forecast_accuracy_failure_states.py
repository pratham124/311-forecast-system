from __future__ import annotations

from app.repositories.forecast_accuracy_repository import ForecastAccuracyRepository


def test_forecast_accuracy_contract_failure_and_render_errors(app_client, planner_headers, viewer_headers, session) -> None:
    response = app_client.get(
        "/api/v1/forecast-accuracy",
        params={
            "timeRangeStart": "2026-03-01T00:00:00Z",
            "timeRangeEnd": "2026-03-02T00:00:00Z",
        },
        headers=planner_headers,
    )
    assert response.status_code == 200
    assert response.json()["viewStatus"] == "unavailable"

    missing = app_client.post(
        "/api/v1/forecast-accuracy/missing/render-events",
        json={"renderStatus": "rendered"},
        headers=planner_headers,
    )
    assert missing.status_code == 404

    invalid = app_client.post(
        "/api/v1/forecast-accuracy/missing/render-events",
        json={"renderStatus": "render_failed"},
        headers=planner_headers,
    )
    assert invalid.status_code == 422

    request = ForecastAccuracyRepository(session).create_request(
        requested_by_actor="city_planner",
        requested_by_subject="someone-else",
        source_cleaned_dataset_version_id=None,
        source_forecast_version_id=None,
        source_evaluation_result_id=None,
        forecast_product_name="daily_1_day",
        comparison_granularity="hourly",
        time_range_start=__import__("datetime").datetime(2026, 3, 1, tzinfo=__import__("datetime").timezone.utc),
        time_range_end=__import__("datetime").datetime(2026, 3, 2, tzinfo=__import__("datetime").timezone.utc),
        service_category=None,
        status="running",
        correlation_id=None,
    )
    result = ForecastAccuracyRepository(session).create_result(
        forecast_accuracy_request_id=request.forecast_accuracy_request_id,
        view_status="rendered_with_metrics",
        metric_resolution_status="computed_on_demand",
        status_message=None,
        aligned_bucket_count=1,
        excluded_bucket_count=0,
    )
    session.commit()
    forbidden = app_client.post(
        f"/api/v1/forecast-accuracy/{request.forecast_accuracy_request_id}/render-events",
        json={"renderStatus": "rendered"},
        headers=planner_headers,
    )
    assert forbidden.status_code == 403

    unauthenticated = app_client.post(
        f"/api/v1/forecast-accuracy/{request.forecast_accuracy_request_id}/render-events",
        json={"renderStatus": "rendered"},
    )
    assert unauthenticated.status_code == 401
    assert result.forecast_accuracy_result_id is not None
