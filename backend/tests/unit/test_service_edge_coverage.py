from __future__ import annotations

from datetime import date, datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.services.alert_review_service import AlertReviewService
from app.services.forecast_scope_service import ForecastScopeService
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
