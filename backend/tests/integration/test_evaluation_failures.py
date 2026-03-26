from __future__ import annotations

from sqlalchemy import delete

from app.models import CleanedCurrentRecord, CurrentDatasetMarker, CurrentForecastMarker, ForecastBucket, ForecastVersion
from app.repositories.evaluation_repository import EvaluationRepository
from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
from app.repositories.forecast_repository import ForecastRepository
from app.repositories.weekly_forecast_repository import WeeklyForecastRepository
from app.services.evaluation_service import EvaluationService
from tests.evaluation_helpers import seed_daily_evaluation_inputs


SETTINGS = type(
    "Settings",
    (),
    {
        "source_name": "edmonton_311",
        "forecast_product_name": "daily_1_day_demand",
        "weekly_forecast_product_name": "weekly_7_day_demand",
        "weekly_forecast_timezone": "America/Edmonton",
        "evaluation_baseline_methods": "seasonal_naive,moving_average",
    },
)()


def _build_service(session) -> EvaluationService:
    return EvaluationService(
        evaluation_repository=EvaluationRepository(session),
        cleaned_dataset_repository=CleanedDatasetRepository(session),
        forecast_repository=ForecastRepository(session),
        weekly_forecast_repository=WeeklyForecastRepository(session),
        settings=SETTINGS,
    )


def test_missing_forecast_output_fails_without_current_replacement(app_client, operational_manager_headers, planner_headers, session) -> None:
    response = app_client.post(
        "/api/v1/evaluation-runs/trigger",
        json={"forecastProduct": "daily_1_day", "triggerType": "on_demand"},
        headers=operational_manager_headers,
    )
    assert response.status_code == 202
    run_id = response.json()["evaluationRunId"]

    run_status = app_client.get(f"/api/v1/evaluation-runs/{run_id}", headers=planner_headers)
    assert run_status.status_code == 200
    assert run_status.json()["resultType"] in {"missing_input_data", "missing_forecast_output"}


def test_baseline_failure_is_recorded(app_client, operational_manager_headers, planner_headers, session) -> None:
    session.execute(delete(CleanedCurrentRecord).where(CleanedCurrentRecord.source_name == "edmonton_311"))
    session.commit()
    seed_daily_evaluation_inputs(session, with_history=False, seed_tag="baseline-failure")

    response = app_client.post(
        "/api/v1/evaluation-runs/trigger",
        json={"forecastProduct": "daily_1_day", "triggerType": "on_demand"},
        headers=operational_manager_headers,
    )
    run_status = app_client.get(f"/api/v1/evaluation-runs/{response.json()['evaluationRunId']}", headers=planner_headers)
    assert run_status.json()["resultType"] == "baseline_failure"


def test_storage_failure_preserves_previous_current_marker(session) -> None:
    seed_daily_evaluation_inputs(session, seed_tag="storage-initial")
    service = _build_service(session)
    first_run = service.start_run("daily_1_day", "on_demand")
    session.commit()
    service.execute_run(first_run.evaluation_run_id)
    session.commit()
    previous_marker = service.evaluation_repository.get_current_marker("daily_1_day")
    assert previous_marker is not None

    second_run = service.start_run("daily_1_day", "on_demand")
    session.commit()
    original_activate = service.evaluation_repository.activate_result
    service.evaluation_repository.activate_result = lambda **kwargs: (_ for _ in ()).throw(RuntimeError("disk full"))
    failed = service.execute_run(second_run.evaluation_run_id)
    session.commit()
    service.evaluation_repository.activate_result = original_activate

    current_marker = service.evaluation_repository.get_current_marker("daily_1_day")
    assert failed.result_type == "storage_failure"
    assert current_marker is not None
    assert current_marker.evaluation_result_id == previous_marker.evaluation_result_id


def test_previous_result_is_retained_across_all_failure_paths(session) -> None:
    seed_daily_evaluation_inputs(session, seed_tag="retained-initial")
    service = _build_service(session)
    success_run = service.start_run("daily_1_day", "on_demand")
    session.commit()
    service.execute_run(success_run.evaluation_run_id)
    session.commit()
    retained_marker = service.evaluation_repository.get_current_marker("daily_1_day")
    assert retained_marker is not None

    session.execute(delete(CurrentForecastMarker).where(CurrentForecastMarker.forecast_product_name == "daily_1_day_demand"))
    session.execute(delete(ForecastBucket))
    session.execute(delete(ForecastVersion))
    session.commit()
    missing_forecast_run = service.start_run("daily_1_day", "on_demand")
    session.commit()
    result = service.execute_run(missing_forecast_run.evaluation_run_id)
    session.commit()
    assert result.result_type == "missing_forecast_output"
    assert service.evaluation_repository.get_current_marker("daily_1_day").evaluation_result_id == retained_marker.evaluation_result_id

    session.execute(delete(CleanedCurrentRecord).where(CleanedCurrentRecord.source_name == "edmonton_311"))
    session.commit()
    seed_daily_evaluation_inputs(session, with_history=False, seed_tag="retained-baseline")
    baseline_failure_run = service.start_run("daily_1_day", "on_demand")
    session.commit()
    result = service.execute_run(baseline_failure_run.evaluation_run_id)
    session.commit()
    assert result.result_type == "baseline_failure"
    assert service.evaluation_repository.get_current_marker("daily_1_day").evaluation_result_id == retained_marker.evaluation_result_id

    session.execute(delete(CurrentDatasetMarker).where(CurrentDatasetMarker.source_name == "edmonton_311"))
    session.commit()
    missing_input_run = service.start_run("daily_1_day", "on_demand")
    session.commit()
    result = service.execute_run(missing_input_run.evaluation_run_id)
    session.commit()
    assert result.result_type == "missing_input_data"
    assert service.evaluation_repository.get_current_marker("daily_1_day").evaluation_result_id == retained_marker.evaluation_result_id

    seed_daily_evaluation_inputs(session, seed_tag="retained-storage")
    storage_failure_run = service.start_run("daily_1_day", "on_demand")
    session.commit()
    original_activate = service.evaluation_repository.activate_result
    service.evaluation_repository.activate_result = lambda **kwargs: (_ for _ in ()).throw(RuntimeError("disk full"))
    result = service.execute_run(storage_failure_run.evaluation_run_id)
    session.commit()
    service.evaluation_repository.activate_result = original_activate
    assert result.result_type == "storage_failure"
    assert service.evaluation_repository.get_current_marker("daily_1_day").evaluation_result_id == retained_marker.evaluation_result_id
