from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import logging
from pathlib import Path
import pickle

from app.clients.nager_date_client import NagerDateClient, NagerDateClientError
from app.clients.weather_client import WeatherClientError
from app.core.logging import summarize_status
from app.pipelines.forecasting.feature_preparation import prepare_forecast_features
from app.pipelines.forecasting.hourly_demand_pipeline import HourlyDemandPipeline, TrainedHourlyDemandArtifact
from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
from app.repositories.forecast_model_repository import ForecastModelRepository


class ForecastModelStorageError(RuntimeError):
    pass


def compute_training_window_start(window_end: datetime, lookback_days: int = 56) -> datetime:
    return window_end - timedelta(hours=max(lookback_days * 24, 1))


def compute_training_window_end(now: datetime | None = None) -> datetime:
    current = now or datetime.now(timezone.utc)
    current = current.astimezone(timezone.utc)
    return current.replace(minute=0, second=0, microsecond=0)


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


@dataclass
class ForecastTrainingService:
    cleaned_dataset_repository: CleanedDatasetRepository
    forecast_model_repository: ForecastModelRepository
    geomet_client: object
    nager_date_client: NagerDateClient
    settings: object
    logger: logging.Logger | None = None

    def __post_init__(self) -> None:
        self.logger = self.logger or logging.getLogger("forecast.training")
        self.pipeline = HourlyDemandPipeline()

    def start_run(self, trigger_type: str, now: datetime | None = None):
        training_window_end = compute_training_window_end(now)
        training_window_start = compute_training_window_start(
            training_window_end,
            lookback_days=getattr(self.settings, "forecast_training_lookback_days", 56),
        )
        approved_dataset = self.cleaned_dataset_repository.get_current_approved_dataset(self.settings.source_name)
        print(
            "[debug][forecast] training start "
            f"trigger_type={trigger_type} "
            f"window_start={training_window_start.isoformat()} "
            f"window_end={training_window_end.isoformat()} "
            f"approved_dataset_version_id={approved_dataset.dataset_version_id if approved_dataset is not None else 'none'}"
        )
        return self.forecast_model_repository.create_run(
            forecast_product_name=self.settings.forecast_product_name,
            trigger_type=trigger_type,
            source_cleaned_dataset_version_id=approved_dataset.dataset_version_id if approved_dataset is not None else None,
            training_window_start=training_window_start,
            training_window_end=training_window_end,
        )

    def execute_run(self, forecast_model_run_id: str):
        run = self.forecast_model_repository.get_run(forecast_model_run_id)
        if run is None:
            raise ValueError("Forecast model run not found")
        run_id = run.forecast_model_run_id
        savepoint = self._begin_repository_savepoint()

        training_window_start = _ensure_utc(run.training_window_start)
        training_window_end = _ensure_utc(run.training_window_end)
        print(
            "[debug][forecast] training execute "
            f"run_id={run.forecast_model_run_id} "
            f"trigger_type={getattr(run, 'trigger_type', 'unknown')} "
            f"window_start={training_window_start.isoformat()} "
            f"window_end={training_window_end.isoformat()}"
        )

        if run.source_cleaned_dataset_version_id is None:
            print(
                "[debug][forecast] training fail "
                f"run_id={run.forecast_model_run_id} reason=missing_input_data "
                "detail=no approved cleaned dataset"
            )
            self._log("forecast_model.failed", run_id=run.forecast_model_run_id, result_type="missing_input_data")
            return self.forecast_model_repository.finalize_failed(
                run.forecast_model_run_id,
                result_type="missing_input_data",
                failure_reason="No approved cleaned dataset is available",
                summary="approved cleaned dataset missing",
            )

        dataset_records = self.cleaned_dataset_repository.list_current_cleaned_records(
            self.settings.source_name,
            start_time=training_window_start,
            end_time=training_window_end,
        )
        print(
            "[debug][forecast] training dataset "
            f"run_id={run.forecast_model_run_id} "
            f"record_count={len(dataset_records)}"
        )
        if not dataset_records:
            print(
                "[debug][forecast] training fail "
                f"run_id={run.forecast_model_run_id} reason=missing_input_data "
                "detail=approved cleaned dataset contains no records"
            )
            self._log("forecast_model.failed", run_id=run.forecast_model_run_id, result_type="missing_input_data")
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
            prepared = prepare_forecast_features(
                dataset_records=dataset_records,
                horizon_start=training_window_end,
                horizon_end=training_window_end,
                weather_rows=weather,
                holidays=holidays,
                max_history_hours=max(getattr(self.settings, "forecast_training_lookback_days", 56) * 24, 1),
            )
            artifact = self.pipeline.fit(prepared)
            artifact_path = self._artifact_path(run.forecast_model_run_id)
            print(
                "[debug][forecast] training artifact save "
                f"run_id={run.forecast_model_run_id} "
                f"path={artifact_path} "
                f"geography_scope={artifact.geography_scope}"
            )
            self._store_artifact(artifact, artifact_path)
            stored_artifact = self.forecast_model_repository.create_artifact(
                forecast_product_name=self.settings.forecast_product_name,
                forecast_model_run_id=run.forecast_model_run_id,
                source_cleaned_dataset_version_id=run.source_cleaned_dataset_version_id,
                geography_scope=artifact.geography_scope,
                model_family=artifact.model_family,
                baseline_method=artifact.baseline_method,
                feature_schema_version=self.pipeline.feature_schema_version,
                artifact_path=str(artifact_path),
                summary="forecast model trained and stored",
            )
            print(
                "[debug][forecast] training artifact stored "
                f"run_id={run_id} "
                f"artifact_id={stored_artifact.forecast_model_artifact_id} "
                f"path={artifact_path}"
            )
            self.forecast_model_repository.activate_artifact(
                forecast_product_name=self.settings.forecast_product_name,
                forecast_model_artifact_id=stored_artifact.forecast_model_artifact_id,
                source_cleaned_dataset_version_id=run.source_cleaned_dataset_version_id,
                training_window_start=training_window_start,
                training_window_end=training_window_end,
                updated_by_run_id=run.forecast_model_run_id,
                geography_scope=artifact.geography_scope,
            )
        except (WeatherClientError, NagerDateClientError) as exc:
            self._rollback_repository_savepoint(savepoint)
            print(
                "[debug][forecast] training fail "
                f"run_id={run_id} reason=engine_failure detail={exc}"
            )
            self._log("forecast_model.failed", run_id=run_id, result_type="engine_failure")
            return self.forecast_model_repository.finalize_failed(
                run_id,
                result_type="engine_failure",
                failure_reason=str(exc),
                summary="forecast model training failed",
            )
        except (OSError, pickle.PickleError, ForecastModelStorageError) as exc:
            self._rollback_repository_savepoint(savepoint)
            print(
                "[debug][forecast] training fail "
                f"run_id={run_id} reason=storage_failure detail={exc}"
            )
            self._log("forecast_model.failed", run_id=run_id, result_type="storage_failure")
            return self.forecast_model_repository.finalize_failed(
                run_id,
                result_type="storage_failure",
                failure_reason=str(exc),
                summary="forecast model storage failed",
            )
        except Exception as exc:
            self._rollback_repository_savepoint(savepoint)
            print(
                "[debug][forecast] training fail "
                f"run_id={run_id} reason=engine_failure detail={exc}"
            )
            self._log("forecast_model.failed", run_id=run_id, result_type="engine_failure")
            return self.forecast_model_repository.finalize_failed(
                run_id,
                result_type="engine_failure",
                failure_reason=str(exc),
                summary="forecast model training failed",
            )

        print(
            "[debug][forecast] training end "
            f"run_id={run_id} "
            f"artifact_id={stored_artifact.forecast_model_artifact_id} "
            f"artifact_path={stored_artifact.artifact_path}"
        )
        self._commit_repository_savepoint(savepoint)
        self._log("forecast_model.trained", run_id=run_id, artifact_id=stored_artifact.forecast_model_artifact_id)
        return self.forecast_model_repository.finalize_trained(
            run_id,
            forecast_model_artifact_id=stored_artifact.forecast_model_artifact_id,
            geography_scope=artifact.geography_scope,
            summary="forecast model trained and stored",
        )

    def load_current_artifact(self) -> TrainedHourlyDemandArtifact | None:
        stored = self.forecast_model_repository.find_current_model(self.settings.forecast_product_name)
        if stored is None:
            print(
                "[debug][forecast] training artifact load "
                f"forecast_product_name={self.settings.forecast_product_name} result=missing"
            )
            return None
        print(
            "[debug][forecast] training artifact load "
            f"forecast_product_name={self.settings.forecast_product_name} "
            f"artifact_id={stored.forecast_model_artifact_id} "
            f"path={stored.artifact_path}"
        )
        return self.load_artifact_bundle(stored.artifact_path)

    def load_artifact_bundle(self, artifact_path: str) -> TrainedHourlyDemandArtifact:
        print(f"[debug][forecast] training artifact load path={artifact_path}")
        try:
            with Path(artifact_path).open("rb") as handle:
                return pickle.load(handle)
        except FileNotFoundError as exc:
            raise ForecastModelStorageError("Forecast model artifact file not found") from exc

    def _artifact_path(self, forecast_model_run_id: str) -> Path:
        artifact_dir = Path(getattr(self.settings, "forecast_model_artifact_dir", "backend/.artifacts/forecast_models"))
        artifact_dir.mkdir(parents=True, exist_ok=True)
        return artifact_dir / f"{forecast_model_run_id}.pkl"

    def _store_artifact(self, artifact: TrainedHourlyDemandArtifact, artifact_path: Path) -> None:
        with artifact_path.open("wb") as handle:
            pickle.dump(artifact, handle)

    def _begin_repository_savepoint(self):
        session = getattr(self.forecast_model_repository, "session", None)
        if session is None:
            return None
        return session.begin_nested()

    def _rollback_repository_savepoint(self, savepoint) -> None:
        if savepoint is not None and getattr(savepoint, "is_active", False):
            savepoint.rollback()

    def _commit_repository_savepoint(self, savepoint) -> None:
        if savepoint is not None and getattr(savepoint, "is_active", False):
            savepoint.commit()

    def _rollback_repository_session(self) -> None:
        session = getattr(self.forecast_model_repository, "session", None)
        if session is not None:
            session.rollback()

    def _log(self, message: str, **fields: object) -> None:
        self.logger.info("%s", summarize_status(message, **fields))
