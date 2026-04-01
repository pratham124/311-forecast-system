from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest

from app.models import ForecastRun, WeeklyForecastRun
from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.demand_comparison_repository import DemandComparisonRepository
from app.repositories.forecast_repository import ForecastRepository
from app.repositories.weekly_forecast_repository import WeeklyForecastRepository
from app.services.demand_comparison_context_service import DemandComparisonContextService
from app.services.demand_comparison_render_service import DemandComparisonRenderService
from app.services.demand_comparison_result_builder import DemandComparisonResultBuilder
from app.services.demand_comparison_service import DemandComparisonService
from app.services.demand_comparison_source_resolution import DemandComparisonSourceResolver
from app.services.demand_comparison_source_resolution import AlignmentResolutionError
from app.services.demand_comparison_warning_service import DemandComparisonWarningService
from app.repositories.demand_lineage_repository import DemandLineageRepository
from app.schemas.demand_comparison_api import DemandComparisonQueryRequest, DemandComparisonRenderEvent


def seed_approved_dataset(session):
    dataset_repository = DatasetRepository(session)
    version = dataset_repository.create_dataset_version(
        source_name="edmonton_311",
        run_id="clean-run",
        candidate_id=None,
        record_count=3,
        records=[
            {"service_request_id": "hist-1", "requested_at": "2026-03-01T00:15:00Z", "category": "Roads", "ward": "Ward 1"},
            {"service_request_id": "hist-2", "requested_at": "2026-03-01T01:15:00Z", "category": "Roads", "ward": "Ward 1"},
            {"service_request_id": "hist-3", "requested_at": "2026-03-01T02:15:00Z", "category": "Waste", "ward": "Ward 1"},
        ],
        validation_status="approved",
        dataset_kind="cleaned",
    )
    dataset_repository.activate_dataset("edmonton_311", version.dataset_version_id, "clean-run")
    session.commit()
    return version


def seed_daily_forecast(session, *, with_geography: bool = True, include_waste: bool = True):
    forecast_repository = ForecastRepository(session)
    run = ForecastRun(
        trigger_type="manual",
        source_cleaned_dataset_version_id="dataset-source",
        requested_horizon_start=datetime(2026, 3, 1, tzinfo=timezone.utc),
        requested_horizon_end=datetime(2026, 3, 3, tzinfo=timezone.utc),
        geography_scope="ward",
        status="success",
    )
    session.add(run)
    session.flush()
    version = forecast_repository.create_forecast_version(
        forecast_run_id=run.forecast_run_id,
        source_cleaned_dataset_version_id="dataset-source",
        horizon_start=datetime(2026, 3, 1, tzinfo=timezone.utc),
        horizon_end=datetime(2026, 3, 3, tzinfo=timezone.utc),
        geography_scope="ward",
        baseline_method="naive",
        summary="daily forecast",
    )
    buckets = [
        {
            "bucket_start": datetime(2026, 3, 1, 0, tzinfo=timezone.utc),
            "bucket_end": datetime(2026, 3, 1, 1, tzinfo=timezone.utc),
            "service_category": "Roads",
            "geography_key": "Ward 1" if with_geography else None,
            "point_forecast": 4.0,
            "quantile_p10": 2.0,
            "quantile_p50": 4.0,
            "quantile_p90": 6.0,
            "baseline_value": 3.0,
        },
    ]
    if include_waste:
        buckets.append(
            {
                "bucket_start": datetime(2026, 3, 1, 1, tzinfo=timezone.utc),
                "bucket_end": datetime(2026, 3, 1, 2, tzinfo=timezone.utc),
                "service_category": "Waste",
                "geography_key": "Ward 1" if with_geography else None,
                "point_forecast": 6.0,
                "quantile_p10": 3.0,
                "quantile_p50": 6.0,
                "quantile_p90": 9.0,
                "baseline_value": 5.0,
            }
        )
    forecast_repository.store_buckets(version.forecast_version_id, buckets)
    forecast_repository.mark_version_stored(version.forecast_version_id, len(buckets))
    forecast_repository.activate_forecast(
        forecast_product_name="daily_1_day_demand",
        forecast_version_id=version.forecast_version_id,
        source_cleaned_dataset_version_id="dataset-source",
        horizon_start=version.horizon_start,
        horizon_end=version.horizon_end,
        updated_by_run_id=run.forecast_run_id,
        geography_scope="ward",
    )
    session.commit()
    return version


def seed_weekly_forecast(session):
    weekly_repository = WeeklyForecastRepository(session)
    run = WeeklyForecastRun(
        trigger_type="manual",
        source_cleaned_dataset_version_id="dataset-source",
        week_start_local=datetime(2026, 3, 1, tzinfo=timezone.utc),
        week_end_local=datetime(2026, 3, 8, tzinfo=timezone.utc),
        geography_scope="ward",
        status="success",
    )
    session.add(run)
    session.flush()
    version = weekly_repository.create_forecast_version(
        weekly_forecast_run_id=run.weekly_forecast_run_id,
        source_cleaned_dataset_version_id="dataset-source",
        week_start_local=datetime(2026, 3, 1, tzinfo=timezone.utc),
        week_end_local=datetime(2026, 3, 8, tzinfo=timezone.utc),
        geography_scope="ward",
        baseline_method="naive",
        summary="weekly forecast",
    )
    weekly_repository.store_buckets(
        version.weekly_forecast_version_id,
        [
            {
                "forecast_date_local": date(2026, 3, 2),
                "service_category": "Roads",
                "geography_key": "Ward 1",
                "point_forecast": 8.0,
                "quantile_p10": 5.0,
                "quantile_p50": 8.0,
                "quantile_p90": 10.0,
                "baseline_value": 7.0,
            }
        ],
    )
    weekly_repository.mark_version_stored(version.weekly_forecast_version_id)
    weekly_repository.activate_forecast(
        forecast_product_name="weekly_7_day_demand",
        weekly_forecast_version_id=version.weekly_forecast_version_id,
        source_cleaned_dataset_version_id="dataset-source",
        week_start_local=version.week_start_local,
        week_end_local=version.week_end_local,
        updated_by_run_id=run.weekly_forecast_run_id,
        geography_scope="ward",
    )
    session.commit()
    return version


def build_service(session) -> DemandComparisonService:
    cleaned_repository = CleanedDatasetRepository(session)
    forecast_repository = ForecastRepository(session)
    weekly_repository = WeeklyForecastRepository(session)
    return DemandComparisonService(
        comparison_repository=DemandComparisonRepository(session),
        cleaned_dataset_repository=cleaned_repository,
        forecast_repository=forecast_repository,
        weekly_forecast_repository=weekly_repository,
        context_service=DemandComparisonContextService(cleaned_repository, "edmonton_311"),
        warning_service=DemandComparisonWarningService(),
        source_resolver=DemandComparisonSourceResolver(
            demand_lineage_repository=DemandLineageRepository(
                cleaned_dataset_repository=cleaned_repository,
                forecast_repository=forecast_repository,
                weekly_forecast_repository=weekly_repository,
            ),
            source_name="edmonton_311",
            daily_forecast_product_name="daily_1_day_demand",
            weekly_forecast_product_name="weekly_7_day_demand",
        ),
        result_builder=DemandComparisonResultBuilder(),
    )


@pytest.mark.integration
def test_demand_comparison_service_success_and_render_flow(session) -> None:
    seed_approved_dataset(session)
    seed_daily_forecast(session)
    service = build_service(session)

    response = service.execute_query(
        DemandComparisonQueryRequest.model_validate(
            {
                "serviceCategories": ["Roads", "Waste"],
                "geographyLevel": "ward",
                "geographyValues": ["Ward 1"],
                "timeRangeStart": "2026-03-01T00:00:00Z",
                "timeRangeEnd": "2026-03-02T00:00:00Z",
            }
        ),
        {"sub": "planner-1", "roles": ["CityPlanner"]},
    )
    session.commit()

    assert response.outcome_status == "success"
    render_response = DemandComparisonRenderService(DemandComparisonRepository(session)).record_event(
        comparison_request_id=response.comparison_request_id,
        payload=DemandComparisonRenderEvent.model_validate({"renderStatus": "rendered"}),
        claims={"sub": "planner-1", "roles": ["CityPlanner"]},
    )
    session.commit()
    assert render_response.recorded_outcome_status == "rendered"


@pytest.mark.integration
def test_demand_comparison_service_warning_partial_forecast_and_alignment_failure(session) -> None:
    seed_approved_dataset(session)
    seed_daily_forecast(session, include_waste=False)
    service = build_service(session)

    warning = service.execute_query(
        DemandComparisonQueryRequest.model_validate(
            {
                "serviceCategories": ["Roads", "Waste"],
                "timeRangeStart": "2026-01-01T00:00:00Z",
                "timeRangeEnd": "2027-03-01T00:00:00Z",
            }
        ),
        {"sub": "planner-1", "roles": ["CityPlanner"]},
    )
    assert warning.outcome_status == "warning_required"

    partial = service.execute_query(
        DemandComparisonQueryRequest.model_validate(
            {
                "serviceCategories": ["Roads", "Waste"],
                "geographyLevel": "ward",
                "geographyValues": ["Ward 1"],
                "timeRangeStart": "2026-03-01T00:00:00Z",
                "timeRangeEnd": "2026-03-02T00:00:00Z",
                "proceedAfterWarning": True,
            }
        ),
        {"sub": "planner-1", "roles": ["CityPlanner"]},
    )
    session.commit()
    assert partial.outcome_status == "partial_forecast_missing"
    assert partial.missing_combinations

    service.source_resolver.ensure_alignment_supported = lambda **_kwargs: (_ for _ in ()).throw(AlignmentResolutionError("alignment broken"))
    alignment_response = service.execute_query(
        DemandComparisonQueryRequest.model_validate(
            {
                "serviceCategories": ["Roads"],
                "geographyLevel": "ward",
                "geographyValues": ["Ward 1"],
                "timeRangeStart": "2026-03-01T00:00:00Z",
                "timeRangeEnd": "2026-03-02T00:00:00Z",
            }
        ),
        {"sub": "planner-1", "roles": ["CityPlanner"]},
    )
    assert alignment_response.outcome_status == "alignment_failed"


@pytest.mark.integration
def test_demand_comparison_service_forecast_only_historical_only_weekly_and_failure_paths(session, monkeypatch) -> None:
    seed_approved_dataset(session)
    seed_weekly_forecast(session)
    service = build_service(session)

    forecast_only = service.execute_query(
        DemandComparisonQueryRequest.model_validate(
                {
                    "serviceCategories": ["Roads"],
                    "geographyLevel": "ward",
                    "geographyValues": ["Ward 1"],
                    "timeRangeStart": "2026-03-02T00:00:00Z",
                    "timeRangeEnd": "2026-03-05T00:00:00Z",
                }
            ),
        {"sub": "planner-1", "roles": ["CityPlanner"]},
    )
    assert forecast_only.outcome_status == "forecast_only"
    assert forecast_only.forecast_product == "weekly_7_day"

    monkeypatch.setattr(service.source_resolver, "resolve", lambda **_kwargs: ("dataset-source", None))
    historical_only = service.execute_query(
        DemandComparisonQueryRequest.model_validate(
            {
                "serviceCategories": ["Roads"],
                "geographyLevel": "ward",
                "geographyValues": ["Ward 1"],
                "timeRangeStart": "2026-03-01T00:00:00Z",
                "timeRangeEnd": "2026-03-02T00:00:00Z",
            }
        ),
        {"sub": "planner-1", "roles": ["CityPlanner"]},
    )
    assert historical_only.outcome_status == "historical_only"

    monkeypatch.setattr(service, "_load_historical_records", lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("history down")))
    history_failed = service.execute_query(
        DemandComparisonQueryRequest.model_validate(
            {
                "serviceCategories": ["Roads"],
                "timeRangeStart": "2026-03-01T00:00:00Z",
                "timeRangeEnd": "2026-03-02T00:00:00Z",
            }
        ),
        {"sub": "planner-1", "roles": ["CityPlanner"]},
    )
    assert history_failed.outcome_status == "historical_retrieval_failed"

    service = build_service(session)
    seed_daily_forecast(session)
    monkeypatch.setattr(service, "_load_forecast_records", lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("forecast down")))
    forecast_failed = service.execute_query(
        DemandComparisonQueryRequest.model_validate(
            {
                "serviceCategories": ["Roads"],
                "timeRangeStart": "2026-03-01T00:00:00Z",
                "timeRangeEnd": "2026-03-02T00:00:00Z",
            }
        ),
        {"sub": "planner-1", "roles": ["CityPlanner"]},
    )
    assert forecast_failed.outcome_status == "forecast_retrieval_failed"

    request_id = forecast_failed.comparison_request_id
    with pytest.raises(Exception):
        DemandComparisonRenderService(DemandComparisonRepository(session)).record_event(
            comparison_request_id=request_id,
            payload=DemandComparisonRenderEvent.model_validate({"renderStatus": "rendered"}),
            claims={"sub": "other-user", "roles": ["CityPlanner"]},
        )

    failed_render = DemandComparisonRenderService(DemandComparisonRepository(session)).record_event(
        comparison_request_id=request_id,
        payload=DemandComparisonRenderEvent.model_validate({"renderStatus": "render_failed", "failureReason": "chart crashed"}),
        claims={"sub": "planner-1", "roles": ["CityPlanner"]},
    )
    assert failed_render.recorded_outcome_status == "render_failed"
