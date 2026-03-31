from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone
import logging
import uuid

from app.core.logging import (
    summarize_historical_demand_failure,
    summarize_historical_demand_no_data,
    summarize_historical_demand_success,
    summarize_historical_demand_warning,
)
from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
from app.repositories.historical_demand_repository import HistoricalDemandRepository
from app.schemas.forecast_visualization import VisualizationPoint
from app.schemas.historical_demand import (
    HistoricalDemandQueryRequest,
    HistoricalDemandRenderEvent,
    HistoricalDemandResponseRead,
    HistoricalDemandSummaryPointRead,
    SelectedFiltersRead,
)
from app.services.historical_context_service import HistoricalContextService
from app.services.historical_warning_service import HistoricalWarningService


class HistoricalDemandService:
    def __init__(self, cleaned_dataset_repository: CleanedDatasetRepository, source_name: str) -> None:
        self.cleaned_dataset_repository = cleaned_dataset_repository
        self.source_name = source_name

    def build_series(
        self,
        *,
        boundary: datetime,
        granularity: str,
        service_categories: list[str] | None = None,
        excluded_service_categories: list[str] | None = None,
        service_category: str | None = None,
    ) -> tuple[list[VisualizationPoint], str | None, datetime, datetime]:
        boundary_utc = boundary.astimezone(timezone.utc) if boundary.tzinfo else boundary.replace(tzinfo=timezone.utc)
        start = boundary_utc - timedelta(days=7)
        records = self.cleaned_dataset_repository.list_current_cleaned_records(
            self.source_name,
            start_time=start,
            end_time=boundary_utc,
        )
        current_dataset = self.cleaned_dataset_repository.get_current_approved_dataset(self.source_name)
        selected_categories = service_categories or ([service_category] if service_category else [])
        excluded_categories = excluded_service_categories or []
        grouped: dict[datetime, float] = defaultdict(float)
        for record in records:
            category = str(record.get("category"))
            if selected_categories and category not in selected_categories:
                continue
            if excluded_categories and category in excluded_categories:
                continue
            timestamp = self._parse_timestamp(str(record.get("requested_at", "")))
            if timestamp is None:
                continue
            bucket_time = timestamp.replace(minute=0, second=0, microsecond=0)
            if granularity == "daily":
                bucket_time = bucket_time.replace(hour=0)
            grouped[bucket_time] += 1.0
        series = [VisualizationPoint(timestamp=key, value=value) for key, value in sorted(grouped.items())]
        dataset_version_id = current_dataset.dataset_version_id if current_dataset is not None else None
        return series, dataset_version_id, start, boundary_utc

    @staticmethod
    def _parse_timestamp(value: str) -> datetime | None:
        if not value:
            return None
        normalized = value.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            return None
        return parsed.astimezone(timezone.utc) if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


@dataclass
class HistoricalDemandAnalysisService:
    historical_demand_repository: HistoricalDemandRepository
    cleaned_dataset_repository: CleanedDatasetRepository
    context_service: HistoricalContextService
    warning_service: HistoricalWarningService
    source_name: str
    logger: logging.Logger | None = None

    def __post_init__(self) -> None:
        self.logger = self.logger or logging.getLogger("historical_demand")

    def execute_query(self, payload: HistoricalDemandQueryRequest) -> HistoricalDemandResponseRead:
        filters = SelectedFiltersRead(
            serviceCategory=payload.service_category,
            timeRangeStart=payload.time_range_start,
            timeRangeEnd=payload.time_range_end,
            geographyLevel=payload.geography_level,
            geographyValue=payload.geography_value,
        )
        self._ensure_supported_geography(payload.geography_level)
        records = self.cleaned_dataset_repository.list_current_cleaned_records(self.source_name)
        preview_records = self._filter_records(records, payload)
        warning = self.warning_service.evaluate(
            candidate_record_count=len(preview_records),
            time_range_start=payload.time_range_start,
            time_range_end=payload.time_range_end,
            service_category=payload.service_category,
            geography_level=payload.geography_level,
            proceed_after_warning=payload.proceed_after_warning,
        )
        if warning is not None and not warning.acknowledged:
            analysis_request_id = f"warning-{uuid.uuid4()}"
            self.logger.info(
                "%s",
                summarize_historical_demand_warning(
                    "historical_demand.warning_shown",
                    analysis_request_id=analysis_request_id,
                    matched_record_count=len(preview_records),
                    filters=filters.model_dump(by_alias=True, mode="json"),
                ),
            )
            return HistoricalDemandResponseRead(
                analysisRequestId=analysis_request_id,
                filters=filters,
                warning=warning,
                outcomeStatus="no_data",
                message=warning.message,
                summary="Historical demand warning shown before retrieval.",
            )
        try:
            dataset_version_id = self.context_service.require_approved_dataset_id()
            request = self.historical_demand_repository.create_request(
                requested_by_actor="city_planner",
                source_cleaned_dataset_version_id=dataset_version_id,
                service_category_filter=payload.service_category,
                time_range_start=payload.time_range_start,
                time_range_end=payload.time_range_end,
                geography_filter_type=payload.geography_level,
                geography_filter_value=payload.geography_value,
                warning_status="acknowledged" if warning and warning.acknowledged else "not_needed",
            )
            self.logger.info(
                "%s",
                summarize_historical_demand_success(
                    "historical_demand.request_started",
                    analysis_request_id=request.analysis_request_id,
                    filters=filters.model_dump(by_alias=True, mode="json"),
                ),
            )
            if not preview_records:
                message = "No historical demand data matches the selected filters."
                self.historical_demand_repository.finalize_request(request.analysis_request_id, status="no_data")
                self.historical_demand_repository.upsert_outcome(
                    analysis_request_id=request.analysis_request_id,
                    outcome_type="no_data",
                    warning_acknowledged=bool(warning and warning.acknowledged),
                    message=message,
                )
                self.logger.info(
                    "%s",
                    summarize_historical_demand_no_data(
                        "historical_demand.no_data",
                        analysis_request_id=request.analysis_request_id,
                        filters=filters.model_dump(by_alias=True, mode="json"),
                    ),
                )
                return HistoricalDemandResponseRead(
                    analysisRequestId=request.analysis_request_id,
                    filters=filters,
                    warning=warning,
                    outcomeStatus="no_data",
                    message=message,
                    summary=message,
                )
            granularity = self._select_granularity(payload.time_range_start, payload.time_range_end)
            summary_points = self._aggregate(preview_records, granularity, payload.geography_level)
            result = self.historical_demand_repository.create_result(
                analysis_request_id=request.analysis_request_id,
                source_cleaned_dataset_version_id=dataset_version_id,
                aggregation_granularity=granularity,
                result_mode="chart_and_table",
                service_category_filter=payload.service_category,
                time_range_start=payload.time_range_start,
                time_range_end=payload.time_range_end,
                geography_filter_type=payload.geography_level,
                geography_filter_value=payload.geography_value,
                record_count=len(preview_records),
            )
            self.historical_demand_repository.replace_summary_points(result.analysis_result_id, summary_points)
            self.historical_demand_repository.finalize_request(
                request.analysis_request_id,
                status="success",
                warning_status="acknowledged" if warning and warning.acknowledged else "not_needed",
            )
            self.historical_demand_repository.upsert_outcome(
                analysis_request_id=request.analysis_request_id,
                outcome_type="success",
                warning_acknowledged=bool(warning and warning.acknowledged),
                message="Historical demand data prepared for visualization.",
            )
            self.logger.info(
                "%s",
                summarize_historical_demand_success(
                    "historical_demand.retrieval_succeeded",
                    analysis_request_id=request.analysis_request_id,
                    aggregation_granularity=granularity,
                    summary_point_count=len(summary_points),
                    record_count=len(preview_records),
                ),
            )
            return HistoricalDemandResponseRead(
                analysisRequestId=request.analysis_request_id,
                filters=filters,
                warning=warning,
                aggregationGranularity=granularity,
                resultMode="chart_and_table",
                summaryPoints=[HistoricalDemandSummaryPointRead.model_validate(point) for point in summary_points],
                outcomeStatus="success",
                message="Historical demand data loaded successfully.",
                summary="Historical demand data prepared for visualization.",
            )
        except Exception as exc:
            return self._build_failure_response(filters, warning, str(exc))

    def record_render_event(self, analysis_request_id: str, payload: HistoricalDemandRenderEvent) -> None:
        request = self.historical_demand_repository.require_request(analysis_request_id)
        if payload.render_status == "render_failed":
            self.historical_demand_repository.finalize_request(
                analysis_request_id,
                status="render_failed",
                failure_reason=payload.failure_reason,
            )
            self.historical_demand_repository.upsert_outcome(
                analysis_request_id=analysis_request_id,
                outcome_type="render_failed",
                warning_acknowledged=request.warning_status == "acknowledged",
                message=payload.failure_reason or "Historical demand rendering failed.",
            )
            self.logger.info(
                "%s",
                summarize_historical_demand_failure(
                    "historical_demand.render_failed",
                    analysis_request_id=analysis_request_id,
                    failure_reason=payload.failure_reason,
                ),
            )
            return
        self.historical_demand_repository.upsert_outcome(
            analysis_request_id=analysis_request_id,
            outcome_type="success",
            warning_acknowledged=request.warning_status == "acknowledged",
            message="Historical demand visualization rendered successfully.",
        )
        self.logger.info(
            "%s",
            summarize_historical_demand_success(
                "historical_demand.render_succeeded",
                analysis_request_id=analysis_request_id,
            ),
        )

    def _build_failure_response(self, filters: SelectedFiltersRead, warning, failure_reason: str) -> HistoricalDemandResponseRead:
        request = self.historical_demand_repository.create_request(
            requested_by_actor="city_planner",
            source_cleaned_dataset_version_id=None,
            service_category_filter=filters.service_category,
            time_range_start=filters.time_range_start,
            time_range_end=filters.time_range_end,
            geography_filter_type=filters.geography_level,
            geography_filter_value=filters.geography_value,
            warning_status="acknowledged" if warning and warning.acknowledged else "not_needed",
        )
        self.historical_demand_repository.finalize_request(
            request.analysis_request_id,
            status="retrieval_failed",
            failure_reason=failure_reason,
        )
        self.historical_demand_repository.upsert_outcome(
            analysis_request_id=request.analysis_request_id,
            outcome_type="retrieval_failed",
            warning_acknowledged=bool(warning and warning.acknowledged),
            message=failure_reason,
        )
        self.logger.info(
            "%s",
            summarize_historical_demand_failure(
                "historical_demand.retrieval_failed",
                analysis_request_id=request.analysis_request_id,
                failure_reason=failure_reason,
            ),
        )
        return HistoricalDemandResponseRead(
            analysisRequestId=request.analysis_request_id,
            filters=filters,
            warning=warning,
            outcomeStatus="retrieval_failed",
            message="Historical demand data could not be retrieved.",
            summary=failure_reason,
        )

    def _ensure_supported_geography(self, geography_level: str | None) -> None:
        if geography_level is None:
            return
        supported_levels = self.context_service.get_context().supported_geography_levels
        if geography_level not in supported_levels:
            raise LookupError("Requested geography level is not supported by the approved historical dataset")

    def _filter_records(self, records: list[dict[str, object]], payload: HistoricalDemandQueryRequest) -> list[dict[str, object]]:
        filtered: list[dict[str, object]] = []
        for record in records:
            timestamp = HistoricalDemandService._parse_timestamp(str(record.get("requested_at", "")))
            if timestamp is None:
                continue
            if timestamp < payload.time_range_start.astimezone(UTC):
                continue
            if timestamp > payload.time_range_end.astimezone(UTC):
                continue
            category = str(record.get("category", "")).strip()
            if payload.service_category and category != payload.service_category:
                continue
            if payload.geography_level and payload.geography_value:
                geography_value = self.context_service.extract_geography_value(record, payload.geography_level)
                if geography_value != payload.geography_value:
                    continue
            filtered.append(record)
        return filtered

    def _select_granularity(self, start: datetime, end: datetime) -> str:
        span_days = max((end - start).days, 0)
        if span_days <= 31:
            return "daily"
        if span_days <= 180:
            return "weekly"
        return "monthly"

    def _aggregate(self, records: list[dict[str, object]], granularity: str, geography_level: str | None) -> list[dict[str, object]]:
        grouped: dict[tuple[datetime, str, str | None], int] = defaultdict(int)
        for record in records:
            timestamp = HistoricalDemandService._parse_timestamp(str(record.get("requested_at", "")))
            if timestamp is None:
                continue
            bucket_start = self._bucket_start(timestamp, granularity)
            category = str(record.get("category", "")).strip() or "Unknown"
            geography_key = self.context_service.extract_geography_value(record, geography_level) if geography_level else None
            grouped[(bucket_start, category, geography_key)] += 1
        points: list[dict[str, object]] = []
        for (bucket_start, category, geography_key), count in sorted(grouped.items(), key=lambda item: item[0]):
            points.append(
                {
                    "bucketStart": bucket_start,
                    "bucketEnd": self._bucket_end(bucket_start, granularity),
                    "serviceCategory": category,
                    "geographyKey": geography_key,
                    "demandCount": count,
                }
            )
        return points

    def _bucket_start(self, timestamp: datetime, granularity: str) -> datetime:
        if granularity == "monthly":
            return timestamp.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if granularity == "weekly":
            start = timestamp - timedelta(days=timestamp.weekday())
            return start.replace(hour=0, minute=0, second=0, microsecond=0)
        return timestamp.replace(hour=0, minute=0, second=0, microsecond=0)

    def _bucket_end(self, bucket_start: datetime, granularity: str) -> datetime:
        if granularity == "monthly":
            if bucket_start.month == 12:
                return bucket_start.replace(year=bucket_start.year + 1, month=1)
            return bucket_start.replace(month=bucket_start.month + 1)
        if granularity == "weekly":
            return bucket_start + timedelta(days=7)
        return bucket_start + timedelta(days=1)
