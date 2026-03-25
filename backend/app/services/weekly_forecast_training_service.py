from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import logging
from pathlib import Path
import pickle

from app.clients.geomet_client import GeoMetClient, GeoMetClientError
from app.clients.nager_date_client import NagerDateClient, NagerDateClientError
from fastapi import HTTPException, status

from app.core.logging import summarize_status
from app.pipelines.forecasting.weekly_feature_preparation import prepare_weekly_forecast_features
from app.pipelines.forecasting.weekly_demand_pipeline import TrainedWeeklyDemandArtifact, WeeklyDemandPipeline
from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
from app.repositories.forecast_model_repository import ForecastModelRepository
from app.services.forecast_training_service import ForecastModelStorageError
from app.schemas.weekly_forecast import CurrentWeeklyForecastModelRead, WeeklyForecastModelRunStatusRead
from app.services.week_window_service import WeekWindowService


def compute_weekly_training_window_end(now: datetime | None = None, timezone_name: str = "America/Edmonton") -> datetime:
    current = now or datetime.now(timezone.utc)
    return WeekWindowService(timezone_name).get_week_window(current).week_start_local


def compute_weekly_training_window_start(window_end: datetime, lookback_days: int = 56) -> datetime:
    return window_end - timedelta(days=max(lookback_days, 7))


def _fetch_historical_weather(geomet_client: object, start: datetime, end: datetime) -> list[dict[str, object]]:
    if hasattr(geomet_client, "fetch_historical_hourly_conditions"):
        return list(geomet_client.fetch_historical_hourly_conditions(start, end))
    if hasattr(geomet_client, "fetch_hourly_conditions"):
        return list(geomet_client.fetch_hourly_conditions(start, end))
    return []


@dataclass
class WeeklyForecastTrainingService:
    cleaned_dataset_repository: CleanedDatasetRepository
    forecast_model_repository: ForecastModelRepository
    geomet_client: GeoMetClient
    nager_date_client: NagerDateClient
    settings: object
    logger: logging.Logger | None = None

    def __post_init__(self) -> None:
        self.logger = self.logger or logging.getLogger("weekly_forecast.training")
        self.pipeline = WeeklyDemandPipeline()

    def start_run(self, trigger_type: str, now: datetime | None = None):
        training_window_end = compute_weekly_training_window_end(now, getattr(self.settings, "weekly_forecast_timezone", "America/Edmonton"))
        training_window_start = compute_weekly_training_window_start(
            training_window_end,
            lookback_days=getattr(self.settings, "weekly_forecast_history_days", 56),
        )
        approved_dataset = self.cleaned_dataset_repository.get_current_approved_dataset(self.settings.source_name)
        return self.forecast_model_repository.create_run(
            forecast_product_name=self.settings.weekly_forecast_product_name,
            trigger_type=trigger_type,
            source_cleaned_dataset_version_id=approved_dataset.dataset_version_id if approved_dataset is not None else None,
            training_window_start=training_window_start,
            training_window_end=training_window_end,
        )

    def execute_run(self, forecast_model_run_id: str):
        run = self.forecast_model_repository.get_run(forecast_model_run_id)
        if run is None:
            raise ValueError("Weekly forecast model run not found")
        if run.source_cleaned_dataset_version_id is None:
            self._log("weekly_forecast_model.failed", run_id=run.forecast_model_run_id, result_type="missing_input_data")
            return self.forecast_model_repository.finalize_failed(
                run.forecast_model_run_id,
                result_type="missing_input_data",
                failure_reason="No approved cleaned dataset is available",
                summary="approved cleaned dataset missing",
            )

        training_window_start = run.training_window_start
        training_window_end = run.training_window_end
        dataset_records = self.cleaned_dataset_repository.list_current_cleaned_records(
            self.settings.source_name,
            start_time=training_window_start,
            end_time=training_window_end,
        )
        if not dataset_records:
            self._log("weekly_forecast_model.failed", run_id=run.forecast_model_run_id, result_type="missing_input_data")
            return self.forecast_model_repository.finalize_failed(
                run.forecast_model_run_id,
                result_type="missing_input_data",
                failure_reason="Approved cleaned dataset contains no records",
                summary="approved cleaned dataset contains no records",
            )

        try:
            weather = _fetch_historical_weather(self.geomet_client, training_window_start, training_window_end)
            holidays: list[dict[str, object]] = []
            for year in range(training_window_start.year, training_window_end.year + 1):
                holidays.extend(self.nager_date_client.fetch_holidays(year))
            prepared = prepare_weekly_forecast_features(
                dataset_records=dataset_records,
                week_start_local=training_window_end,
                week_end_local=training_window_end + timedelta(days=6, hours=23, minutes=59, seconds=59),
                timezone_name=getattr(self.settings, "weekly_forecast_timezone", "America/Edmonton"),
                weather_rows=weather,
                holidays=holidays,
            )
            artifact = self.pipeline.fit(prepared)
            artifact_path = self._artifact_path(run.forecast_model_run_id)
            self._store_artifact(artifact, artifact_path)
            stored_artifact = self.forecast_model_repository.create_artifact(
                forecast_product_name=self.settings.weekly_forecast_product_name,
                forecast_model_run_id=run.forecast_model_run_id,
                source_cleaned_dataset_version_id=run.source_cleaned_dataset_version_id,
                geography_scope=artifact.geography_scope,
                model_family=artifact.model_family,
                baseline_method=artifact.baseline_method,
                feature_schema_version=self.pipeline.feature_schema_version,
                artifact_path=str(artifact_path),
                summary="weekly forecast model trained and stored",
            )
            self.forecast_model_repository.activate_artifact(
                forecast_product_name=self.settings.weekly_forecast_product_name,
                forecast_model_artifact_id=stored_artifact.forecast_model_artifact_id,
                source_cleaned_dataset_version_id=run.source_cleaned_dataset_version_id,
                training_window_start=training_window_start,
                training_window_end=training_window_end,
                updated_by_run_id=run.forecast_model_run_id,
                geography_scope=artifact.geography_scope,
            )
        except (GeoMetClientError, NagerDateClientError) as exc:
            self._log("weekly_forecast_model.failed", run_id=run.forecast_model_run_id, result_type="engine_failure")
            return self.forecast_model_repository.finalize_failed(
                run.forecast_model_run_id,
                result_type="engine_failure",
                failure_reason=str(exc),
                summary="weekly forecast model training failed",
            )
        except (OSError, pickle.PickleError, ForecastModelStorageError) as exc:
            self._log("weekly_forecast_model.failed", run_id=run.forecast_model_run_id, result_type="storage_failure")
            return self.forecast_model_repository.finalize_failed(
                run.forecast_model_run_id,
                result_type="storage_failure",
                failure_reason=str(exc),
                summary="weekly forecast model storage failed",
            )
        except Exception as exc:
            self._log("weekly_forecast_model.failed", run_id=run.forecast_model_run_id, result_type="engine_failure")
            return self.forecast_model_repository.finalize_failed(
                run.forecast_model_run_id,
                result_type="engine_failure",
                failure_reason=str(exc),
                summary="weekly forecast model training failed",
            )

        self._log("weekly_forecast_model.trained", run_id=run.forecast_model_run_id, artifact_id=stored_artifact.forecast_model_artifact_id)
        return self.forecast_model_repository.finalize_trained(
            run.forecast_model_run_id,
            forecast_model_artifact_id=stored_artifact.forecast_model_artifact_id,
            geography_scope=artifact.geography_scope,
            summary="weekly forecast model trained and stored",
        )

    def get_run_status(self, forecast_model_run_id: str) -> WeeklyForecastModelRunStatusRead:
        run = self.forecast_model_repository.get_run(forecast_model_run_id)
        if run is None or getattr(run, "forecast_product_name", None) != self.settings.weekly_forecast_product_name:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Weekly forecast model run not found")
        return WeeklyForecastModelRunStatusRead.model_validate(run, from_attributes=True)

    def get_current_model(self) -> CurrentWeeklyForecastModelRead:
        marker = self.forecast_model_repository.get_current_marker(self.settings.weekly_forecast_product_name)
        if marker is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Current weekly forecast model not found")
        artifact = self.forecast_model_repository.get_artifact(marker.forecast_model_artifact_id)
        if artifact is None or artifact.forecast_product_name != self.settings.weekly_forecast_product_name:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Current weekly forecast model not found")
        return CurrentWeeklyForecastModelRead(
            forecastProductName=marker.forecast_product_name,
            forecastModelArtifactId=artifact.forecast_model_artifact_id,
            sourceCleanedDatasetVersionId=marker.source_cleaned_dataset_version_id,
            trainingWindowStart=marker.training_window_start,
            trainingWindowEnd=marker.training_window_end,
            updatedAt=marker.updated_at,
            updatedByRunId=marker.updated_by_run_id,
            geographyScope=marker.geography_scope,
            modelFamily=artifact.model_family,
            baselineMethod=artifact.baseline_method,
            featureSchemaVersion=artifact.feature_schema_version,
            artifactPath=artifact.artifact_path,
            summary=artifact.summary,
        )

    def load_current_artifact(self) -> TrainedWeeklyDemandArtifact | None:
        stored = self.forecast_model_repository.find_current_model(self.settings.weekly_forecast_product_name)
        if stored is None:
            return None
        return self.load_artifact_bundle(stored.artifact_path)

    def load_artifact_bundle(self, artifact_path: str) -> TrainedWeeklyDemandArtifact:
        try:
            with Path(artifact_path).open("rb") as handle:
                return pickle.load(handle)
        except FileNotFoundError as exc:
            raise ForecastModelStorageError("Weekly forecast model artifact file not found") from exc

    def _artifact_path(self, forecast_model_run_id: str) -> Path:
        artifact_dir = Path(getattr(self.settings, "weekly_forecast_model_artifact_dir", "backend/.artifacts/weekly_forecast_models"))
        artifact_dir.mkdir(parents=True, exist_ok=True)
        return artifact_dir / f"{forecast_model_run_id}.pkl"

    def _store_artifact(self, artifact: TrainedWeeklyDemandArtifact, artifact_path: Path) -> None:
        try:
            with artifact_path.open("wb") as handle:
                pickle.dump(artifact, handle)
        except OSError as exc:
            raise ForecastModelStorageError("Unable to persist weekly forecast model artifact") from exc

    def _log(self, message: str, **fields) -> None:
        self.logger.info("%s", summarize_status(message, **fields))
