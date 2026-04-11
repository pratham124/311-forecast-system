from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from typing import Any
import logging

from fastapi import HTTPException, status

from app.clients.nager_date_client import NagerDateClient, NagerDateClientError
from app.clients.weather_client import WeatherClientError
from app.core.logging import summarize_status
from app.models import ForecastBucket, ForecastRun
from app.pipelines.forecasting.feature_preparation import prepare_forecast_features
from app.pipelines.forecasting.hourly_demand_pipeline import HourlyDemandPipeline
from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
from app.repositories.forecast_model_repository import ForecastModelRepository
from app.repositories.forecast_repository import ForecastRepository
from app.repositories.forecast_run_repository import ForecastRunRepository
from app.schemas.forecast import CurrentForecastRead, ForecastBucketRead, ForecastRunStatusRead
from app.services.forecast_activation_service import ForecastActivationService, ForecastStorageError
from app.services.forecast_bucket_service import ForecastBucketService
from app.services.forecast_training_service import ForecastModelStorageError, ForecastTrainingService
from app.services.surge_alert_trigger_service import run_surge_alert_evaluation_for_forecast
from app.services.threshold_alert_trigger_service import run_threshold_alert_evaluation


class ForecastModelUnavailableError(RuntimeError):
    pass


def compute_training_window_start(
    horizon_start: datetime,
    lookback_days: int = 56,
) -> datetime:
    return horizon_start - timedelta(hours=max(lookback_days * 24, 1))


def _parse_requested_at(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _fetch_historical_weather(weather_client: object, start: datetime, end: datetime) -> list[dict[str, object]]:
    if hasattr(weather_client, "fetch_historical_hourly_conditions"):
        return list(weather_client.fetch_historical_hourly_conditions(start, end))
    if hasattr(weather_client, "fetch_hourly_conditions"):
        return list(weather_client.fetch_hourly_conditions(start, end))
    return []


def _fetch_forecast_weather(weather_client: object, start: datetime, end: datetime) -> list[dict[str, object]]:
    if hasattr(weather_client, "fetch_forecast_hourly_conditions"):
        return list(weather_client.fetch_forecast_hourly_conditions(start, end))
    if hasattr(weather_client, "fetch_hourly_conditions"):
        return list(weather_client.fetch_hourly_conditions(start, end))
    return []


def _merge_weather_rows(*weather_sets: list[dict[str, object]]) -> list[dict[str, object]]:
    merged: dict[datetime, dict[str, object]] = {}
    for rows in weather_sets:
        for row in rows:
            timestamp = row.get("timestamp")
            if isinstance(timestamp, datetime):
                merged[timestamp] = row
    return [merged[timestamp] for timestamp in sorted(merged)]


def compute_forecast_horizon(now: datetime | None = None) -> tuple[datetime, datetime]:
    current = now or datetime.now(timezone.utc)
    current = current.astimezone(timezone.utc)
    horizon_start = current.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    horizon_end = horizon_start + timedelta(hours=24)
    return horizon_start, horizon_end


def _map_alert_trigger_source(trigger_type: str) -> str:
    if trigger_type == "scheduled":
        return "forecast_refresh"
    return "forecast_publish"


@dataclass
class ForecastService:
    cleaned_dataset_repository: CleanedDatasetRepository
    forecast_run_repository: ForecastRunRepository
    forecast_repository: ForecastRepository
    geomet_client: object
    nager_date_client: NagerDateClient
    settings: object
    forecast_model_repository: ForecastModelRepository | None = None
    logger: logging.Logger | None = None

    def __post_init__(self) -> None:
        self.logger = self.logger or logging.getLogger("forecast")
        self.pipeline = HourlyDemandPipeline()
        self.bucket_service = ForecastBucketService()
        self.activation_service = ForecastActivationService(self.forecast_repository)
        self.forecast_model_repository = self.forecast_model_repository or SimpleNamespace(find_current_model=lambda *_args, **_kwargs: None)
        self.training_service = ForecastTrainingService(
            cleaned_dataset_repository=self.cleaned_dataset_repository,
            forecast_model_repository=self.forecast_model_repository,
            geomet_client=self.geomet_client,
            nager_date_client=self.nager_date_client,
            settings=self.settings,
            logger=logging.getLogger("forecast.training.loader"),
        )

    def start_run(self, trigger_type: str, now: datetime | None = None) -> ForecastRun:
        horizon_start, horizon_end = compute_forecast_horizon(now)
        approved_dataset = self.cleaned_dataset_repository.get_current_approved_dataset(self.settings.source_name)
        print(
            "[debug][forecast] forecast start "
            f"trigger_type={trigger_type} "
            f"horizon_start={horizon_start.isoformat()} "
            f"horizon_end={horizon_end.isoformat()} "
            f"approved_dataset_version_id={approved_dataset.dataset_version_id if approved_dataset is not None else 'none'}"
        )
        run = self.forecast_run_repository.create_run(
            trigger_type=trigger_type,
            source_cleaned_dataset_version_id=approved_dataset.dataset_version_id if approved_dataset is not None else None,
            requested_horizon_start=horizon_start,
            requested_horizon_end=horizon_end,
        )
        return run

    def execute_run(self, forecast_run_id: str) -> ForecastRun:
        run = self.forecast_run_repository.get_run(forecast_run_id)
        if run is None:
            raise ValueError("Forecast run not found")

        horizon_start = _ensure_utc(run.requested_horizon_start)
        horizon_end = _ensure_utc(run.requested_horizon_end)
        print(
            "[debug][forecast] forecast execute "
            f"run_id={run.forecast_run_id} "
            f"trigger_type={getattr(run, 'trigger_type', 'unknown')} "
            f"horizon_start={horizon_start.isoformat()} "
            f"horizon_end={horizon_end.isoformat()}"
        )

        reused = self.forecast_repository.find_current_for_horizon(
            forecast_product_name=self.settings.forecast_product_name,
            horizon_start=horizon_start,
            horizon_end=horizon_end,
        )
        if reused is not None:
            summary = "served current forecast without regeneration"
            print(
                "[debug][forecast] forecast reuse "
                f"run_id={run.forecast_run_id} "
                f"forecast_version_id={reused.forecast_version_id}"
            )
            self._log("forecast.reused", run_id=run.forecast_run_id, forecast_version_id=reused.forecast_version_id)
            return self.forecast_run_repository.finalize_reused(
                run.forecast_run_id,
                served_forecast_version_id=reused.forecast_version_id,
                geography_scope=reused.geography_scope,
                summary=summary,
            )

        if run.source_cleaned_dataset_version_id is None:
            print(
                "[debug][forecast] forecast fail "
                f"run_id={run.forecast_run_id} reason=missing_input_data detail=no approved cleaned dataset"
            )
            self._log("forecast.failed", run_id=run.forecast_run_id, result_type="missing_input_data")
            return self.forecast_run_repository.finalize_failed(
                run.forecast_run_id,
                result_type="missing_input_data",
                failure_reason="No approved cleaned dataset is available",
                summary="approved cleaned dataset missing",
            )

        training_window_start = compute_training_window_start(
            horizon_start,
            lookback_days=getattr(self.settings, "forecast_training_lookback_days", 56),
        )
        dataset_records = self.cleaned_dataset_repository.list_current_cleaned_records(
            self.settings.source_name,
            start_time=training_window_start,
            end_time=horizon_start,
        )
        print(
            "[debug][forecast] forecast dataset "
            f"run_id={run.forecast_run_id} "
            f"record_count={len(dataset_records)}"
        )
        if not dataset_records:
            print(
                "[debug][forecast] forecast fail "
                f"run_id={run.forecast_run_id} reason=missing_input_data "
                "detail=approved cleaned dataset contains no records"
            )
            self._log("forecast.failed", run_id=run.forecast_run_id, result_type="missing_input_data")
            return self.forecast_run_repository.finalize_failed(
                run.forecast_run_id,
                result_type="missing_input_data",
                failure_reason="Approved cleaned dataset contains no records",
                summary="approved cleaned dataset contains no records",
            )

        try:
            historical_weather = _fetch_historical_weather(self.geomet_client, training_window_start, horizon_start)
            forecast_weather = _fetch_forecast_weather(self.geomet_client, horizon_start, horizon_end)
            weather = _merge_weather_rows(historical_weather, forecast_weather)
            holidays: list[dict[str, object]] = []
            for year in range(training_window_start.year, horizon_end.year + 1):
                holidays.extend(self.nager_date_client.fetch_holidays(year))
            prepared = prepare_forecast_features(
                dataset_records=dataset_records,
                horizon_start=horizon_start,
                horizon_end=horizon_end,
                weather_rows=weather,
                holidays=holidays,
                max_history_hours=max(getattr(self.settings, "forecast_training_lookback_days", 56) * 24, 1),
            )

            stored_model = self.forecast_model_repository.find_current_model(self.settings.forecast_product_name)
            if stored_model is None:
                print(
                    "[debug][forecast] forecast model path "
                    f"run_id={run.forecast_run_id} mode=fallback_fit_predict"
                )
                generated = self.pipeline.run(prepared)
            else:
                if stored_model.source_cleaned_dataset_version_id != run.source_cleaned_dataset_version_id:
                    print(
                        "[debug][forecast] forecast fail "
                        f"run_id={run.forecast_run_id} reason=missing_model "
                        "detail=current trained forecast model is stale for the approved dataset"
                    )
                    raise ForecastModelUnavailableError("Current trained forecast model is stale for the approved dataset")
                print(
                    "[debug][forecast] forecast model path "
                    f"run_id={run.forecast_run_id} "
                    f"mode=stored_artifact "
                    f"artifact_id={stored_model.forecast_model_artifact_id} "
                    f"path={stored_model.artifact_path}"
                )
                artifact = self.training_service.load_artifact_bundle(stored_model.artifact_path)
                generated = self.pipeline.predict(artifact, prepared)
            buckets, geography_scope = self.bucket_service.build_buckets(generated)
            forecast_version_id = self.activation_service.store_and_activate(
                forecast_product_name=self.settings.forecast_product_name,
                forecast_run_id=run.forecast_run_id,
                source_cleaned_dataset_version_id=run.source_cleaned_dataset_version_id,
                horizon_start=horizon_start,
                horizon_end=horizon_end,
                geography_scope=geography_scope,
                baseline_method=str(generated["baseline_method"]),
                summary="forecast generated and activated",
                buckets=buckets,
            )
            try:
                run_threshold_alert_evaluation(
                    self.forecast_repository.session,
                    forecast_reference_id=forecast_version_id,
                    forecast_product="daily",
                    trigger_source=_map_alert_trigger_source(run.trigger_type),
                )
            except Exception as exc:  # noqa: BLE001
                self.logger.warning(
                    "threshold alert evaluation failed for forecast_version_id=%s: %s",
                    forecast_version_id,
                    exc,
                )
            try:
                self.logger.info(
                    "%s",
                    summarize_status(
                        "forecast.surge_alert_trigger.started",
                        forecast_run_id=run.forecast_run_id,
                        forecast_version_id=forecast_version_id,
                        trigger_source="ingestion_completion",
                    ),
                )
                run_surge_alert_evaluation_for_forecast(
                    self.forecast_repository.session,
                    forecast_version_id=forecast_version_id,
                    trigger_source="ingestion_completion",
                )
                self.logger.info(
                    "%s",
                    summarize_status(
                        "forecast.surge_alert_trigger.completed",
                        forecast_run_id=run.forecast_run_id,
                        forecast_version_id=forecast_version_id,
                        trigger_source="ingestion_completion",
                    ),
                )
            except Exception as exc:  # noqa: BLE001
                self.logger.warning(
                    "surge alert evaluation failed for forecast_version_id=%s: %s",
                    forecast_version_id,
                    exc,
                )
        except ForecastModelUnavailableError as exc:
            print(
                "[debug][forecast] forecast fail "
                f"run_id={run.forecast_run_id} reason=missing_model detail={exc}"
            )
            self._log("forecast.failed", run_id=run.forecast_run_id, result_type="missing_model")
            return self.forecast_run_repository.finalize_failed(
                run.forecast_run_id,
                result_type="missing_model",
                failure_reason=str(exc),
                summary="trained forecast model missing",
            )
        except (WeatherClientError, NagerDateClientError, ForecastStorageError, ForecastModelStorageError) as exc:
            result_type = "storage_failure" if isinstance(exc, (ForecastStorageError, ForecastModelStorageError)) else "engine_failure"
            print(
                "[debug][forecast] forecast fail "
                f"run_id={run.forecast_run_id} reason={result_type} detail={exc}"
            )
            self._log("forecast.failed", run_id=run.forecast_run_id, result_type=result_type)
            return self.forecast_run_repository.finalize_failed(
                run.forecast_run_id,
                result_type=result_type,
                failure_reason=str(exc),
                summary="forecast generation failed",
            )
        except Exception as exc:
            print(
                "[debug][forecast] forecast fail "
                f"run_id={run.forecast_run_id} reason=engine_failure detail={exc}"
            )
            self._log("forecast.failed", run_id=run.forecast_run_id, result_type="engine_failure")
            return self.forecast_run_repository.finalize_failed(
                run.forecast_run_id,
                result_type="engine_failure",
                failure_reason=str(exc),
                summary="forecast generation failed",
            )

        print(
            "[debug][forecast] forecast end "
            f"run_id={run.forecast_run_id} "
            f"forecast_version_id={forecast_version_id} "
            f"geography_scope={geography_scope}"
        )
        self._log("forecast.generated", run_id=run.forecast_run_id, forecast_version_id=forecast_version_id)
        return self.forecast_run_repository.finalize_generated(
            run.forecast_run_id,
            forecast_version_id=forecast_version_id,
            geography_scope=geography_scope,
            summary="forecast generated and activated",
        )

    def get_run_status(self, forecast_run_id: str) -> ForecastRunStatusRead:
        run = self.forecast_run_repository.get_run(forecast_run_id)
        if run is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Forecast run not found")
        return ForecastRunStatusRead.model_validate(run, from_attributes=True)

    def get_current_forecast(self) -> CurrentForecastRead:
        marker = self.forecast_repository.get_current_marker(self.settings.forecast_product_name)
        if marker is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Current forecast not found")
        version = self.forecast_repository.get_forecast_version(marker.forecast_version_id)
        if version is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Current forecast not found")
        buckets = self.forecast_repository.list_buckets(version.forecast_version_id)
        return CurrentForecastRead(
            forecastVersionId=version.forecast_version_id,
            sourceCleanedDatasetVersionId=marker.source_cleaned_dataset_version_id,
            horizonStart=marker.horizon_start,
            horizonEnd=marker.horizon_end,
            bucketGranularity=version.bucket_granularity,
            bucketCount=version.bucket_count,
            geographyScope=marker.geography_scope,
            summary=version.summary,
            updatedAt=marker.updated_at,
            updatedByRunId=marker.updated_by_run_id,
            buckets=[self._bucket_to_read(bucket) for bucket in buckets],
        )

    def _bucket_to_read(self, bucket: ForecastBucket) -> ForecastBucketRead:
        return ForecastBucketRead(
            bucketStart=bucket.bucket_start,
            bucketEnd=bucket.bucket_end,
            serviceCategory=bucket.service_category,
            geographyKey=bucket.geography_key,
            pointForecast=float(bucket.point_forecast),
            quantileP10=float(bucket.quantile_p10),
            quantileP50=float(bucket.quantile_p50),
            quantileP90=float(bucket.quantile_p90),
            baselineValue=float(bucket.baseline_value),
        )

    def _log(self, message: str, **fields: object) -> None:
        self.logger.info("%s", summarize_status(message, **fields))
