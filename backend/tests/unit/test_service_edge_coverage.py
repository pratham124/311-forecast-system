from __future__ import annotations

from datetime import date, datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.services.alert_review_service import AlertReviewService
from app.services.forecast_scope_service import ForecastScopeService
from app.services.forecast_service import ForecastService
from app.pipelines.surge_alert_evaluation_pipeline import SurgeAlertEvaluationPipeline
from app.services.surge_scope_service import SurgeScopeService
from app.services.weekly_forecast_service import WeeklyForecastService


@pytest.mark.unit
def test_alert_review_service_raises_not_found_for_missing_event() -> None:
    service = AlertReviewService(repository=SimpleNamespace(get_event_bundle=lambda _event_id: None))

    with pytest.raises(HTTPException) as exc:
        service.get_event("missing")

    assert exc.value.status_code == 404


@pytest.mark.unit
def test_forecast_scope_service_filters_daily_and_weekly_buckets() -> None:
    daily_buckets = [
        SimpleNamespace(
            service_category="Roads",
            bucket_start=datetime(2026, 3, 20, 0, 0, tzinfo=timezone.utc),
            bucket_end=datetime(2026, 3, 20, 1, 0, tzinfo=timezone.utc),
            point_forecast=12,
        ),
        SimpleNamespace(
            service_category="Waste",
            bucket_start=datetime(2026, 3, 20, 1, 0, tzinfo=timezone.utc),
            bucket_end=datetime(2026, 3, 20, 2, 0, tzinfo=timezone.utc),
            point_forecast=9,
        ),
    ]
    weekly_buckets = [
        SimpleNamespace(service_category="Roads", forecast_date_local=date(2026, 3, 23), point_forecast=70),
        SimpleNamespace(service_category="Waste", forecast_date_local=date(2026, 3, 24), point_forecast=30),
    ]
    service = ForecastScopeService(
        forecast_repository=SimpleNamespace(list_buckets=lambda _ref: list(daily_buckets)),
        weekly_forecast_repository=SimpleNamespace(list_buckets=lambda _ref: list(weekly_buckets)),
    )

    daily = service.list_scopes(
        forecast_reference_id="daily-version",
        forecast_product="daily",
        service_category="Roads",
    )
    weekly = service.list_scopes(
        forecast_reference_id="weekly-version",
        forecast_product="weekly",
        service_category="Waste",
    )

    assert len(daily) == 1
    assert daily[0].forecast_window_type == "hourly"
    assert daily[0].service_category == "Roads"
    assert len(weekly) == 1
    assert weekly[0].forecast_window_type == "daily"
    assert weekly[0].service_category == "Waste"
    assert weekly[0].forecast_window_start == datetime(2026, 3, 24, 0, 0, tzinfo=timezone.utc)


@pytest.mark.unit
def test_weekly_forecast_service_logs_threshold_alert_failures_and_still_finalizes_generated(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = SimpleNamespace(
        source_name="edmonton_311",
        weekly_forecast_product_name="weekly_7_day_demand",
        weekly_forecast_timezone="America/Edmonton",
        weekly_forecast_history_days=56,
    )
    run = SimpleNamespace(
        weekly_forecast_run_id="run-1",
        status="running",
        trigger_type="scheduled",
        source_cleaned_dataset_version_id="dataset-1",
        week_start_local=datetime(2026, 3, 23, tzinfo=timezone.utc),
        week_end_local=datetime(2026, 3, 29, 23, 59, 59, tzinfo=timezone.utc),
    )
    finalized: list[dict[str, object]] = []
    warnings: list[str] = []
    run_repo = SimpleNamespace(
        get_run=lambda _run_id: run,
        finalize_generated=lambda run_id, **kwargs: finalized.append({"run_id": run_id, **kwargs}) or SimpleNamespace(status="completed", **kwargs),
        finalize_failed=lambda *args, **kwargs: None,
    )
    logger = SimpleNamespace(
        warning=lambda message, *args: warnings.append(message % args),
        info=lambda *args, **kwargs: None,
    )
    service = WeeklyForecastService(
        cleaned_dataset_repository=SimpleNamespace(
            list_current_cleaned_records=lambda *args, **kwargs: [{"requested_at": "2026-03-20T10:00:00Z", "category": "Roads"}],
        ),
        weekly_forecast_run_repository=run_repo,
        weekly_forecast_repository=SimpleNamespace(
            session="session",
            find_current_for_week=lambda **kwargs: None,
        ),
        settings=settings,
        geomet_client=SimpleNamespace(fetch_forecast_hourly_conditions=lambda start, end: []),
        nager_date_client=SimpleNamespace(fetch_holidays=lambda year: []),
        forecast_model_repository=SimpleNamespace(find_current_model=lambda *_args, **_kwargs: None),
        logger=logger,
    )
    service.pipeline = SimpleNamespace(run=lambda prepared: {"baseline_method": "baseline", "buckets": [{"x": 1}]})
    service.bucket_service = SimpleNamespace(build_buckets=lambda generated: ([{"bucket": 1}], "citywide"))
    service.activation_service = SimpleNamespace(store_and_activate=lambda **kwargs: "weekly-version-1")
    monkeypatch.setattr(
        "app.services.weekly_forecast_service.prepare_weekly_forecast_features",
        lambda **kwargs: {"scopes": [("Roads", None)]},
    )
    monkeypatch.setattr(
        "app.services.weekly_forecast_service.run_threshold_alert_evaluation",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("alert boom")),
    )

    result = service.execute_run("run-1")

    assert result.generated_forecast_version_id == "weekly-version-1"
    assert finalized == [{
        "run_id": "run-1",
        "generated_forecast_version_id": "weekly-version-1",
        "geography_scope": "citywide",
        "summary": "weekly forecast generated and activated",
    }]
    assert warnings == ["threshold alert evaluation failed for weekly_forecast_version_id=weekly-version-1: alert boom"]


@pytest.mark.unit
def test_forecast_service_triggers_surge_evaluation_after_activation(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = SimpleNamespace(
        source_name="edmonton_311",
        forecast_product_name="daily_1_day_demand",
        forecast_training_lookback_days=56,
    )
    horizon_start = datetime(2026, 3, 22, 1, tzinfo=timezone.utc)
    horizon_end = datetime(2026, 3, 23, 1, tzinfo=timezone.utc)
    run = SimpleNamespace(
        forecast_run_id="run-1",
        status="running",
        trigger_type="scheduled",
        source_cleaned_dataset_version_id="dataset-1",
        requested_horizon_start=horizon_start,
        requested_horizon_end=horizon_end,
    )
    finalized: list[dict[str, object]] = []
    threshold_calls: list[dict[str, object]] = []
    surge_calls: list[dict[str, object]] = []
    run_repo = SimpleNamespace(
        get_run=lambda _run_id: run,
        finalize_generated=lambda run_id, **kwargs: finalized.append({"run_id": run_id, **kwargs}) or SimpleNamespace(status="completed", **kwargs),
        finalize_failed=lambda *args, **kwargs: None,
        finalize_reused=lambda *args, **kwargs: None,
    )
    service = ForecastService(
        cleaned_dataset_repository=SimpleNamespace(
            list_current_cleaned_records=lambda *args, **kwargs: [{"requested_at": "2026-03-20T10:00:00Z", "category": "Roads"}],
        ),
        forecast_run_repository=run_repo,
        forecast_repository=SimpleNamespace(
            session="session",
            find_current_for_horizon=lambda **kwargs: None,
        ),
        geomet_client=SimpleNamespace(fetch_hourly_conditions=lambda start, end: []),
        nager_date_client=SimpleNamespace(fetch_holidays=lambda year: []),
        settings=settings,
        forecast_model_repository=SimpleNamespace(find_current_model=lambda *_args, **_kwargs: None),
        logger=SimpleNamespace(info=lambda *args, **kwargs: None, warning=lambda *args, **kwargs: None),
    )
    service.pipeline = SimpleNamespace(run=lambda prepared: {"baseline_method": "baseline", "buckets": [{"x": 1}]})
    service.bucket_service = SimpleNamespace(build_buckets=lambda generated: ([{"bucket": 1}], "category_only"))
    service.activation_service = SimpleNamespace(store_and_activate=lambda **kwargs: "forecast-version-1")
    monkeypatch.setattr(
        "app.services.forecast_service.prepare_forecast_features",
        lambda **kwargs: {"rows": [1]},
    )
    monkeypatch.setattr(
        "app.services.forecast_service.run_threshold_alert_evaluation",
        lambda session, **kwargs: threshold_calls.append({"session": session, **kwargs}),
    )
    monkeypatch.setattr(
        "app.services.forecast_service.run_surge_alert_evaluation_for_forecast",
        lambda session, **kwargs: surge_calls.append({"session": session, **kwargs}),
    )

    result = service.execute_run("run-1")

    assert result.forecast_version_id == "forecast-version-1"
    assert threshold_calls == [{
        "session": "session",
        "forecast_reference_id": "forecast-version-1",
        "forecast_product": "daily",
        "trigger_source": "forecast_refresh",
    }]
    assert surge_calls == [{
        "session": "session",
        "forecast_version_id": "forecast-version-1",
        "trigger_source": "ingestion_completion",
    }]
    assert finalized == [{
        "run_id": "run-1",
        "forecast_version_id": "forecast-version-1",
        "geography_scope": "category_only",
        "summary": "forecast generated and activated",
    }]


@pytest.mark.unit
def test_surge_scope_service_accepts_successful_ingestion_runs() -> None:
    evaluation_hour = datetime(2026, 4, 1, 10, tzinfo=timezone.utc)
    service = SurgeScopeService(
        run_repository=SimpleNamespace(
            get_run=lambda _run_id: SimpleNamespace(
                run_id="ingestion-1",
                status="success",
                dataset_version_id="dataset-1",
            )
        ),
        dataset_repository=SimpleNamespace(
            list_dataset_records=lambda _dataset_version_id: [
                {
                    "requested_at": evaluation_hour.isoformat().replace("+00:00", "Z"),
                    "category": "Roads",
                }
            ]
        ),
        forecast_repository=SimpleNamespace(
            get_current_marker=lambda _product_name: SimpleNamespace(forecast_version_id="forecast-1"),
            get_forecast_version=lambda _forecast_version_id: SimpleNamespace(
                forecast_run_id="forecast-run-1",
                forecast_version_id="forecast-1",
            ),
            list_buckets=lambda _forecast_version_id: [
                SimpleNamespace(
                    service_category="Roads",
                    bucket_start=evaluation_hour,
                    bucket_end=evaluation_hour.replace(hour=11),
                    quantile_p50=2,
                )
            ],
        ),
    )

    scopes = service.list_scopes(ingestion_run_id="ingestion-1")

    assert len(scopes) == 1
    assert scopes[0].service_category == "Roads"
    assert scopes[0].actual_demand_value == 1.0
    assert scopes[0].forecast_p50_value == 2.0


@pytest.mark.unit
def test_surge_pipeline_finalizes_run_when_scope_resolution_fails() -> None:
    finalized: list[dict[str, object]] = []
    pipeline = SurgeAlertEvaluationPipeline(
        scope_service=SimpleNamespace(list_scopes=lambda **kwargs: (_ for _ in ()).throw(ValueError("scope boom"))),
        configuration_repository=SimpleNamespace(find_active_configuration=lambda **kwargs: None),
        evaluation_repository=SimpleNamespace(
            create_run=lambda **kwargs: SimpleNamespace(surge_evaluation_run_id="surge-run-1"),
            finalize_run=lambda run_id, **kwargs: finalized.append({"run_id": run_id, **kwargs}) or SimpleNamespace(
                surge_evaluation_run_id=run_id,
                status=kwargs["status"],
                failure_summary=kwargs["failure_summary"],
            ),
        ),
        state_repository=SimpleNamespace(get_state=lambda **kwargs: None, reconcile_state=lambda **kwargs: None),
        event_repository=SimpleNamespace(create_event=lambda **kwargs: None, add_attempt=lambda **kwargs: None),
        detection_service=SimpleNamespace(compute_metrics=lambda **kwargs: None),
        confirmation_service=SimpleNamespace(evaluate=lambda **kwargs: None),
        state_service=SimpleNamespace(transition=lambda **kwargs: None),
        delivery_service=SimpleNamespace(deliver=lambda **kwargs: None),
        logger=SimpleNamespace(info=lambda *args, **kwargs: None, warning=lambda *args, **kwargs: None),
    )

    completed = pipeline.run(ingestion_run_id="ingestion-1", trigger_source="ingestion_completion")

    assert completed.status == "completed_with_failures"
    assert completed.failure_summary == "scope boom"
    assert finalized == [{
        "run_id": "surge-run-1",
        "status": "completed_with_failures",
        "evaluated_scope_count": 0,
        "candidate_count": 0,
        "confirmed_count": 0,
        "notification_created_count": 0,
        "failure_summary": "scope boom",
    }]
