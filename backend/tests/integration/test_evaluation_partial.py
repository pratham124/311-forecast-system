from __future__ import annotations

from tests.evaluation_helpers import seed_daily_evaluation_inputs


def test_partial_evaluation_marks_excluded_metrics(app_client, operational_manager_headers, planner_headers, session) -> None:
    seed_daily_evaluation_inputs(session, include_zero_actual=True, seed_tag="partial-integration")

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
    assert any(segment["excludedMetricCount"] > 0 for segment in body["segments"])
    assert "fairComparison" in body
    assert len(body["segments"]) >= 5
    assert body["fairComparison"]["evaluationWindowStart"] == body["evaluationWindowStart"]
    assert body["fairComparison"]["evaluationWindowEnd"] == body["evaluationWindowEnd"]


def test_partial_evaluation_skips_sparse_categories_without_baseline_history(app_client, operational_manager_headers, planner_headers, session) -> None:
    seed_daily_evaluation_inputs(session, extra_forecast_categories=['Cemeteries'], seed_tag='partial-sparse')

    response = app_client.post(
        '/api/v1/evaluation-runs/trigger',
        json={'forecastProduct': 'daily_1_day', 'triggerType': 'on_demand'},
        headers=operational_manager_headers,
    )
    assert response.status_code == 202

    run_status = app_client.get(f"/api/v1/evaluation-runs/{response.json()['evaluationRunId']}", headers=planner_headers)
    assert run_status.status_code == 200
    assert run_status.json()['resultType'] == 'stored_partial'
    assert 'Cemeteries' in (run_status.json()['summary'] or '')

    current = app_client.get('/api/v1/evaluations/current', params={'forecastProduct': 'daily_1_day'}, headers=planner_headers)
    assert current.status_code == 200
    body = current.json()
    assert body['comparisonStatus'] == 'partial'
    overall = next(segment for segment in body['segments'] if segment['segmentType'] == 'overall')
    assert 'Cemeteries' in (overall['notes'] or '')
    cemeteries = next(segment for segment in body['segments'] if segment['segmentType'] == 'service_category' and segment['segmentKey'] == 'Cemeteries')
    assert cemeteries['segmentStatus'] == 'partial'
    assert cemeteries['comparisonRowCount'] == 0
    assert cemeteries['notes']
