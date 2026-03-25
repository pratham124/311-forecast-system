from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.forecast_repository import ForecastRepository
from app.repositories.forecast_run_repository import ForecastRunRepository
from app.repositories.visualization_repository import VisualizationRepository
from app.services.forecast_visualization_service import ForecastVisualizationService
from app.services.forecast_visualization_sources import ForecastVisualizationSourceService
from app.services.historical_demand_service import HistoricalDemandService
from app.services.visualization_snapshot_service import VisualizationSnapshotService
from app.core.config import get_settings


def _build_service(session):
    visualization_repository = VisualizationRepository(session)
    settings = get_settings()
    return ForecastVisualizationService(
        cleaned_dataset_repository=CleanedDatasetRepository(session),
        forecast_repository=ForecastRepository(session),
        weekly_forecast_repository=__import__("app.repositories.weekly_forecast_repository", fromlist=["WeeklyForecastRepository"]).WeeklyForecastRepository(session),
        visualization_repository=visualization_repository,
        historical_demand_service=HistoricalDemandService(CleanedDatasetRepository(session), settings.source_name),
        source_service=ForecastVisualizationSourceService(),
        snapshot_service=VisualizationSnapshotService(visualization_repository, settings.visualization_fallback_age_hours),
        settings=settings,
        logger=__import__('logging').getLogger('test.visualization'),
    )


def _seed(session, include_history: bool = True):
    dataset_repository = DatasetRepository(session)
    records = []
    if include_history:
        records = [
            {"service_request_id": f"history-{idx}", "requested_at": f"2026-03-1{idx}T0{idx}:00:00Z", "category": "Roads"}
            for idx in range(1, 5)
        ]
    version = dataset_repository.create_dataset_version(
        source_name="edmonton_311",
        run_id="run-1",
        candidate_id=None,
        record_count=max(len(records), 1),
        records=records or [{"service_request_id": "seed-1", "requested_at": "2026-03-01T00:00:00Z", "category": "Transit"}],
    )
    dataset_repository.activate_dataset("edmonton_311", version.dataset_version_id, "run-1")
    if include_history:
        CleanedDatasetRepository(session).upsert_current_cleaned_records(
            source_name="edmonton_311",
            ingestion_run_id="run-1",
            source_dataset_version_id=version.dataset_version_id,
            approved_dataset_version_id=version.dataset_version_id,
            approved_by_validation_run_id="validation-1",
            cleaned_records=records,
        )
    run = ForecastRunRepository(session).create_run(
        trigger_type="scheduled",
        source_cleaned_dataset_version_id=version.dataset_version_id,
        requested_horizon_start=datetime(2026, 3, 20, 0, tzinfo=timezone.utc),
        requested_horizon_end=datetime(2026, 3, 21, 0, tzinfo=timezone.utc),
    )
    forecast_repository = ForecastRepository(session)
    forecast_version = forecast_repository.create_forecast_version(
        forecast_run_id=run.forecast_run_id,
        source_cleaned_dataset_version_id=version.dataset_version_id,
        horizon_start=datetime(2026, 3, 20, 0, tzinfo=timezone.utc),
        horizon_end=datetime(2026, 3, 21, 0, tzinfo=timezone.utc),
        geography_scope="citywide",
        baseline_method="seasonal_naive",
        summary="Daily forecast",
    )
    forecast_repository.store_buckets(
        forecast_version.forecast_version_id,
        [
            {
                "bucket_start": datetime(2026, 3, 20, hour, tzinfo=timezone.utc),
                "bucket_end": datetime(2026, 3, 20, hour, tzinfo=timezone.utc) + timedelta(hours=1),
                "service_category": "Roads",
                "geography_key": None,
                "point_forecast": 10 + hour,
                "quantile_p10": 8 + hour,
                "quantile_p50": 10 + hour,
                "quantile_p90": 12 + hour,
                "baseline_value": 9 + hour,
            }
            for hour in range(3)
        ],
    )
    forecast_repository.mark_version_stored(forecast_version.forecast_version_id, bucket_count=3)
    forecast_repository.activate_forecast(
        forecast_product_name="daily_1_day_demand",
        forecast_version_id=forecast_version.forecast_version_id,
        source_cleaned_dataset_version_id=version.dataset_version_id,
        horizon_start=datetime(2026, 3, 20, 0, tzinfo=timezone.utc),
        horizon_end=datetime(2026, 3, 21, 0, tzinfo=timezone.utc),
        updated_by_run_id=run.forecast_run_id,
        geography_scope="citywide",
    )
    session.commit()


def test_visualization_success_records_terminal_outcome_and_snapshot(session):
    _seed(session, include_history=True)
    service = _build_service(session)
    response = service.get_current_visualization(forecast_product="daily_1_day", service_category="Roads")
    session.commit()
    assert response.view_status == "success"
    repository = VisualizationRepository(session)
    load = repository.require_load_record(response.visualization_load_id)
    assert load.status == "success"
    snapshot = repository.get_latest_eligible_snapshot(
        forecast_product_name="daily_1_day",
        service_category_filter="Roads",
        now=datetime.utcnow().replace(tzinfo=timezone.utc),
    )
    assert snapshot is not None


def test_visualization_degrades_when_history_missing(session):
    _seed(session, include_history=False)
    service = _build_service(session)
    response = service.get_current_visualization(forecast_product="daily_1_day", service_category="Roads")
    session.commit()
    assert response.view_status == "degraded"
    assert response.degradation_type == "history_missing"
    load = VisualizationRepository(session).require_load_record(response.visualization_load_id)
    assert load.status == "degraded"



def test_visualization_aggregates_selected_categories_by_timestamp(session):
    dataset_repository = DatasetRepository(session)
    records = [
        {"service_request_id": "roads-1", "requested_at": "2026-03-19T01:00:00Z", "category": "Roads"},
        {"service_request_id": "waste-1", "requested_at": "2026-03-19T01:00:00Z", "category": "Waste"},
    ]
    version = dataset_repository.create_dataset_version(
        source_name="edmonton_311",
        run_id="run-agg",
        candidate_id=None,
        record_count=len(records),
        records=records,
    )
    dataset_repository.activate_dataset("edmonton_311", version.dataset_version_id, "run-agg")
    CleanedDatasetRepository(session).upsert_current_cleaned_records(
        source_name="edmonton_311",
        ingestion_run_id="run-agg",
        source_dataset_version_id=version.dataset_version_id,
        approved_dataset_version_id=version.dataset_version_id,
        approved_by_validation_run_id="validation-agg",
        cleaned_records=records,
    )
    run = ForecastRunRepository(session).create_run(
        trigger_type="scheduled",
        source_cleaned_dataset_version_id=version.dataset_version_id,
        requested_horizon_start=datetime(2026, 3, 20, 0, tzinfo=timezone.utc),
        requested_horizon_end=datetime(2026, 3, 21, 0, tzinfo=timezone.utc),
    )
    forecast_repository = ForecastRepository(session)
    forecast_version = forecast_repository.create_forecast_version(
        forecast_run_id=run.forecast_run_id,
        source_cleaned_dataset_version_id=version.dataset_version_id,
        horizon_start=datetime(2026, 3, 20, 0, tzinfo=timezone.utc),
        horizon_end=datetime(2026, 3, 21, 0, tzinfo=timezone.utc),
        geography_scope="citywide",
        baseline_method="seasonal_naive",
        summary="Daily forecast",
    )
    forecast_repository.store_buckets(
        forecast_version.forecast_version_id,
        [
            {
                "bucket_start": datetime(2026, 3, 20, 0, tzinfo=timezone.utc),
                "bucket_end": datetime(2026, 3, 20, 1, tzinfo=timezone.utc),
                "service_category": "Roads",
                "geography_key": None,
                "point_forecast": 10,
                "quantile_p10": 8,
                "quantile_p50": 10,
                "quantile_p90": 12,
                "baseline_value": 9,
            },
            {
                "bucket_start": datetime(2026, 3, 20, 0, tzinfo=timezone.utc),
                "bucket_end": datetime(2026, 3, 20, 1, tzinfo=timezone.utc),
                "service_category": "Waste",
                "geography_key": None,
                "point_forecast": 7,
                "quantile_p10": 5,
                "quantile_p50": 7,
                "quantile_p90": 9,
                "baseline_value": 6,
            },
        ],
    )
    forecast_repository.mark_version_stored(forecast_version.forecast_version_id, bucket_count=2)
    forecast_repository.activate_forecast(
        forecast_product_name="daily_1_day_demand",
        forecast_version_id=forecast_version.forecast_version_id,
        source_cleaned_dataset_version_id=version.dataset_version_id,
        horizon_start=datetime(2026, 3, 20, 0, tzinfo=timezone.utc),
        horizon_end=datetime(2026, 3, 21, 0, tzinfo=timezone.utc),
        updated_by_run_id=run.forecast_run_id,
        geography_scope="citywide",
    )
    session.commit()

    service = _build_service(session)
    response = service.get_current_visualization(forecast_product="daily_1_day", service_categories=["Roads", "Waste"])
    session.commit()

    assert len(response.forecast_series) == 1
    assert response.forecast_series[0].point_forecast == 17
    assert response.uncertainty_bands is not None
    assert response.uncertainty_bands.points[0].p10 == 13
    assert response.uncertainty_bands.points[0].p50 == 17
    assert response.uncertainty_bands.points[0].p90 == 21
