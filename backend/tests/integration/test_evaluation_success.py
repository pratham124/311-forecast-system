from __future__ import annotations

from datetime import datetime

from app.core.db import get_session_factory
from app.repositories.evaluation_repository import EvaluationRepository
from app.services.evaluation_service import build_evaluation_job
from tests.evaluation_helpers import seed_daily_evaluation_inputs, seed_weekly_evaluation_inputs


def test_on_demand_evaluation_stores_daily_result(app_client, operational_manager_headers, planner_headers, session) -> None:
    seed_daily_evaluation_inputs(session, seed_tag="success-daily")

    response = app_client.post(
        "/api/v1/evaluation-runs/trigger",
        json={"forecastProduct": "daily_1_day", "triggerType": "on_demand"},
        headers=operational_manager_headers,
    )
    assert response.status_code == 202

    run_id = response.json()["evaluationRunId"]
    run_status = app_client.get(f"/api/v1/evaluation-runs/{run_id}", headers=planner_headers).json()
    assert run_status["status"] == "success"
    assert run_status["resultType"] == "stored_complete"
    started = datetime.fromisoformat(run_status["startedAt"].replace("Z", "+00:00"))
    completed = datetime.fromisoformat(run_status["completedAt"].replace("Z", "+00:00"))
    assert (completed - started).total_seconds() < 1800

    repo = EvaluationRepository(session)
    current = repo.get_current_result("daily_1_day")
    assert current is not None
    bundles = repo.list_result_bundles_for_product("daily_1_day", limit=3)
    assert bundles
    assert bundles[0].result.evaluation_result_id == current.evaluation_result_id
    assert any(segment.segment_type == "overall" for segment in bundles[0].segments)


def test_scheduled_evaluation_runs_for_both_products(session) -> None:
    seed_daily_evaluation_inputs(session, seed_tag="scheduled-daily")
    seed_weekly_evaluation_inputs(session, seed_tag="scheduled-weekly")

    run_ids = build_evaluation_job(get_session_factory())()
    repo = EvaluationRepository(session)

    assert len(run_ids) == 2
    assert repo.get_current_result("daily_1_day") is not None
    assert repo.get_current_result("weekly_7_day") is not None
    assert len(repo.list_results_for_product("daily_1_day", limit=5)) >= 1
    assert len(repo.list_result_bundles_for_product("weekly_7_day", limit=5)) >= 1
