from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.clients.nager_date_client import NagerDateClientError
from app.clients.nager_date_client import NagerDateClient
from app.clients.weather_client import WeatherClientError
from app.clients.weather_client import build_weather_client
from app.core.config import get_settings
from app.pipelines.ingestion.approved_pipeline import ApprovedPipeline
from app.pipelines.ingestion.blocked_outcome_pipeline import BlockedOutcomePipeline
from app.pipelines.ingestion.rejection_pipeline import RejectionPipeline
from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
from app.repositories.forecast_model_repository import ForecastModelRepository
from app.repositories.forecast_repository import ForecastRepository
from app.repositories.forecast_run_repository import ForecastRunRepository
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.review_needed_repository import ReviewNeededRepository
from app.repositories.validation_repository import ValidationRepository
from app.repositories.weekly_forecast_repository import WeeklyForecastRepository
from app.repositories.weekly_forecast_run_repository import WeeklyForecastRunRepository
from app.services.cleaned_dataset_service import CleanedDatasetService
from app.services.forecast_service import ForecastService
from app.services.forecast_training_service import ForecastTrainingService
from app.services.duplicate_analysis_service import DuplicateAnalysisService
from app.services.duplicate_resolution_service import DuplicateResolutionService
from app.services.schema_validation_service import SchemaValidationService
from app.services.weekly_forecast_service import WeeklyForecastService
from app.services.weekly_forecast_training_service import WeeklyForecastTrainingService


class _ApprovalWeatherClient:
    def __init__(self, client: object, logger: logging.Logger) -> None:
        self._client = client
        self._logger = logger

    def fetch_historical_hourly_conditions(self, start, end) -> list[dict[str, object]]:
        return self._fetch("historical", start, end)

    def fetch_forecast_hourly_conditions(self, start, end) -> list[dict[str, object]]:
        return self._fetch("forecast", start, end)

    def fetch_hourly_conditions(self, start, end) -> list[dict[str, object]]:
        return self._fetch("generic", start, end)

    def _fetch(self, mode: str, start, end) -> list[dict[str, object]]:
        method_names = {
            "historical": ("fetch_historical_hourly_conditions", "fetch_hourly_conditions"),
            "forecast": ("fetch_forecast_hourly_conditions", "fetch_hourly_conditions"),
            "generic": ("fetch_hourly_conditions",),
        }[mode]
        for method_name in method_names:
            method = getattr(self._client, method_name, None)
            if method is None:
                continue
            try:
                return list(method(start, end))
            except WeatherClientError as exc:
                self._logger.warning(
                    "approval.follow_on.weather_fallback mode=%s start=%s end=%s detail=%s",
                    mode,
                    start,
                    end,
                    exc,
                )
                return []
        return []


class _ApprovalHolidayClient:
    def __init__(self, client: NagerDateClient, logger: logging.Logger) -> None:
        self._client = client
        self._logger = logger

    def fetch_holidays(self, year: int, country_code: str = "CA") -> list[dict[str, object]]:
        try:
            return list(self._client.fetch_holidays(year, country_code))
        except NagerDateClientError as exc:
            self._logger.warning(
                "approval.follow_on.holiday_fallback year=%s country_code=%s detail=%s",
                year,
                country_code,
                exc,
            )
            return []


class ValidationPipeline:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.settings = get_settings()
        self.dataset_repository = DatasetRepository(session)
        self.validation_repository = ValidationRepository(session)
        self.review_needed_repository = ReviewNeededRepository(session)
        self.schema_validation_service = SchemaValidationService()
        self.duplicate_analysis_service = DuplicateAnalysisService()
        self.duplicate_resolution_service = DuplicateResolutionService()
        self.cleaned_dataset_repository = CleanedDatasetRepository(session)
        self.cleaned_dataset_service = CleanedDatasetService(
            self.dataset_repository,
            self.validation_repository,
            self.cleaned_dataset_repository,
        )
        approval_weather_client = _ApprovalWeatherClient(build_weather_client(), logging.getLogger("validation.approval.weather"))
        approval_holiday_client = _ApprovalHolidayClient(
            NagerDateClient(),
            logging.getLogger("validation.approval.holidays"),
        )
        self.forecast_training_service = ForecastTrainingService(
            cleaned_dataset_repository=self.cleaned_dataset_repository,
            forecast_model_repository=ForecastModelRepository(session),
            geomet_client=approval_weather_client,
            nager_date_client=approval_holiday_client,
            settings=self.settings,
            logger=logging.getLogger("validation.forecast_training"),
        )
        self.weekly_forecast_training_service = WeeklyForecastTrainingService(
            cleaned_dataset_repository=self.cleaned_dataset_repository,
            forecast_model_repository=ForecastModelRepository(session),
            geomet_client=approval_weather_client,
            nager_date_client=approval_holiday_client,
            settings=self.settings,
            logger=logging.getLogger("validation.weekly_forecast_training"),
        )
        self.forecast_service = ForecastService(
            cleaned_dataset_repository=self.cleaned_dataset_repository,
            forecast_run_repository=ForecastRunRepository(session),
            forecast_repository=ForecastRepository(session),
            forecast_model_repository=ForecastModelRepository(session),
            geomet_client=approval_weather_client,
            nager_date_client=approval_holiday_client,
            settings=self.settings,
            logger=logging.getLogger("validation.forecast"),
        )
        self.weekly_forecast_service = WeeklyForecastService(
            cleaned_dataset_repository=self.cleaned_dataset_repository,
            weekly_forecast_run_repository=WeeklyForecastRunRepository(session),
            weekly_forecast_repository=WeeklyForecastRepository(session),
            forecast_model_repository=ForecastModelRepository(session),
            geomet_client=approval_weather_client,
            nager_date_client=approval_holiday_client,
            settings=self.settings,
            logger=logging.getLogger("validation.weekly_forecast"),
        )
        self.approved_pipeline = ApprovedPipeline(
            self.cleaned_dataset_service,
            self.validation_repository,
            self.forecast_training_service,
            self.weekly_forecast_training_service,
            self.forecast_service,
            self.weekly_forecast_service,
            logging.getLogger("validation.approval"),
        )
        self.rejection_pipeline = RejectionPipeline(self.validation_repository)
        self.blocked_pipeline = BlockedOutcomePipeline(self.validation_repository, self.review_needed_repository)
        self.logger = logging.getLogger("validation")

    def run(
        self,
        ingestion_run_id: str,
        source_dataset_version_id: str,
        records: list[dict[str, object]],
        *,
        run_follow_on_jobs: bool = True,
    ) -> str:
        threshold = self.settings.duplicate_review_threshold_percentage
        self.logger.info(
            "validation.run.started ingestion_run_id=%s source_dataset_version_id=%s record_count=%s threshold_percentage=%s",
            ingestion_run_id,
            source_dataset_version_id,
            len(records),
            threshold,
        )
        validation_run = self.validation_repository.create_run(
            ingestion_run_id=ingestion_run_id,
            source_dataset_version_id=source_dataset_version_id,
            threshold_percentage=threshold,
        )

        schema_result = self.schema_validation_service.validate(records)
        self.validation_repository.record_validation_result(
            validation_run.validation_run_id,
            status=schema_result.status,
            required_field_check=schema_result.required_field_check,
            type_check=schema_result.type_check,
            format_check=schema_result.format_check,
            completeness_check=schema_result.completeness_check,
            issue_summary=schema_result.issue_summary,
        )
        self.logger.info(
            "validation.schema.completed validation_run_id=%s status=%s issue_summary=%s",
            validation_run.validation_run_id,
            schema_result.status,
            schema_result.issue_summary,
        )
        if not schema_result.passed:
            self.rejection_pipeline.reject(validation_run.validation_run_id, schema_result.issue_summary or "Rejected.")
            self.logger.info(
                "validation.run.completed validation_run_id=%s status=%s",
                validation_run.validation_run_id,
                "rejected",
            )
            return validation_run.validation_run_id

        duplicate_result = self.duplicate_analysis_service.analyze(records, threshold)
        analysis = self.validation_repository.record_duplicate_analysis(
            validation_run.validation_run_id,
            status=duplicate_result.status,
            total_record_count=duplicate_result.total_record_count,
            duplicate_record_count=duplicate_result.duplicate_record_count,
            duplicate_percentage=duplicate_result.duplicate_percentage,
            threshold_percentage=duplicate_result.threshold_percentage,
            duplicate_group_count=duplicate_result.duplicate_group_count,
            issue_summary=duplicate_result.issue_summary,
        )
        self.logger.info(
            "validation.duplicate_analysis.completed validation_run_id=%s status=%s duplicate_group_count=%s duplicate_percentage=%s",
            validation_run.validation_run_id,
            duplicate_result.status,
            duplicate_result.duplicate_group_count,
            duplicate_result.duplicate_percentage,
        )
        if duplicate_result.status == "review_needed":
            self.blocked_pipeline.hold_for_review(
                validation_run.validation_run_id,
                analysis.duplicate_analysis_id,
                duplicate_result.duplicate_percentage,
                duplicate_result.issue_summary or "Review needed due to duplicate threshold.",
            )
            self.logger.info(
                "validation.run.completed validation_run_id=%s status=%s",
                validation_run.validation_run_id,
                "review_needed",
            )
            return validation_run.validation_run_id

        try:
            self.logger.info(
                "validation.duplicate_resolution.started validation_run_id=%s duplicate_group_count=%s",
                validation_run.validation_run_id,
                duplicate_result.duplicate_group_count,
            )
            cleaned_records, resolutions = self.duplicate_resolution_service.resolve(records, duplicate_result.groups)
            self.logger.info(
                "validation.duplicate_resolution.completed validation_run_id=%s cleaned_record_count=%s resolution_count=%s",
                validation_run.validation_run_id,
                len(cleaned_records),
                len(resolutions),
            )
            stored_groups = self.validation_repository.record_duplicate_groups(
                analysis.duplicate_analysis_id,
                [
                    {
                        "group_key": resolution.group_key,
                        "source_record_count": resolution.source_record_count,
                        "resolution_status": resolution.resolution_status,
                        "cleaned_record_id": None,
                        "resolution_summary": resolution.resolution_summary,
                    }
                    for resolution in resolutions
                ],
            )
            self.logger.info(
                "validation.approval.started validation_run_id=%s cleaned_record_count=%s",
                validation_run.validation_run_id,
                len(cleaned_records),
            )
            cleaned_dataset_id = self.approved_pipeline.approve(
                source_name=self.settings.source_name,
                ingestion_run_id=ingestion_run_id,
                source_dataset_version_id=source_dataset_version_id,
                validation_run_id=validation_run.validation_run_id,
                cleaned_records=cleaned_records,
                duplicate_group_count=len(stored_groups),
                run_follow_on_jobs=run_follow_on_jobs,
            )
            self.logger.info(
                "validation.approval.completed validation_run_id=%s approved_dataset_version_id=%s",
                validation_run.validation_run_id,
                cleaned_dataset_id,
            )
            for stored_group in stored_groups:
                stored_group.cleaned_record_id = cleaned_dataset_id
            self.session.flush()
        except Exception as exc:
            self.logger.exception("validation.failed", extra={"validation_run_id": validation_run.validation_run_id})
            self.blocked_pipeline.fail(validation_run.validation_run_id, "storage", str(exc))
            self.logger.info(
                "validation.run.completed validation_run_id=%s status=%s",
                validation_run.validation_run_id,
                "failed",
            )
            return validation_run.validation_run_id

        self.logger.info(
            "validation.run.completed validation_run_id=%s status=%s",
            validation_run.validation_run_id,
            "approved",
        )
        return validation_run.validation_run_id
