from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timezone

from app.core.demand_comparison_observability import (
    summarize_demand_comparison_failure,
    summarize_demand_comparison_success,
    summarize_demand_comparison_warning,
)
from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
from app.repositories.demand_comparison_repository import DemandComparisonRepository
from app.repositories.forecast_repository import ForecastRepository
from app.repositories.weekly_forecast_repository import WeeklyForecastRepository
from app.schemas.demand_comparison_api import (
    DemandComparisonDataResponse,
    DemandComparisonFailureResponse,
    DemandComparisonQueryRequest,
    DemandComparisonWarningResponse,
    DemandComparisonSeriesRead,
    HighVolumeWarning,
    MissingCombinationRead,
    SelectedComparisonFilters,
)
from app.services.demand_comparison_context_service import DemandComparisonContextService
from app.services.demand_comparison_outcomes import build_terminal_message, map_terminal_outcome
from app.services.demand_comparison_result_builder import DemandComparisonAlignmentError, DemandComparisonResultBuilder
from app.services.demand_comparison_source_resolution import AlignmentResolutionError, DemandComparisonSourceResolver
from app.services.demand_comparison_warning_service import DemandComparisonWarningService


@dataclass
class DemandComparisonService:
    comparison_repository: DemandComparisonRepository
    cleaned_dataset_repository: CleanedDatasetRepository
    forecast_repository: ForecastRepository
    weekly_forecast_repository: WeeklyForecastRepository
    context_service: DemandComparisonContextService
    warning_service: DemandComparisonWarningService
    source_resolver: DemandComparisonSourceResolver
    result_builder: DemandComparisonResultBuilder
    logger: logging.Logger | None = None

    def __post_init__(self) -> None:
        self.logger = self.logger or logging.getLogger("demand_comparison")

    def execute_query(self, payload: DemandComparisonQueryRequest, claims: dict):
        filters = SelectedComparisonFilters(
            serviceCategories=payload.service_categories,
            geographyLevel=payload.geography_level,
            geographyValues=payload.geography_values,
            timeRangeStart=payload.time_range_start,
            timeRangeEnd=payload.time_range_end,
        )
        self._ensure_supported_filters(payload)
        source_cleaned_dataset_version_id, source_resolution = self.source_resolver.resolve(
            time_range_start=payload.time_range_start,
            time_range_end=payload.time_range_end,
            geography_level=payload.geography_level,
        )
        warning = self.warning_service.evaluate(
            service_category_count=len(payload.service_categories),
            geography_count=len(payload.geography_values),
            time_range_start=payload.time_range_start,
            time_range_end=payload.time_range_end,
            proceed_after_warning=payload.proceed_after_warning,
        )
        if warning is not None and not warning.acknowledged:
            request = self.comparison_repository.create_request(
                requested_by_actor="city_planner",
                requested_by_subject=str(claims.get("sub") or ""),
                source_cleaned_dataset_version_id=source_cleaned_dataset_version_id,
                source_forecast_version_id=source_resolution.source_forecast_version_id if source_resolution else None,
                source_weekly_forecast_version_id=source_resolution.source_weekly_forecast_version_id if source_resolution else None,
                forecast_product_name=source_resolution.forecast_product if source_resolution else None,
                forecast_granularity=source_resolution.forecast_granularity if source_resolution else None,
                geography_level=payload.geography_level,
                service_category_count=len(payload.service_categories),
                geography_value_count=len(payload.geography_values),
                time_range_start=payload.time_range_start,
                time_range_end=payload.time_range_end,
                warning_status="shown",
            )
            self.comparison_repository.upsert_outcome(
                comparison_request_id=request.comparison_request_id,
                outcome_type="high_volume_warning",
                warning_acknowledged=False,
                message=warning.message or "Large comparison request warning shown.",
            )
            self.logger.info(
                "%s",
                summarize_demand_comparison_warning(
                    "demand_comparison.warning_required",
                    comparison_request_id=request.comparison_request_id,
                    filters=filters.model_dump(by_alias=True, mode="json"),
                ),
            )
            return DemandComparisonWarningResponse(
                comparisonRequestId=request.comparison_request_id,
                filters=filters,
                outcomeStatus="warning_required",
                warning=warning,
                message=warning.message or "Large comparison request warning shown.",
                summary="Comparison retrieval has not started.",
            )

        request = self.comparison_repository.create_request(
            requested_by_actor="city_planner",
            requested_by_subject=str(claims.get("sub") or ""),
            source_cleaned_dataset_version_id=source_cleaned_dataset_version_id,
            source_forecast_version_id=source_resolution.source_forecast_version_id if source_resolution else None,
            source_weekly_forecast_version_id=source_resolution.source_weekly_forecast_version_id if source_resolution else None,
            forecast_product_name=source_resolution.forecast_product if source_resolution else None,
            forecast_granularity=source_resolution.forecast_granularity if source_resolution else None,
            geography_level=payload.geography_level,
            service_category_count=len(payload.service_categories),
            geography_value_count=len(payload.geography_values),
            time_range_start=payload.time_range_start,
            time_range_end=payload.time_range_end,
            warning_status="acknowledged" if warning else "not_needed",
        )
        try:
            historical_records = self._load_historical_records(payload)
        except Exception as exc:
            return self._build_failure_response(request.comparison_request_id, filters, "historical_retrieval_failed", str(exc), warning)
        try:
            forecast_records = self._load_forecast_records(payload, source_resolution)
        except Exception as exc:
            return self._build_failure_response(request.comparison_request_id, filters, "forecast_retrieval_failed", str(exc), warning)
        try:
            self.source_resolver.ensure_alignment_supported(
                comparison_granularity=source_resolution.comparison_granularity if source_resolution else None,
                geography_level=payload.geography_level,
                forecast_has_geography=(not forecast_records) or any(record.get("geography_key") is not None for record in forecast_records),
            )
            series, missing_combinations, uncovered_interval = self.result_builder.build(
                historical_records=historical_records,
                forecast_records=forecast_records,
                categories=payload.service_categories,
                geography_level=payload.geography_level,
                geography_values=payload.geography_values,
                comparison_granularity=source_resolution.comparison_granularity if source_resolution else "daily",
            )
        except (AlignmentResolutionError, DemandComparisonAlignmentError) as exc:
            return self._build_failure_response(request.comparison_request_id, filters, "alignment_failed", str(exc), warning)

        outcome_status = map_terminal_outcome(
            has_historical_data=bool(historical_records),
            has_forecast_data=bool(forecast_records),
            missing_combinations=missing_combinations,
        )
        message = build_terminal_message(
            outcome_status,
            missing_count=len(missing_combinations),
            uncovered_historical_interval=uncovered_interval if outcome_status == "forecast_only" else None,
        )
        result = self.comparison_repository.create_result(
            comparison_request_id=request.comparison_request_id,
            source_cleaned_dataset_version_id=source_cleaned_dataset_version_id if outcome_status != "forecast_only" else None,
            source_forecast_version_id=source_resolution.source_forecast_version_id if source_resolution else None,
            source_weekly_forecast_version_id=source_resolution.source_weekly_forecast_version_id if source_resolution else None,
            forecast_product_name=source_resolution.forecast_product if source_resolution else None,
            forecast_granularity=source_resolution.forecast_granularity if source_resolution else None,
            result_mode="chart_and_table",
            comparison_granularity=source_resolution.comparison_granularity if source_resolution else "daily",
            status=outcome_status,
        )
        self.comparison_repository.replace_series_points(result.comparison_result_id, self.result_builder.flatten_points(series))
        self.comparison_repository.replace_missing_combinations(
            result.comparison_result_id,
            self.result_builder.flatten_missing_combinations(missing_combinations),
        )
        self.comparison_repository.finalize_request(
            request.comparison_request_id,
            status=outcome_status,
            warning_status="acknowledged" if warning else "not_needed",
        )
        self.comparison_repository.upsert_outcome(
            comparison_request_id=request.comparison_request_id,
            outcome_type=outcome_status,
            warning_acknowledged=bool(warning),
            message=message,
        )
        self.logger.info(
            "%s",
            summarize_demand_comparison_success(
                "demand_comparison.completed",
                comparison_request_id=request.comparison_request_id,
                outcome_status=outcome_status,
                historical_series=bool(historical_records),
                forecast_series=bool(forecast_records),
                missing_combination_count=len(missing_combinations),
            ),
        )
        return DemandComparisonDataResponse(
            comparisonRequestId=request.comparison_request_id,
            filters=filters,
            outcomeStatus=outcome_status,
            resultMode="chart_and_table",
            comparisonGranularity=source_resolution.comparison_granularity if source_resolution else "daily",
            forecastProduct=source_resolution.forecast_product if source_resolution else None,
            forecastGranularity=source_resolution.forecast_granularity if source_resolution else None,
            sourceCleanedDatasetVersionId=source_cleaned_dataset_version_id if outcome_status != "forecast_only" else None,
            sourceForecastVersionId=source_resolution.source_forecast_version_id if source_resolution else None,
            sourceWeeklyForecastVersionId=source_resolution.source_weekly_forecast_version_id if source_resolution else None,
            series=[DemandComparisonSeriesRead.model_validate(self._series_payload(item)) for item in series],
            missingCombinations=[MissingCombinationRead.model_validate(self._missing_payload(item)) for item in missing_combinations],
            message=message,
            summary="Demand comparison prepared for visualization.",
        )

    def _build_failure_response(
        self,
        comparison_request_id: str,
        filters: SelectedComparisonFilters,
        outcome_status: str,
        failure_reason: str,
        warning: HighVolumeWarning | None,
    ) -> DemandComparisonFailureResponse:
        message = build_terminal_message(outcome_status)
        self.comparison_repository.finalize_request(
            comparison_request_id,
            status=outcome_status,
            warning_status="acknowledged" if warning else "not_needed",
            failure_reason=failure_reason,
        )
        self.comparison_repository.upsert_outcome(
            comparison_request_id=comparison_request_id,
            outcome_type=outcome_status,
            warning_acknowledged=bool(warning),
            message=failure_reason,
        )
        self.logger.info(
            "%s",
            summarize_demand_comparison_failure(
                "demand_comparison.failed",
                comparison_request_id=comparison_request_id,
                outcome_status=outcome_status,
                failure_reason=failure_reason,
            ),
        )
        return DemandComparisonFailureResponse(
            comparisonRequestId=comparison_request_id,
            filters=filters,
            outcomeStatus=outcome_status,
            message=message,
            summary=failure_reason,
        )

    def _ensure_supported_filters(self, payload: DemandComparisonQueryRequest) -> None:
        context = self.context_service.get_context()
        unsupported_categories = set(payload.service_categories) - set(context.service_categories)
        if unsupported_categories:
            raise LookupError("One or more selected service categories are not available")
        if payload.geography_level and payload.geography_level not in context.geography_levels:
            raise LookupError("Requested geography level is not supported")
        if payload.geography_values:
            supported_values = set(context.geography_options.get(payload.geography_level or "", []))
            if not set(payload.geography_values).issubset(supported_values):
                raise LookupError("One or more selected geography values are not available")

    def _load_historical_records(self, payload: DemandComparisonQueryRequest) -> list[dict[str, object]]:
        records = self.cleaned_dataset_repository.list_current_cleaned_records(
            self.context_service.source_name,
            start_time=payload.time_range_start,
            end_time=payload.time_range_end.astimezone(timezone.utc),
        )
        filtered: list[dict[str, object]] = []
        for record in records:
            category = str(record.get("category", "")).strip()
            if category not in payload.service_categories:
                continue
            if payload.geography_values:
                geography_value = self.context_service.extract_geography_value(record, payload.geography_level)
                if geography_value not in payload.geography_values:
                    continue
            filtered.append(record)
        return filtered

    def _load_forecast_records(self, payload: DemandComparisonQueryRequest, source_resolution) -> list[dict[str, object]]:
        def normalize_dt(value):
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
            return value.astimezone(timezone.utc)

        if source_resolution is None:
            return []
        if source_resolution.forecast_product == "daily_1_day":
            buckets = self.forecast_repository.list_buckets(source_resolution.source_forecast_version_id or "")
            rows = [
                {
                    "bucket_start": bucket.bucket_start,
                    "bucket_end": bucket.bucket_end,
                    "service_category": bucket.service_category,
                    "geography_key": bucket.geography_key,
                    "point_forecast": float(bucket.point_forecast),
                }
                for bucket in buckets
                if bucket.service_category in payload.service_categories
                and (not payload.geography_values or bucket.geography_key in payload.geography_values)
                and normalize_dt(bucket.bucket_start) >= payload.time_range_start
                and normalize_dt(bucket.bucket_end) <= payload.time_range_end
            ]
            return rows
        buckets = self.weekly_forecast_repository.list_buckets(source_resolution.source_weekly_forecast_version_id or "")
        return [
            {
                "forecast_date_local": bucket.forecast_date_local,
                "service_category": bucket.service_category,
                "geography_key": bucket.geography_key,
                "point_forecast": float(bucket.point_forecast),
            }
            for bucket in buckets
            if bucket.service_category in payload.service_categories
            and (not payload.geography_values or bucket.geography_key in payload.geography_values)
            and payload.time_range_start.date() <= bucket.forecast_date_local <= payload.time_range_end.date()
        ]

    @staticmethod
    def _series_payload(series) -> dict[str, object]:
        return {
            "seriesType": series.series_type,
            "serviceCategory": series.service_category,
            "geographyKey": series.geography_key,
            "points": [
                {
                    "bucketStart": point.bucket_start,
                    "bucketEnd": point.bucket_end,
                    "value": point.value,
                }
                for point in series.points
            ],
        }

    @staticmethod
    def _missing_payload(item) -> dict[str, object]:
        return {
            "serviceCategory": item.service_category,
            "geographyKey": item.geography_key,
            "missingSource": item.missing_source,
            "message": item.message,
        }
