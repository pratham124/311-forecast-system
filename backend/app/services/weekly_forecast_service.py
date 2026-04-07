from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from datetime import timedelta
from typing import Any
import logging

from fastapi import HTTPException, status

from app.clients.nager_date_client import NagerDateClient, NagerDateClientError
from app.clients.weather_client import WeatherClientError
from app.core.logging import summarize_status
from app.models import WeeklyForecastBucket, WeeklyForecastRun
from app.pipelines.forecasting.weekly_demand_pipeline import WeeklyDemandPipeline
from app.pipelines.forecasting.weekly_feature_preparation import prepare_weekly_forecast_features
from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
from app.repositories.forecast_model_repository import ForecastModelRepository
from app.repositories.forecast_repository import ForecastRepository
from app.repositories.notification_event_repository import NotificationEventRepository
from app.repositories.threshold_configuration_repository import ThresholdConfigurationRepository
from app.repositories.threshold_evaluation_repository import ThresholdEvaluationRepository
from app.repositories.threshold_state_repository import ThresholdStateRepository
from app.repositories.weekly_forecast_repository import WeeklyForecastRepository
from app.repositories.weekly_forecast_run_repository import WeeklyForecastRunRepository
from app.schemas.weekly_forecast import CurrentWeeklyForecastRead, WeeklyForecastBucketRead, WeeklyForecastRunStatusRead
from app.services.forecast_scope_service import ForecastScopeService
from app.pipelines.threshold_alert_evaluation_pipeline import ThresholdAlertEvaluationPipeline
from app.services.week_window_service import WeekWindowService
from app.services.forecast_service import ForecastModelUnavailableError
from app.services.forecast_training_service import ForecastModelStorageError
from app.services.weekly_forecast_activation_service import WeeklyForecastActivationService, WeeklyForecastStorageError
from app.services.weekly_forecast_bucket_service import WeeklyForecastBucketService
from app.services.weekly_forecast_training_service import WeeklyForecastTrainingService


@dataclass
class WeeklyForecastService:
    cleaned_dataset_repository: CleanedDatasetRepository
    weekly_forecast_run_repository: WeeklyForecastRunRepository
    weekly_forecast_repository: WeeklyForecastRepository
    settings: object
    geomet_client: object
    nager_date_client: NagerDateClient
    forecast_model_repository: ForecastModelRepository | None = None
    logger: logging.Logger | None = None

    def __post_init__(self) -> None:
        self.logger = self.logger or logging.getLogger("weekly_forecast")
        self.week_window_service = WeekWindowService(getattr(self.settings, "weekly_forecast_timezone", "America/Edmonton"))
        self.pipeline = WeeklyDemandPipeline()
        self.bucket_service = WeeklyForecastBucketService()
        self.activation_service = WeeklyForecastActivationService(self.weekly_forecast_repository)
        self.forecast_model_repository = self.forecast_model_repository or SimpleNamespace(find_current_model=lambda *_args, **_kwargs: None)
        self.training_service = WeeklyForecastTrainingService(
            cleaned_dataset_repository=self.cleaned_dataset_repository,
            forecast_model_repository=self.forecast_model_repository,
            geomet_client=self.geomet_client,
            nager_date_client=self.nager_date_client,
            settings=self.settings,
            logger=logging.getLogger("weekly_forecast.training.loader"),
        )

    def start_run(self, trigger_type: str, now=None) -> tuple[WeeklyForecastRun, bool]:
        week_window = self.week_window_service.get_week_window(now)
        existing = self.weekly_forecast_run_repository.find_in_progress_run(
            week_start_local=week_window.week_start_local,
            week_end_local=week_window.week_end_local,
        )
        if existing is not None:
            return existing, False

        approved_dataset = self.cleaned_dataset_repository.get_current_approved_dataset(self.settings.source_name)
        run = self.weekly_forecast_run_repository.create_run(
            trigger_type=trigger_type,
            source_cleaned_dataset_version_id=approved_dataset.dataset_version_id if approved_dataset is not None else None,
            week_start_local=week_window.week_start_local,
            week_end_local=week_window.week_end_local,
        )
        return run, True

    def execute_run(self, weekly_forecast_run_id: str) -> WeeklyForecastRun:
        run = self.weekly_forecast_run_repository.get_run(weekly_forecast_run_id)
        if run is None:
            raise ValueError("Weekly forecast run not found")
        if run.status != "running":
            return run

        reused = self.weekly_forecast_repository.find_current_for_week(
            forecast_product_name=self.settings.weekly_forecast_product_name,
            week_start_local=run.week_start_local,
            week_end_local=run.week_end_local,
        )
        if reused is not None:
            self._log("weekly_forecast.reused", run_id=run.weekly_forecast_run_id, forecast_version_id=reused.weekly_forecast_version_id)
            return self.weekly_forecast_run_repository.finalize_reused(
                run.weekly_forecast_run_id,
                served_forecast_version_id=reused.weekly_forecast_version_id,
                geography_scope=reused.geography_scope,
                summary="served current weekly forecast without regeneration",
            )

        if run.source_cleaned_dataset_version_id is None:
            return self._finalize_missing_data(run, "No approved cleaned dataset is available")

        history_days = max(getattr(self.settings, "weekly_forecast_history_days", 56), 7)
        dataset_records = self.cleaned_dataset_repository.list_current_cleaned_records(
            self.settings.source_name,
            start_time=run.week_start_local - timedelta(days=history_days),
            end_time=run.week_start_local,
        )
        if not dataset_records:
            return self._finalize_missing_data(run, "Approved cleaned dataset contains no records")

        try:
            weather_rows = list(self.geomet_client.fetch_forecast_hourly_conditions(run.week_start_local, run.week_end_local))
            holidays: list[dict[str, object]] = []
            for year in range(run.week_start_local.year, run.week_end_local.year + 1):
                holidays.extend(self.nager_date_client.fetch_holidays(year))
            prepared = prepare_weekly_forecast_features(
                dataset_records=dataset_records,
                week_start_local=run.week_start_local,
                week_end_local=run.week_end_local,
                timezone_name=self.settings.weekly_forecast_timezone,
                weather_rows=weather_rows,
                holidays=holidays,
            )
            if not prepared["scopes"]:
                return self._finalize_missing_data(run, "Approved cleaned dataset contains no usable category records")
            stored_model = self.forecast_model_repository.find_current_model(self.settings.weekly_forecast_product_name)
            if stored_model is None:
                generated = self.pipeline.run(prepared)
            else:
                if stored_model.source_cleaned_dataset_version_id != run.source_cleaned_dataset_version_id:
                    raise ForecastModelUnavailableError("Current trained weekly forecast model is stale for the approved dataset")
                if stored_model.feature_schema_version != self.pipeline.feature_schema_version:
                    raise ForecastModelUnavailableError("Current trained weekly forecast model uses an outdated feature schema")
                artifact = self.training_service.load_artifact_bundle(stored_model.artifact_path)
                generated = self.pipeline.predict(artifact, prepared)
            buckets, geography_scope = self.bucket_service.build_buckets(generated)
            weekly_forecast_version_id = self.activation_service.store_and_activate(
                forecast_product_name=self.settings.weekly_forecast_product_name,
                weekly_forecast_run_id=run.weekly_forecast_run_id,
                source_cleaned_dataset_version_id=run.source_cleaned_dataset_version_id,
                week_start_local=run.week_start_local,
                week_end_local=run.week_end_local,
                geography_scope=geography_scope,
                baseline_method=str(generated["baseline_method"]),
                summary="weekly forecast generated and activated",
                buckets=buckets,
            )
            self._run_threshold_alert_evaluation(run.weekly_forecast_run_id, weekly_forecast_version_id)
        except (WeatherClientError, NagerDateClientError) as exc:
            self._log("weekly_forecast.failed", run_id=run.weekly_forecast_run_id, result_type="engine_failure")
            return self.weekly_forecast_run_repository.finalize_failed(
                run.weekly_forecast_run_id,
                result_type="engine_failure",
                failure_reason=str(exc),
                summary="weekly forecast enrichment failed",
            )
        except (ForecastModelUnavailableError, ForecastModelStorageError) as exc:
            self._log("weekly_forecast.failed", run_id=run.weekly_forecast_run_id, result_type="engine_failure")
            return self.weekly_forecast_run_repository.finalize_failed(
                run.weekly_forecast_run_id,
                result_type="engine_failure",
                failure_reason=str(exc),
                summary="weekly forecast model unavailable",
            )
        except WeeklyForecastStorageError as exc:
            self._log("weekly_forecast.failed", run_id=run.weekly_forecast_run_id, result_type="storage_failure")
            return self.weekly_forecast_run_repository.finalize_failed(
                run.weekly_forecast_run_id,
                result_type="storage_failure",
                failure_reason=str(exc),
                summary="weekly forecast storage failed",
            )
        except Exception as exc:
            self._log("weekly_forecast.failed", run_id=run.weekly_forecast_run_id, result_type="engine_failure")
            return self.weekly_forecast_run_repository.finalize_failed(
                run.weekly_forecast_run_id,
                result_type="engine_failure",
                failure_reason=str(exc),
                summary="weekly forecast generation failed",
            )

        self._log("weekly_forecast.generated", run_id=run.weekly_forecast_run_id, forecast_version_id=weekly_forecast_version_id)
        return self.weekly_forecast_run_repository.finalize_generated(
            run.weekly_forecast_run_id,
            generated_forecast_version_id=weekly_forecast_version_id,
            geography_scope=geography_scope,
            summary="weekly forecast generated and activated",
        )

    def _run_threshold_alert_evaluation(self, weekly_forecast_run_id: str, weekly_forecast_version_id: str) -> None:
        session = self.weekly_forecast_repository.session
        pipeline = ThresholdAlertEvaluationPipeline(
            forecast_scope_service=ForecastScopeService(
                forecast_repository=ForecastRepository(session),
                weekly_forecast_repository=self.weekly_forecast_repository,
            ),
            threshold_configuration_repository=ThresholdConfigurationRepository(session),
            threshold_evaluation_repository=ThresholdEvaluationRepository(session),
            threshold_state_repository=ThresholdStateRepository(session),
            notification_event_repository=NotificationEventRepository(session),
            logger=logging.getLogger("weekly_forecast.alerts"),
        )
        try:
            pipeline.evaluate(
                forecast_reference_id=weekly_forecast_version_id,
                forecast_product="weekly",
                trigger_source="forecast_publish",
                weekly_forecast_run_id=weekly_forecast_run_id,
            )
        except Exception as exc:
            self.logger.warning(
                "weekly_forecast.threshold_alert_evaluation_failed run_id=%s version_id=%s error=%s",
                weekly_forecast_run_id,
                weekly_forecast_version_id,
                exc,
            )

    def get_run_status(self, weekly_forecast_run_id: str) -> WeeklyForecastRunStatusRead:
        run = self.weekly_forecast_run_repository.get_run(weekly_forecast_run_id)
        if run is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Weekly forecast run not found")
        return WeeklyForecastRunStatusRead.model_validate(run, from_attributes=True)

    def get_current_forecast(self) -> CurrentWeeklyForecastRead:
        marker = self.weekly_forecast_repository.get_current_marker(self.settings.weekly_forecast_product_name)
        if marker is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Current weekly forecast not found")
        version = self.weekly_forecast_repository.get_forecast_version(marker.weekly_forecast_version_id)
        if version is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Current weekly forecast not found")
        buckets = self.weekly_forecast_repository.list_buckets(version.weekly_forecast_version_id)
        return CurrentWeeklyForecastRead(
            weeklyForecastVersionId=version.weekly_forecast_version_id,
            sourceCleanedDatasetVersionId=marker.source_cleaned_dataset_version_id,
            weekStartLocal=marker.week_start_local,
            weekEndLocal=marker.week_end_local,
            bucketGranularity=version.bucket_granularity,
            bucketCountDays=version.bucket_count_days,
            geographyScope=marker.geography_scope,
            updatedAt=marker.updated_at,
            updatedByRunId=marker.updated_by_run_id,
            summary=version.summary,
            buckets=[self._bucket_to_read(bucket) for bucket in buckets],
        )

    def _finalize_missing_data(self, run: WeeklyForecastRun, failure_reason: str) -> WeeklyForecastRun:
        self._log("weekly_forecast.failed", run_id=run.weekly_forecast_run_id, result_type="missing_input_data")
        return self.weekly_forecast_run_repository.finalize_failed(
            run.weekly_forecast_run_id,
            result_type="missing_input_data",
            failure_reason=failure_reason,
            summary="approved cleaned dataset missing or unusable",
        )

    def _bucket_to_read(self, bucket: WeeklyForecastBucket) -> WeeklyForecastBucketRead:
        return WeeklyForecastBucketRead(
            forecastDateLocal=bucket.forecast_date_local,
            serviceCategory=bucket.service_category,
            geographyKey=bucket.geography_key,
            pointForecast=float(bucket.point_forecast),
            quantileP10=float(bucket.quantile_p10),
            quantileP50=float(bucket.quantile_p50),
            quantileP90=float(bucket.quantile_p90),
            baselineValue=float(bucket.baseline_value),
        )

    def _log(self, message: str, **fields: Any) -> None:
        self.logger.info("%s", summarize_status(message, **fields))
