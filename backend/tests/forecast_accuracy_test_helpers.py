from __future__ import annotations

from datetime import datetime, timezone

from app.models import ForecastRun
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.forecast_repository import ForecastRepository


def seed_forecast_accuracy_data(
    session,
    *,
    actual_records: list[dict[str, object]] | None = None,
    forecast_buckets: list[dict[str, object]] | None = None,
) -> dict[str, str]:
    dataset_repository = DatasetRepository(session)
    actual_records = actual_records or [
        {"service_request_id": "actual-1", "requested_at": "2026-03-01T00:10:00Z", "category": "Roads"},
        {"service_request_id": "actual-2", "requested_at": "2026-03-01T01:10:00Z", "category": "Roads"},
    ]
    version = dataset_repository.create_dataset_version(
        source_name="edmonton_311",
        run_id="clean-run",
        candidate_id=None,
        record_count=len(actual_records),
        records=actual_records,
        validation_status="approved",
        dataset_kind="cleaned",
    )
    dataset_repository.activate_dataset("edmonton_311", version.dataset_version_id, "clean-run")

    forecast_repository = ForecastRepository(session)
    run = ForecastRun(
        trigger_type="manual",
        source_cleaned_dataset_version_id=version.dataset_version_id,
        requested_horizon_start=datetime(2026, 3, 1, tzinfo=timezone.utc),
        requested_horizon_end=datetime(2026, 3, 2, tzinfo=timezone.utc),
        geography_scope="category_only",
        status="success",
    )
    session.add(run)
    session.flush()
    forecast_version = forecast_repository.create_forecast_version(
        forecast_run_id=run.forecast_run_id,
        source_cleaned_dataset_version_id=version.dataset_version_id,
        horizon_start=datetime(2026, 3, 1, tzinfo=timezone.utc),
        horizon_end=datetime(2026, 3, 2, tzinfo=timezone.utc),
        geography_scope="category_only",
        baseline_method="naive",
        summary="daily forecast",
    )
    forecast_repository.store_buckets(
        forecast_version.forecast_version_id,
        forecast_buckets
        or [
            {
                "bucket_start": datetime(2026, 3, 1, 0, tzinfo=timezone.utc),
                "bucket_end": datetime(2026, 3, 1, 1, tzinfo=timezone.utc),
                "service_category": "Roads",
                "geography_key": None,
                "point_forecast": 4.0,
                "quantile_p10": 2.0,
                "quantile_p50": 4.0,
                "quantile_p90": 6.0,
                "baseline_value": 3.0,
            },
            {
                "bucket_start": datetime(2026, 3, 1, 1, tzinfo=timezone.utc),
                "bucket_end": datetime(2026, 3, 1, 2, tzinfo=timezone.utc),
                "service_category": "Roads",
                "geography_key": None,
                "point_forecast": 2.0,
                "quantile_p10": 1.0,
                "quantile_p50": 2.0,
                "quantile_p90": 3.0,
                "baseline_value": 1.5,
            },
        ],
    )
    forecast_repository.mark_version_stored(forecast_version.forecast_version_id, 2)
    session.commit()
    return {
        "dataset_version_id": version.dataset_version_id,
        "forecast_version_id": forecast_version.forecast_version_id,
    }
