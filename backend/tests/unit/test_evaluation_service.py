from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.core.logging import summarize_evaluation_failure, summarize_evaluation_partial_success, summarize_evaluation_success
from app.services.baseline_service import BaselineGenerationError
from app.services.evaluation_metrics import compute_metric_values
from app.services.evaluation_scope_service import EvaluationScopeService, MissingForecastScopeError
from app.services.evaluation_segments import build_evaluation_segments
from app.services.evaluation_service import EvaluationService


@pytest.mark.unit
def test_metric_computation_excludes_mape_for_zero_actuals() -> None:
    metrics = compute_metric_values(
        [{"forecast_engine": 4.0, "actual": 0.0}],
        "forecast_engine",
        "Forecast Engine",
    )
    excluded = next(metric for metric in metrics["metrics"] if metric["metric_name"] == "mape")
    assert excluded["is_excluded"] is True


@pytest.mark.unit
def test_scope_service_resolves_daily_and_weekly_markers() -> None:
    cleaned_repo = SimpleNamespace(get_current_approved_dataset=lambda _source: SimpleNamespace(dataset_version_id="dataset-1"))
    forecast_repo = SimpleNamespace(get_current_marker=lambda _product: SimpleNamespace(forecast_version_id="forecast-1", horizon_start=datetime(2026, 3, 20, tzinfo=timezone.utc), horizon_end=datetime(2026, 3, 20, 3, tzinfo=timezone.utc)))
    weekly_repo = SimpleNamespace(get_current_marker=lambda _product: SimpleNamespace(weekly_forecast_version_id="weekly-1", week_start_local=datetime(2026, 3, 23, tzinfo=timezone.utc), week_end_local=datetime(2026, 3, 26, tzinfo=timezone.utc)))
    settings = SimpleNamespace(source_name="edmonton_311", forecast_product_name="daily_1_day_demand", weekly_forecast_product_name="weekly_7_day_demand", weekly_forecast_timezone="America/Edmonton")
    service = EvaluationScopeService(cleaned_repo, forecast_repo, weekly_repo, settings)

    daily = service.resolve_scope("daily_1_day")
    weekly = service.resolve_scope("weekly_7_day")

    assert daily.source_forecast_version_id == "forecast-1"
    assert weekly.source_weekly_forecast_version_id == "weekly-1"


@pytest.mark.unit
def test_category_and_time_period_aggregation_and_exclusion_labels() -> None:
    segments, status = build_evaluation_segments([
        {"service_category": "Roads", "time_period_key": "2026-03-20T00:00:00Z", "forecast_engine": 2.0, "seasonal_naive": 1.0, "moving_average": 1.5, "actual": 1.0},
        {"service_category": "Roads", "time_period_key": "2026-03-20T01:00:00Z", "forecast_engine": 3.0, "seasonal_naive": 2.0, "moving_average": 2.5, "actual": 0.0},
        {"service_category": "Waste", "time_period_key": "2026-03-20T01:00:00Z", "forecast_engine": 4.0, "seasonal_naive": 2.5, "moving_average": 3.0, "actual": 2.0},
    ])
    assert status == "partial"
    roads_segment = next(segment for segment in segments if segment["segment_type"] == "service_category" and segment["segment_key"] == "Roads")
    period_segment = next(segment for segment in segments if segment["segment_type"] == "time_period" and segment["segment_key"] == "2026-03-20T01:00:00Z")
    assert roads_segment["segment_status"] == "partial"
    assert period_segment["segment_status"] == "partial"
    assert any(segment["segment_type"] == "service_category" and segment["segment_key"] == "Waste" for segment in segments)
    partial_segment = next(segment for segment in segments if segment["excluded_metric_count"] > 0)
    assert partial_segment["segment_status"] == "partial"
    assert partial_segment["notes"] is not None
    excluded_metric = next(
        metric
        for method in partial_segment["method_metrics"]
        for metric in method["metrics"]
        if metric["is_excluded"]
    )
    assert excluded_metric["exclusion_reason"] == "MAPE cannot be computed when actual demand includes zero values"


@pytest.mark.unit
def test_evaluation_service_fails_when_cleaned_dataset_missing() -> None:
    repo = SimpleNamespace(require_run=lambda _run_id: SimpleNamespace(evaluation_run_id="run-1", status="running", source_cleaned_dataset_version_id=None), finalize_failed=lambda run_id, **kwargs: SimpleNamespace(result_type=kwargs["result_type"], run_id=run_id))
    service = EvaluationService(
        evaluation_repository=repo,
        cleaned_dataset_repository=SimpleNamespace(),
        forecast_repository=SimpleNamespace(),
        weekly_forecast_repository=SimpleNamespace(),
        settings=SimpleNamespace(source_name="edmonton_311", forecast_product_name="daily_1_day_demand", weekly_forecast_product_name="weekly_7_day_demand", weekly_forecast_timezone="America/Edmonton", evaluation_baseline_methods="seasonal_naive,moving_average"),
    )

    failed = service.execute_run("run-1")
    assert failed.result_type == "missing_input_data"


@pytest.mark.unit
def test_failure_outcome_selection_for_missing_forecast_baseline_and_storage() -> None:
    run = SimpleNamespace(
        evaluation_run_id="run-1",
        status="running",
        source_cleaned_dataset_version_id="dataset-1",
        source_forecast_version_id="forecast-1",
        source_weekly_forecast_version_id=None,
        evaluation_window_start=datetime(2026, 3, 20, tzinfo=timezone.utc),
        evaluation_window_end=datetime(2026, 3, 20, 3, tzinfo=timezone.utc),
        forecast_product_name="daily_1_day",
    )
    repo = SimpleNamespace(
        require_run=lambda _run_id: run,
        finalize_failed=lambda run_id, **kwargs: SimpleNamespace(result_type=kwargs["result_type"]),
        create_result=lambda **kwargs: SimpleNamespace(evaluation_result_id="result-1"),
        replace_segments=lambda *_args, **_kwargs: None,
        store_result_and_activate=lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("disk full")),
    )
    settings = SimpleNamespace(source_name="edmonton_311", forecast_product_name="daily_1_day_demand", weekly_forecast_product_name="weekly_7_day_demand", weekly_forecast_timezone="America/Edmonton", evaluation_baseline_methods="seasonal_naive,moving_average")
    service = EvaluationService(repo, SimpleNamespace(), SimpleNamespace(), SimpleNamespace(), settings)

    service.scope_service = SimpleNamespace(
        resolve_scope_from_run=lambda _run: SimpleNamespace(forecast_product_name="daily_1_day"),
        list_engine_rows=lambda _scope: (_ for _ in ()).throw(MissingForecastScopeError("no forecast")),
        list_actual_rows=lambda _scope: {},
        build_aligned_rows=lambda _scope, _engine, _actual: [],
    )
    failed = service.execute_run("run-1")
    assert failed.result_type == "missing_forecast_output"

    service.scope_service = SimpleNamespace(
        resolve_scope_from_run=lambda _run: SimpleNamespace(forecast_product_name="daily_1_day"),
        list_engine_rows=lambda _scope: [{"service_category": "Roads", "time_period_key": "t", "bucket_start": datetime(2026, 3, 20, tzinfo=timezone.utc), "bucket_end": datetime(2026, 3, 20, 1, tzinfo=timezone.utc), "forecast_engine": 2.0}],
        list_actual_rows=lambda _scope: {},
        build_aligned_rows=lambda _scope, _engine, _actual: [{"service_category": "Roads", "time_period_key": "t", "bucket_start": datetime(2026, 3, 20, tzinfo=timezone.utc), "bucket_end": datetime(2026, 3, 20, 1, tzinfo=timezone.utc), "forecast_engine": 2.0, "actual": 1.0}],
    )
    service.baseline_service = SimpleNamespace(generate_baselines=lambda *_args, **_kwargs: (_ for _ in ()).throw(BaselineGenerationError("baseline boom")))
    failed = service.execute_run("run-1")
    assert failed.result_type == "baseline_failure"

    service.baseline_service = SimpleNamespace(generate_baselines=lambda *_args, **_kwargs: [{"service_category": "Roads", "time_period_key": "t", "forecast_engine": 2.0, "seasonal_naive": 1.0, "moving_average": 1.5, "actual": 1.0}])
    failed = service.execute_run("run-1")
    assert failed.result_type == "storage_failure"


@pytest.mark.unit

@pytest.mark.unit
def test_sparse_baseline_scope_produces_partial_result() -> None:
    run = SimpleNamespace(
        evaluation_run_id="run-partial",
        status="running",
        source_cleaned_dataset_version_id="dataset-1",
        source_forecast_version_id="forecast-1",
        source_weekly_forecast_version_id=None,
        evaluation_window_start=datetime(2026, 3, 20, tzinfo=timezone.utc),
        evaluation_window_end=datetime(2026, 3, 20, 3, tzinfo=timezone.utc),
        forecast_product_name="daily_1_day",
    )
    repo = SimpleNamespace(
        require_run=lambda _run_id: run,
        create_result=lambda **kwargs: SimpleNamespace(evaluation_result_id="result-1"),
        replace_segments=lambda *_args, **_kwargs: None,
        store_result_and_activate=lambda **_kwargs: None,
        finalize_success=lambda _run_id, **kwargs: SimpleNamespace(result_type=kwargs["result_type"], summary=kwargs["summary"]),
    )
    settings = SimpleNamespace(source_name="edmonton_311", forecast_product_name="daily_1_day_demand", weekly_forecast_product_name="weekly_7_day_demand", weekly_forecast_timezone="America/Edmonton", evaluation_baseline_methods="seasonal_naive,moving_average")
    service = EvaluationService(repo, SimpleNamespace(), SimpleNamespace(), SimpleNamespace(), settings)
    service.scope_service = SimpleNamespace(
        resolve_scope_from_run=lambda _run: SimpleNamespace(forecast_product_name="daily_1_day"),
        list_engine_rows=lambda _scope: [{"service_category": "Roads", "time_period_key": "t", "bucket_start": datetime(2026, 3, 20, tzinfo=timezone.utc), "bucket_end": datetime(2026, 3, 20, 1, tzinfo=timezone.utc), "forecast_engine": 2.0}],
        list_actual_rows=lambda _scope: {},
        build_aligned_rows=lambda _scope, _engine, _actual: [{"service_category": "Roads", "time_period_key": "t", "bucket_start": datetime(2026, 3, 20, tzinfo=timezone.utc), "bucket_end": datetime(2026, 3, 20, 1, tzinfo=timezone.utc), "forecast_engine": 2.0, "actual": 1.0}],
    )

    class PartialRows(list):
        def __init__(self):
            super().__init__([{"service_category": "Roads", "time_period_key": "t", "forecast_engine": 2.0, "seasonal_naive": 1.0, "moving_average": 1.5, "actual": 1.0}])
            self.excluded_scopes = ["Cemeteries"]

    service.baseline_service = SimpleNamespace(generate_baselines=lambda *_args, **_kwargs: PartialRows())
    result = service.execute_run("run-partial")
    assert result.result_type == "stored_partial"
    assert "Cemeteries" in result.summary


def test_missing_input_from_alignment_is_recorded_as_missing_input() -> None:
    run = SimpleNamespace(
        evaluation_run_id="run-2",
        status="running",
        source_cleaned_dataset_version_id="dataset-1",
        source_forecast_version_id="forecast-1",
        source_weekly_forecast_version_id=None,
        evaluation_window_start=datetime(2026, 3, 20, tzinfo=timezone.utc),
        evaluation_window_end=datetime(2026, 3, 20, 3, tzinfo=timezone.utc),
        forecast_product_name="daily_1_day",
    )
    repo = SimpleNamespace(
        require_run=lambda _run_id: run,
        finalize_failed=lambda run_id, **kwargs: SimpleNamespace(result_type=kwargs["result_type"], failure_reason=kwargs["failure_reason"]),
    )
    settings = SimpleNamespace(source_name="edmonton_311", forecast_product_name="daily_1_day_demand", weekly_forecast_product_name="weekly_7_day_demand", weekly_forecast_timezone="America/Edmonton", evaluation_baseline_methods="seasonal_naive,moving_average")
    service = EvaluationService(repo, SimpleNamespace(), SimpleNamespace(), SimpleNamespace(), settings)
    service.scope_service = SimpleNamespace(
        resolve_scope_from_run=lambda _run: SimpleNamespace(forecast_product_name="daily_1_day"),
        list_engine_rows=lambda _scope: [{"service_category": "Roads", "time_period_key": "t"}],
        list_actual_rows=lambda _scope: {},
        build_aligned_rows=lambda _scope, _engine, _actual: (_ for _ in ()).throw(MissingForecastScopeError("actuals missing")),
    )

    failed = service.execute_run("run-2")
    assert failed.result_type == "missing_input_data"
    assert failed.failure_reason == "actuals missing"


@pytest.mark.unit
def test_evaluation_logging_helpers_label_outcomes() -> None:
    success = summarize_evaluation_success("evaluation.stored", run_id="run-1", forecast_product="daily_1_day")
    partial = summarize_evaluation_partial_success("evaluation.stored", run_id="run-1", forecast_product="daily_1_day")
    failure = summarize_evaluation_failure("evaluation.failed", run_id="run-1", result_type="storage_failure")
    assert success["outcome"] == "success"
    assert success["forecast_product"] == "daily_1_day"
    assert partial["outcome"] == "partial_success"
    assert failure["outcome"] == "failure"
    assert failure["result_type"] == "storage_failure"
