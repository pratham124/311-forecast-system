from __future__ import annotations

import logging

from app.repositories.validation_repository import ValidationRepository
from app.services.cleaned_dataset_service import CleanedDatasetService
from app.services.forecast_service import ForecastService
from app.services.forecast_training_service import ForecastTrainingService
from app.services.weekly_forecast_service import WeeklyForecastService
from app.services.weekly_forecast_training_service import WeeklyForecastTrainingService


class ApprovedPipeline:
    def __init__(
        self,
        cleaned_dataset_service: CleanedDatasetService,
        validation_repository: ValidationRepository,
        forecast_training_service: ForecastTrainingService | None = None,
        weekly_forecast_training_service: WeeklyForecastTrainingService | None = None,
        forecast_service: ForecastService | None = None,
        weekly_forecast_service: WeeklyForecastService | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.cleaned_dataset_service = cleaned_dataset_service
        self.validation_repository = validation_repository
        self.forecast_training_service = forecast_training_service
        self.weekly_forecast_training_service = weekly_forecast_training_service
        self.forecast_service = forecast_service
        self.weekly_forecast_service = weekly_forecast_service
        self.logger = logger or logging.getLogger("validation.approval")

    def approve(
        self,
        *,
        source_name: str,
        ingestion_run_id: str,
        source_dataset_version_id: str,
        validation_run_id: str,
        cleaned_records: list[dict[str, object]],
        duplicate_group_count: int,
        run_follow_on_jobs: bool = True,
    ) -> str:
        self.logger.info(
            "approval.cleaned_dataset.started ingestion_run_id=%s validation_run_id=%s cleaned_record_count=%s duplicate_group_count=%s",
            ingestion_run_id,
            validation_run_id,
            len(cleaned_records),
            duplicate_group_count,
        )
        cleaned_version = self.cleaned_dataset_service.store_and_approve_cleaned_dataset(
            source_name=source_name,
            ingestion_run_id=ingestion_run_id,
            source_dataset_version_id=source_dataset_version_id,
            validation_run_id=validation_run_id,
            cleaned_records=cleaned_records,
            duplicate_group_count=duplicate_group_count,
        )
        self.logger.info(
            "approval.cleaned_dataset.completed ingestion_run_id=%s validation_run_id=%s approved_dataset_version_id=%s",
            ingestion_run_id,
            validation_run_id,
            cleaned_version.dataset_version_id,
        )
        self.validation_repository.finalize_run(
            validation_run_id,
            status="approved",
            approved_dataset_version_id=cleaned_version.dataset_version_id,
            summary="Validation and deduplication completed successfully.",
        )
        if not run_follow_on_jobs:
            self.logger.info(
                "approval.follow_on.skipped ingestion_run_id=%s validation_run_id=%s",
                ingestion_run_id,
                validation_run_id,
            )
            return cleaned_version.dataset_version_id
        self._trigger_forecast_model_training()
        self._trigger_weekly_forecast_model_training()
        self._trigger_forecast_generation()
        self._trigger_weekly_forecast_generation()
        return cleaned_version.dataset_version_id


    def _trigger_forecast_generation(self) -> None:
        if self.forecast_service is None:
            return
        try:
            self.logger.info("approval.follow_on.started job=%s", "forecast-generation")
            run = self.forecast_service.start_run(trigger_type="approval")
            self.forecast_service.execute_run(run.forecast_run_id)
            self.logger.info("approval.follow_on.completed job=%s run_id=%s", "forecast-generation", run.forecast_run_id)
        except Exception:
            self.logger.exception("forecast generation trigger failed after approval")

    def _trigger_weekly_forecast_generation(self) -> None:
        if self.weekly_forecast_service is None:
            return
        try:
            self.logger.info("approval.follow_on.started job=%s", "weekly-forecast-generation")
            run, should_execute = self.weekly_forecast_service.start_run(trigger_type="approval")
            if should_execute:
                self.weekly_forecast_service.execute_run(run.weekly_forecast_run_id)
            self.logger.info(
                "approval.follow_on.completed job=%s run_id=%s executed=%s",
                "weekly-forecast-generation",
                run.weekly_forecast_run_id,
                should_execute,
            )
        except Exception:
            self.logger.exception("weekly forecast generation trigger failed after approval")

    def _trigger_forecast_model_training(self) -> None:
        if self.forecast_training_service is None:
            return
        try:
            self.logger.info("approval.follow_on.started job=%s", "forecast-model-training")
            run = self.forecast_training_service.start_run(trigger_type="approval")
            self.forecast_training_service.execute_run(run.forecast_model_run_id)
            self.logger.info(
                "approval.follow_on.completed job=%s run_id=%s",
                "forecast-model-training",
                run.forecast_model_run_id,
            )
        except Exception:
            self.logger.exception("forecast model training trigger failed after approval")

    def _trigger_weekly_forecast_model_training(self) -> None:
        if self.weekly_forecast_training_service is None:
            return
        try:
            self.logger.info("approval.follow_on.started job=%s", "weekly-forecast-model-training")
            run = self.weekly_forecast_training_service.start_run(trigger_type="approval")
            self.weekly_forecast_training_service.execute_run(run.forecast_model_run_id)
            self.logger.info(
                "approval.follow_on.completed job=%s run_id=%s",
                "weekly-forecast-model-training",
                run.forecast_model_run_id,
            )
        except Exception:
            self.logger.exception("weekly forecast model training trigger failed after approval")
