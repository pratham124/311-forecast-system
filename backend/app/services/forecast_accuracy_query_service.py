from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from app.clients.actual_demand_client import ActualDemandClient
from app.clients.forecast_history_client import ForecastHistoryClient
from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
from app.repositories.evaluation_repository import EvaluationRepository
from app.repositories.forecast_accuracy_repository import ForecastAccuracyRepository
from app.schemas.forecast_accuracy import (
    ForecastAccuracyAlignedBucketRead,
    ForecastAccuracyMetrics,
    ForecastAccuracyQuery,
    ForecastAccuracyResponse,
)
from app.services.forecast_accuracy_alignment_service import ForecastAccuracyAlignmentService
from app.services.forecast_accuracy_metric_service import ForecastAccuracyMetricService
from app.services.forecast_accuracy_observability_service import ForecastAccuracyObservabilityService


@dataclass
class ForecastAccuracyQueryService:
    repository: ForecastAccuracyRepository
    cleaned_dataset_repository: CleanedDatasetRepository
    forecast_history_client: ForecastHistoryClient
    actual_demand_client: ActualDemandClient
    metric_service: ForecastAccuracyMetricService
    alignment_service: ForecastAccuracyAlignmentService
    observability_service: ForecastAccuracyObservabilityService
    source_name: str
    logger: logging.Logger | None = None

    def __post_init__(self) -> None:
        self.logger = self.logger or logging.getLogger("forecast_accuracy.query")

    def get_view(self, query: ForecastAccuracyQuery, claims: dict) -> ForecastAccuracyResponse:
        time_range_start, time_range_end = self._resolve_time_range(query)
        comparison_granularity = "hourly" if (time_range_end - time_range_start) <= timedelta(days=2) else "daily"
        approved_dataset = self.cleaned_dataset_repository.get_current_approved_dataset(self.source_name)
        request = self.repository.create_request(
            requested_by_actor="city_planner",
            requested_by_subject=str(claims.get("sub") or ""),
            source_cleaned_dataset_version_id=approved_dataset.dataset_version_id if approved_dataset is not None else None,
            source_forecast_version_id=None,
            source_evaluation_result_id=None,
            forecast_product_name="daily_1_day",
            comparison_granularity=comparison_granularity,
            time_range_start=time_range_start,
            time_range_end=time_range_end,
            service_category=query.service_category,
            status="running",
            correlation_id=None,
        )
        request.correlation_id = request.forecast_accuracy_request_id
        self.observability_service.log_event(
            "forecast_accuracy.request_started",
            forecast_accuracy_request_id=request.forecast_accuracy_request_id,
            comparison_granularity=comparison_granularity,
        )
        forecast_rows, source_forecast_version_id = self.forecast_history_client.list_forecast_rows(
            time_range_start=time_range_start,
            time_range_end=time_range_end,
            service_category=query.service_category,
            comparison_granularity=comparison_granularity,
        )
        if not forecast_rows:
            return self._finalize_unavailable(
                request_id=request.forecast_accuracy_request_id,
                time_range_start=time_range_start,
                time_range_end=time_range_end,
                comparison_granularity=comparison_granularity,
                service_category=query.service_category,
                status="forecast_missing",
                message="Historical forecast data is unavailable for the selected scope.",
            )
        actual_rows = self.actual_demand_client.list_actual_rows(
            time_range_start=time_range_start,
            time_range_end=time_range_end,
            service_category=query.service_category,
            comparison_granularity=comparison_granularity,
        )
        if not actual_rows:
            return self._finalize_unavailable(
                request_id=request.forecast_accuracy_request_id,
                time_range_start=time_range_start,
                time_range_end=time_range_end,
                comparison_granularity=comparison_granularity,
                service_category=query.service_category,
                status="actual_missing",
                message="Actual demand data is unavailable for the selected scope.",
                source_forecast_version_id=source_forecast_version_id,
            )
        try:
            alignment = self.alignment_service.align(
                forecast_rows=forecast_rows,
                actual_rows=actual_rows,
            )
        except ValueError as exc:
            return self._finalize_unavailable(
                request_id=request.forecast_accuracy_request_id,
                time_range_start=time_range_start,
                time_range_end=time_range_end,
                comparison_granularity=comparison_granularity,
                service_category=query.service_category,
                status="alignment_unavailable",
                message=str(exc),
                source_forecast_version_id=source_forecast_version_id,
            )
        metric_status, metrics, evaluation_result_id, metric_message = self.metric_service.resolve_metrics(
            aligned_buckets=alignment.aligned_buckets,
            time_range_start=time_range_start,
            time_range_end=time_range_end,
            service_category=query.service_category,
        )
        self.repository.upsert_metric_resolution(
            forecast_accuracy_request_id=request.forecast_accuracy_request_id,
            resolution_status=metric_status,
            metric_names=["mae", "rmse", "mape"],
            metric_values=metrics,
            source_evaluation_result_id=evaluation_result_id,
            status_message=metric_message,
        )
        view_status = "rendered_with_metrics" if metrics is not None else "rendered_without_metrics"
        status_message = None if metrics is not None else (metric_message or "Metrics are unavailable for this comparison window.")
        result = self.repository.create_result(
            forecast_accuracy_request_id=request.forecast_accuracy_request_id,
            view_status=view_status,
            metric_resolution_status=metric_status,
            status_message=status_message,
            aligned_bucket_count=len(alignment.aligned_buckets),
            excluded_bucket_count=alignment.excluded_bucket_count,
        )
        self.repository.replace_aligned_buckets(result.forecast_accuracy_result_id, alignment.aligned_buckets)
        self.repository.finalize_request(
            request.forecast_accuracy_request_id,
            status=view_status,
            source_forecast_version_id=source_forecast_version_id,
            source_evaluation_result_id=evaluation_result_id,
        )
        self.observability_service.log_event(
            "forecast_accuracy.prepared",
            forecast_accuracy_request_id=request.forecast_accuracy_request_id,
            view_status=view_status,
            metric_resolution_status=metric_status,
            aligned_bucket_count=len(alignment.aligned_buckets),
            excluded_bucket_count=alignment.excluded_bucket_count,
        )
        return ForecastAccuracyResponse(
            forecastAccuracyRequestId=request.forecast_accuracy_request_id,
            forecastAccuracyResultId=result.forecast_accuracy_result_id,
            correlationId=request.correlation_id,
            timeRangeStart=time_range_start,
            timeRangeEnd=time_range_end,
            serviceCategory=query.service_category,
            forecastProductName="daily_1_day",
            comparisonGranularity=comparison_granularity,
            viewStatus=view_status,
            metricResolutionStatus=metric_status,
            statusMessage=status_message,
            metrics=ForecastAccuracyMetrics(**metrics) if metrics is not None else None,
            alignedBuckets=[ForecastAccuracyAlignedBucketRead.model_validate(bucket) for bucket in alignment.aligned_buckets],
        )

    def _finalize_unavailable(
        self,
        *,
        request_id: str,
        time_range_start: datetime,
        time_range_end: datetime,
        comparison_granularity: str,
        service_category: str | None,
        status: str,
        message: str,
        source_forecast_version_id: str | None = None,
    ) -> ForecastAccuracyResponse:
        view_status = "error" if status == "alignment_unavailable" else "unavailable"
        result = self.repository.create_result(
            forecast_accuracy_request_id=request_id,
            view_status=view_status,
            metric_resolution_status=None,
            status_message=message,
            aligned_bucket_count=0,
            excluded_bucket_count=0,
        )
        self.repository.finalize_request(
            request_id,
            status=status,
            source_forecast_version_id=source_forecast_version_id,
            failure_reason=message,
        )
        self.observability_service.log_event(
            "forecast_accuracy.unavailable",
            forecast_accuracy_request_id=request_id,
            status=status,
            detail=message,
        )
        return ForecastAccuracyResponse(
            forecastAccuracyRequestId=request_id,
            forecastAccuracyResultId=result.forecast_accuracy_result_id,
            correlationId=None,
            timeRangeStart=time_range_start,
            timeRangeEnd=time_range_end,
            serviceCategory=service_category,
            forecastProductName="daily_1_day",
            comparisonGranularity=comparison_granularity,
            viewStatus=view_status,
            metricResolutionStatus=None,
            statusMessage=message,
            metrics=None,
            alignedBuckets=[],
        )

    def _resolve_time_range(self, query: ForecastAccuracyQuery) -> tuple[datetime, datetime]:
        if query.time_range_start and query.time_range_end:
            return query.time_range_start.astimezone(timezone.utc), query.time_range_end.astimezone(timezone.utc)
        tz = ZoneInfo("America/Edmonton")
        now_local = datetime.now(tz)
        end_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
        start_local = end_local - timedelta(days=30)
        return start_local.astimezone(timezone.utc), end_local.astimezone(timezone.utc)
