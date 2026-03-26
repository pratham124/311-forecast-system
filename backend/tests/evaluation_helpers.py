from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.forecast_repository import ForecastRepository
from app.repositories.forecast_run_repository import ForecastRunRepository
from app.repositories.weekly_forecast_repository import WeeklyForecastRepository
from app.repositories.weekly_forecast_run_repository import WeeklyForecastRunRepository


def seed_daily_evaluation_inputs(
    session,
    *,
    include_zero_actual: bool = False,
    with_history: bool = True,
    with_evaluation_actuals: bool = True,
    extra_forecast_categories: list[str] | None = None,
    horizon_start: datetime | None = None,
    seed_tag: str = "default",
) -> tuple[str, str]:
    horizon_start = horizon_start or datetime(2026, 3, 20, 0, tzinfo=timezone.utc)
    history_start = horizon_start - timedelta(days=7)
    horizon_end = horizon_start + timedelta(hours=3)

    extra_forecast_categories = extra_forecast_categories or []
    records: list[dict[str, object]] = []
    if with_history:
        for day_offset in range(7):
            for hour in range(3):
                for category in ["Roads", "Waste"]:
                    records.append(
                        {
                            "service_request_id": f"{seed_tag}-hist-{day_offset}-{hour}-{category}",
                            "requested_at": (history_start + timedelta(days=day_offset, hours=hour)).isoformat().replace("+00:00", "Z"),
                            "category": category,
                        }
                    )
    if with_evaluation_actuals:
        for hour in range(3):
            records.append(
                {
                    "service_request_id": f"{seed_tag}-eval-roads-{hour}",
                    "requested_at": (horizon_start + timedelta(hours=hour)).isoformat().replace("+00:00", "Z"),
                    "category": "Roads",
                }
            )
            if not (include_zero_actual and hour == 1):
                records.append(
                    {
                        "service_request_id": f"{seed_tag}-eval-waste-{hour}",
                        "requested_at": (horizon_start + timedelta(hours=hour)).isoformat().replace("+00:00", "Z"),
                        "category": "Waste",
                    }
                )

    dataset_repository = DatasetRepository(session)
    cleaned_repository = CleanedDatasetRepository(session)
    validation_run_id = f"{seed_tag}-validation-run"
    approved_by_validation_run_id = f"{seed_tag}-validation-1"
    version = dataset_repository.create_dataset_version(
        source_name="edmonton_311",
        run_id=validation_run_id,
        candidate_id=None,
        record_count=len(records),
        records=records,
        validation_status="approved",
        dataset_kind="cleaned",
        approved_by_validation_run_id=approved_by_validation_run_id,
    )
    cleaned_repository.upsert_current_cleaned_records(
        source_name="edmonton_311",
        ingestion_run_id=validation_run_id,
        source_dataset_version_id=version.dataset_version_id,
        approved_dataset_version_id=version.dataset_version_id,
        approved_by_validation_run_id=approved_by_validation_run_id,
        cleaned_records=records,
    )
    dataset_repository.activate_dataset("edmonton_311", version.dataset_version_id, approved_by_validation_run_id)

    run = ForecastRunRepository(session).create_run(
        trigger_type="scheduled",
        source_cleaned_dataset_version_id=version.dataset_version_id,
        requested_horizon_start=horizon_start,
        requested_horizon_end=horizon_end,
    )
    forecast_repository = ForecastRepository(session)
    forecast_version = forecast_repository.create_forecast_version(
        forecast_run_id=run.forecast_run_id,
        source_cleaned_dataset_version_id=version.dataset_version_id,
        horizon_start=horizon_start,
        horizon_end=horizon_end,
        geography_scope="citywide",
        baseline_method="historical_hourly_mean",
        summary="Daily forecast",
    )
    forecast_repository.store_buckets(
        forecast_version.forecast_version_id,
        [
            {
                "bucket_start": horizon_start + timedelta(hours=hour),
                "bucket_end": horizon_start + timedelta(hours=hour + 1),
                "service_category": category,
                "geography_key": None,
                "point_forecast": 2 + hour,
                "quantile_p10": 1 + hour,
                "quantile_p50": 2 + hour,
                "quantile_p90": 3 + hour,
                "baseline_value": 1 + hour,
            }
            for category in ["Roads", "Waste", *extra_forecast_categories]
            for hour in range(3)
        ],
    )
    forecast_repository.mark_version_stored(
        forecast_version.forecast_version_id,
        bucket_count=3 * len(["Roads", "Waste", *extra_forecast_categories]),
    )
    forecast_repository.activate_forecast(
        forecast_product_name="daily_1_day_demand",
        forecast_version_id=forecast_version.forecast_version_id,
        source_cleaned_dataset_version_id=version.dataset_version_id,
        horizon_start=horizon_start,
        horizon_end=horizon_end,
        updated_by_run_id=run.forecast_run_id,
        geography_scope="citywide",
    )
    session.commit()
    return version.dataset_version_id, forecast_version.forecast_version_id


def seed_weekly_evaluation_inputs(
    session,
    *,
    with_history: bool = True,
    with_evaluation_actuals: bool = True,
    week_start: datetime | None = None,
    seed_tag: str = "default",
) -> tuple[str, str]:
    week_start = week_start or datetime(2026, 3, 23, 0, tzinfo=timezone.utc)
    week_end = week_start + timedelta(days=3)
    history_start = week_start - timedelta(days=14)

    records: list[dict[str, object]] = []
    if with_history:
        for day_offset in range(10):
            for category in ["Roads", "Waste"]:
                records.append(
                    {
                        "service_request_id": f"{seed_tag}-weekly-hist-{day_offset}-{category}",
                        "requested_at": (history_start + timedelta(days=day_offset, hours=9)).isoformat().replace("+00:00", "Z"),
                        "category": category,
                    }
                )
    if with_evaluation_actuals:
        for day_offset in range(3):
            for category in ["Roads", "Waste"]:
                records.append(
                    {
                        "service_request_id": f"{seed_tag}-weekly-eval-{day_offset}-{category}",
                        "requested_at": (week_start + timedelta(days=day_offset, hours=8)).isoformat().replace("+00:00", "Z"),
                        "category": category,
                    }
                )

    dataset_repository = DatasetRepository(session)
    cleaned_repository = CleanedDatasetRepository(session)
    validation_run_id = f"{seed_tag}-validation-run"
    approved_by_validation_run_id = f"{seed_tag}-validation-1"
    version = dataset_repository.create_dataset_version(
        source_name="edmonton_311",
        run_id=validation_run_id,
        candidate_id=None,
        record_count=len(records),
        records=records,
        validation_status="approved",
        dataset_kind="cleaned",
        approved_by_validation_run_id=approved_by_validation_run_id,
    )
    cleaned_repository.upsert_current_cleaned_records(
        source_name="edmonton_311",
        ingestion_run_id=validation_run_id,
        source_dataset_version_id=version.dataset_version_id,
        approved_dataset_version_id=version.dataset_version_id,
        approved_by_validation_run_id=approved_by_validation_run_id,
        cleaned_records=records,
    )
    dataset_repository.activate_dataset("edmonton_311", version.dataset_version_id, approved_by_validation_run_id)

    run = WeeklyForecastRunRepository(session).create_run(
        trigger_type="scheduled",
        source_cleaned_dataset_version_id=version.dataset_version_id,
        week_start_local=week_start,
        week_end_local=week_end,
    )
    forecast_repository = WeeklyForecastRepository(session)
    forecast_version = forecast_repository.create_forecast_version(
        weekly_forecast_run_id=run.weekly_forecast_run_id,
        source_cleaned_dataset_version_id=version.dataset_version_id,
        week_start_local=week_start,
        week_end_local=week_end,
        geography_scope="citywide",
        baseline_method="historical_weekday_mean",
        summary="Weekly forecast",
    )
    forecast_repository.store_buckets(
        forecast_version.weekly_forecast_version_id,
        [
            {
                "forecast_date_local": (week_start + timedelta(days=day_offset)).date(),
                "service_category": category,
                "geography_key": None,
                "point_forecast": 5 + day_offset,
                "quantile_p10": 4 + day_offset,
                "quantile_p50": 5 + day_offset,
                "quantile_p90": 6 + day_offset,
                "baseline_value": 4 + day_offset,
            }
            for category in ["Roads", "Waste"]
            for day_offset in range(3)
        ],
    )
    forecast_repository.mark_version_stored(forecast_version.weekly_forecast_version_id)
    forecast_repository.activate_forecast(
        forecast_product_name="weekly_7_day_demand",
        weekly_forecast_version_id=forecast_version.weekly_forecast_version_id,
        source_cleaned_dataset_version_id=version.dataset_version_id,
        week_start_local=week_start,
        week_end_local=week_end,
        updated_by_run_id=run.weekly_forecast_run_id,
        geography_scope="citywide",
    )
    session.commit()
    return version.dataset_version_id, forecast_version.weekly_forecast_version_id
