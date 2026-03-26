from __future__ import annotations

from datetime import datetime, timezone

from tests.evaluation_helpers import seed_daily_evaluation_inputs, seed_weekly_evaluation_inputs


def test_evaluation_trigger_and_current_daily_flow(app_client, operational_manager_headers, planner_headers, session) -> None:
    seed_daily_evaluation_inputs(session, seed_tag="daily-flow")

    trigger = app_client.post(
        "/api/v1/evaluation-runs/trigger",
        json={"forecastProduct": "daily_1_day", "triggerType": "on_demand"},
        headers=operational_manager_headers,
    )
    assert trigger.status_code == 202
    run_id = trigger.json()["evaluationRunId"]

    run_status = app_client.get(f"/api/v1/evaluation-runs/{run_id}", headers=planner_headers)
    assert run_status.status_code == 200
    assert run_status.json()["resultType"] == "stored_complete"

    current = app_client.get("/api/v1/evaluations/current", params={"forecastProduct": "daily_1_day"}, headers=planner_headers)
    assert current.status_code == 200
    body = current.json()
    assert body["forecastProduct"] == "daily_1_day"
    assert body["comparisonStatus"] == "complete"
    assert body["baselineMethods"] == ["seasonal_naive", "moving_average"]


def test_evaluation_prefers_latest_completed_daily_window_when_current_marker_is_future(app_client, operational_manager_headers, planner_headers, session) -> None:
    seed_daily_evaluation_inputs(session, seed_tag="completed-window")
    seed_daily_evaluation_inputs(
        session,
        with_evaluation_actuals=False,
        horizon_start=datetime(2026, 3, 27, 0, tzinfo=timezone.utc),
        seed_tag="future-window",
    )

    trigger = app_client.post(
        "/api/v1/evaluation-runs/trigger",
        json={"forecastProduct": "daily_1_day", "triggerType": "on_demand"},
        headers=operational_manager_headers,
    )
    assert trigger.status_code == 202

    run_status = app_client.get(f"/api/v1/evaluation-runs/{trigger.json()['evaluationRunId']}", headers=planner_headers)
    assert run_status.status_code == 200
    assert run_status.json()["resultType"] == "stored_complete"

    current = app_client.get("/api/v1/evaluations/current", params={"forecastProduct": "daily_1_day"}, headers=planner_headers)
    assert current.status_code == 200
    assert current.json()["evaluationWindowStart"].startswith("2026-03-20T00:00:00")


def test_evaluation_current_weekly_flow(app_client, operational_manager_headers, planner_headers, session) -> None:
    seed_weekly_evaluation_inputs(session, seed_tag="weekly-flow")
    response = app_client.post(
        "/api/v1/evaluation-runs/trigger",
        json={"forecastProduct": "weekly_7_day", "triggerType": "on_demand"},
        headers=operational_manager_headers,
    )
    assert response.status_code == 202
    current = app_client.get("/api/v1/evaluations/current", params={"forecastProduct": "weekly_7_day"}, headers=planner_headers)
    assert current.status_code == 200
    assert current.json()["forecastProduct"] == "weekly_7_day"


def test_segmented_current_evaluation_and_partial_payload_structure(app_client, operational_manager_headers, planner_headers, session) -> None:
    seed_daily_evaluation_inputs(session, include_zero_actual=True, seed_tag="partial-flow")
    response = app_client.post(
        "/api/v1/evaluation-runs/trigger",
        json={"forecastProduct": "daily_1_day", "triggerType": "on_demand"},
        headers=operational_manager_headers,
    )
    assert response.status_code == 202

    current = app_client.get("/api/v1/evaluations/current", params={"forecastProduct": "daily_1_day"}, headers=planner_headers)
    assert current.status_code == 200
    body = current.json()
    assert body["comparisonStatus"] == "partial"
    assert body["fairComparison"]["productScope"] == "daily_1_day"
    assert "overall" in body["fairComparison"]["segmentCoverage"]
    assert any(segment["segmentType"] == "service_category" for segment in body["segments"])
    assert any(segment["segmentType"] == "time_period" for segment in body["segments"])
    assert any(segment["excludedMetricCount"] > 0 for segment in body["segments"])
    partial_segment = next(segment for segment in body["segments"] if segment["excludedMetricCount"] > 0)
    assert partial_segment["segmentStatus"] == "partial"
    assert partial_segment["notes"]
    assert partial_segment["methodMetrics"]
    assert any(metric["isExcluded"] for method in partial_segment["methodMetrics"] for metric in method["metrics"])
    assert any(metric["exclusionReason"] for method in partial_segment["methodMetrics"] for metric in method["metrics"] if metric["isExcluded"])


def test_future_window_run_reports_actuals_not_available(app_client, operational_manager_headers, planner_headers, session) -> None:
    seed_daily_evaluation_inputs(session, with_evaluation_actuals=False, horizon_start=datetime(2026, 3, 27, 0, tzinfo=timezone.utc), seed_tag="future-only")

    response = app_client.post(
        "/api/v1/evaluation-runs/trigger",
        json={"forecastProduct": "daily_1_day", "triggerType": "on_demand"},
        headers=operational_manager_headers,
    )
    assert response.status_code == 202

    run_status = app_client.get(f"/api/v1/evaluation-runs/{response.json()['evaluationRunId']}", headers=planner_headers)
    assert run_status.status_code == 200
    assert run_status.json()["status"] == "failed"
    assert run_status.json()["resultType"] == "actuals_not_available"
    assert run_status.json()["failureReason"]

    missing_current = app_client.get("/api/v1/evaluations/current", params={"forecastProduct": "daily_1_day"}, headers=planner_headers)
    assert missing_current.status_code == 404


def test_failed_status_missing_current_and_access_denial_are_separate(app_client, operational_manager_headers, planner_headers, viewer_headers, session) -> None:
    response = app_client.post(
        "/api/v1/evaluation-runs/trigger",
        json={"forecastProduct": "daily_1_day", "triggerType": "on_demand"},
        headers=operational_manager_headers,
    )
    assert response.status_code == 202
    run_status = app_client.get(f"/api/v1/evaluation-runs/{response.json()['evaluationRunId']}", headers=planner_headers)
    assert run_status.status_code == 200
    assert run_status.json()["status"] == "failed"
    assert run_status.json()["resultType"] in {"missing_input_data", "missing_forecast_output", "actuals_not_available"}
    assert run_status.json()["failureReason"]

    missing_current = app_client.get("/api/v1/evaluations/current", params={"forecastProduct": "daily_1_day"}, headers=planner_headers)
    assert missing_current.status_code == 404

    forbidden_run = app_client.get(f"/api/v1/evaluation-runs/{response.json()['evaluationRunId']}", headers=viewer_headers)
    assert forbidden_run.status_code == 403

    forbidden = app_client.get("/api/v1/evaluations/current", params={"forecastProduct": "daily_1_day"}, headers=viewer_headers)
    assert forbidden.status_code == 403


def test_evaluation_routes_require_auth(app_client, viewer_headers) -> None:
    trigger = app_client.post("/api/v1/evaluation-runs/trigger", json={"forecastProduct": "daily_1_day"})
    assert trigger.status_code == 401

    forbidden = app_client.post(
        "/api/v1/evaluation-runs/trigger",
        json={"forecastProduct": "daily_1_day"},
        headers=viewer_headers,
    )
    assert forbidden.status_code == 403


def test_evaluation_request_validation(app_client, operational_manager_headers, planner_headers) -> None:
    invalid_trigger = app_client.post(
        "/api/v1/evaluation-runs/trigger",
        json={"forecastProduct": "monthly"},
        headers=operational_manager_headers,
    )
    assert invalid_trigger.status_code == 422

    invalid_current = app_client.get(
        "/api/v1/evaluations/current",
        params={"forecastProduct": "monthly"},
        headers=planner_headers,
    )
    assert invalid_current.status_code == 422
