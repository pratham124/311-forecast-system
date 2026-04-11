from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from app.core.config import Settings
from app.models import VisualizationLoadRecord
from app.schemas.forecast_visualization import CategoryFilter, ForecastConfidenceRead, ForecastVisualizationRead, ServiceCategoryOptionsRead, StatusMessage, VisualizationRenderEvent
from app.services.forecast_confidence_service import (
    ForecastConfidenceService,
    build_unavailable_confidence_read,
    confidence_signal_resolution_status,
)
from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
from app.repositories.forecast_repository import ForecastRepository
from app.repositories.visualization_repository import VisualizationRepository
from app.repositories.weekly_forecast_repository import WeeklyForecastRepository
from app.services.forecast_visualization_sources import ForecastVisualizationSourceService, NormalizedForecastSource
from app.services.historical_demand_service import HistoricalDemandService
from app.services.visualization_snapshot_service import VisualizationSnapshotService


def normalize_service_categories(service_categories: list[str] | None) -> list[str]:
    if not service_categories:
        return []
    seen: dict[str, None] = {}
    for category in service_categories:
        token = category.strip()
        if token:
            seen[token] = None
    return sorted(seen.keys())


def serialize_category_filter(service_categories: list[str] | None, excluded_service_categories: list[str] | None = None) -> str | None:
    normalized = normalize_service_categories(service_categories)
    normalized_excluded = normalize_service_categories(excluded_service_categories)
    if normalized_excluded:
        return f"exclude:{','.join(normalized_excluded)}"
    if not normalized:
        return None
    return ','.join(normalized)


class ForecastVisualizationService:
    def __init__(
        self,
        *,
        cleaned_dataset_repository: CleanedDatasetRepository,
        forecast_repository: ForecastRepository,
        weekly_forecast_repository: WeeklyForecastRepository,
        visualization_repository: VisualizationRepository,
        historical_demand_service: HistoricalDemandService,
        source_service: ForecastVisualizationSourceService,
        snapshot_service: VisualizationSnapshotService,
        settings: Settings,
        logger: logging.Logger,
        confidence_service: ForecastConfidenceService | None = None,
    ) -> None:
        self.cleaned_dataset_repository = cleaned_dataset_repository
        self.forecast_repository = forecast_repository
        self.weekly_forecast_repository = weekly_forecast_repository
        self.visualization_repository = visualization_repository
        self.historical_demand_service = historical_demand_service
        self.source_service = source_service
        self.snapshot_service = snapshot_service
        self.settings = settings
        self.logger = logger
        self.confidence_service = confidence_service or ForecastConfidenceService(
            surge_state_repository=None,
            surge_evaluation_repository=None,
            settings=settings,
            logger=logger,
        )

    def get_current_visualization(
        self,
        *,
        forecast_product: str,
        service_categories: list[str] | None = None,
        excluded_service_categories: list[str] | None = None,
        service_category: str | None = None,
    ) -> ForecastVisualizationRead:
        normalized_categories = normalize_service_categories(service_categories or ([service_category] if service_category else []))
        normalized_excluded_categories = normalize_service_categories(excluded_service_categories)
        filter_key = serialize_category_filter(normalized_categories, normalized_excluded_categories)
        now = datetime.utcnow().replace(tzinfo=timezone.utc)
        source = self._load_source(
            forecast_product=forecast_product,
            service_categories=normalized_categories,
            excluded_service_categories=normalized_excluded_categories,
        )
        inferred_granularity = "hourly" if forecast_product == "daily_1_day" else "daily"
        history_end = source.forecast_boundary if source is not None else now
        history_start = history_end - timedelta(days=7)
        load_record = self.visualization_repository.create_load_record(
            requested_by_actor="operational_manager",
            forecast_product_name=forecast_product,
            forecast_granularity=source.forecast_granularity if source is not None else inferred_granularity,
            service_category_filter=filter_key,
            history_window_start=history_start,
            history_window_end=history_end,
            forecast_window_start=source.forecast_window_start if source is not None else None,
            forecast_window_end=source.forecast_window_end if source is not None else None,
            source_cleaned_dataset_version_id=source.source_cleaned_dataset_version_id if source is not None else None,
            source_forecast_version_id=source.source_forecast_version_id if source is not None else None,
            source_weekly_forecast_version_id=source.source_weekly_forecast_version_id if source is not None else None,
        )

        if source is None:
            fallback = self.snapshot_service.get_fallback_visualization(
                forecast_product=forecast_product,
                service_categories=normalized_categories,
                excluded_service_categories=normalized_excluded_categories,
                visualization_load_id=load_record.visualization_load_id,
                now=now,
            )
            if fallback is not None:
                response, snapshot = fallback
                self.visualization_repository.complete_load(
                    load_record.visualization_load_id,
                    status="fallback_shown",
                    fallback_snapshot_id=snapshot.visualization_snapshot_id,
                    history_window_start=response.history_window_start,
                    history_window_end=response.history_window_end,
                    forecast_window_start=response.forecast_window_start,
                    forecast_window_end=response.forecast_window_end,
                    source_cleaned_dataset_version_id=response.source_cleaned_dataset_version_id,
                    source_forecast_version_id=response.source_forecast_version_id,
                    source_weekly_forecast_version_id=response.source_weekly_forecast_version_id,
                    **self._confidence_kwargs(response.forecast_confidence),
                )
                return response
            response = self._build_unavailable_response(
                load_record=load_record,
                forecast_product=forecast_product,
                granularity=inferred_granularity,
                service_categories=normalized_categories,
                history_window_start=history_start,
                history_window_end=history_end,
                failure_reason="Current forecast data is unavailable and no eligible fallback snapshot exists.",
            )
            self.visualization_repository.complete_load(
                load_record.visualization_load_id,
                status="unavailable",
                failure_reason=response.summary,
                **self._confidence_kwargs(response.forecast_confidence),
            )
            return response

        historical_series, dataset_version_id, history_start, history_end = self.historical_demand_service.build_series(
            boundary=source.forecast_boundary,
            granularity=source.forecast_granularity,
            service_categories=normalized_categories,
            excluded_service_categories=normalized_excluded_categories,
        )
        degradation_type = None
        if not historical_series:
            degradation_type = "history_missing"
        elif source.uncertainty_bands is None:
            degradation_type = "uncertainty_missing"
        selected_categories = getattr(source, 'selected_categories', None) or normalized_categories
        confidence = self.confidence_service.assess_confidence(
            visualization_load_id=load_record.visualization_load_id,
            forecast_product=forecast_product,
            service_categories=selected_categories,
            degradation_type=degradation_type,
            now=now,
        )
        response = ForecastVisualizationRead(
            visualizationLoadId=load_record.visualization_load_id,
            forecastProduct=forecast_product,
            forecastGranularity=source.forecast_granularity,
            categoryFilter=CategoryFilter(selectedCategory=selected_categories[0] if selected_categories else None, selectedCategories=selected_categories),
            historyWindowStart=history_start,
            historyWindowEnd=history_end,
            forecastWindowStart=source.forecast_window_start,
            forecastWindowEnd=source.forecast_window_end,
            forecastBoundary=source.forecast_boundary,
            lastUpdatedAt=source.last_updated_at,
            sourceCleanedDatasetVersionId=dataset_version_id or source.source_cleaned_dataset_version_id,
            sourceForecastVersionId=source.source_forecast_version_id,
            sourceWeeklyForecastVersionId=source.source_weekly_forecast_version_id,
            historicalSeries=historical_series,
            forecastSeries=source.forecast_series,
            uncertaintyBands=source.uncertainty_bands,
            alerts=self._build_alerts(degradation_type),
            pipelineStatus=self._build_pipeline_status(source, degradation_type),
            forecastConfidence=confidence.to_schema(),
            viewStatus="degraded" if degradation_type else "success",
            degradationType=degradation_type,
            summary=self._build_summary(degradation_type),
        )
        self.visualization_repository.complete_load(
            load_record.visualization_load_id,
            status="degraded" if degradation_type else "success",
            degradation_type=degradation_type,
            history_window_start=history_start,
            history_window_end=history_end,
            source_cleaned_dataset_version_id=dataset_version_id or source.source_cleaned_dataset_version_id,
            **self._confidence_kwargs(response.forecast_confidence),
        )
        if degradation_type is None:
            self.snapshot_service.store_snapshot(load_record=load_record, source=source, response=response)
        return response

    def list_service_categories(self, *, forecast_product: str) -> ServiceCategoryOptionsRead:
        categories: list[str]
        if forecast_product == "daily_1_day":
            marker = self.forecast_repository.get_current_marker(self.settings.forecast_product_name)
            if marker is None:
                categories = []
            else:
                buckets = self.forecast_repository.list_buckets(marker.forecast_version_id)
                categories = self.source_service.list_daily_categories(buckets)
        else:
            marker = self.weekly_forecast_repository.get_current_marker(self.settings.weekly_forecast_product_name)
            if marker is None:
                categories = []
            else:
                buckets = self.weekly_forecast_repository.list_buckets(marker.weekly_forecast_version_id)
                categories = self.source_service.list_weekly_categories(buckets)
        return ServiceCategoryOptionsRead(forecastProduct=forecast_product, categories=categories)

    def record_render_event(self, visualization_load_id: str, payload: VisualizationRenderEvent) -> None:
        self.visualization_repository.report_render_event(
            visualization_load_id,
            render_status=payload.render_status,
            failure_reason=payload.failure_reason,
        )

    def record_confidence_render_event(self, visualization_load_id: str, payload: VisualizationRenderEvent) -> None:
        self.visualization_repository.report_confidence_render_event(
            visualization_load_id,
            render_status=payload.render_status,
            failure_reason=payload.failure_reason,
        )

    def _load_source(
        self,
        *,
        forecast_product: str,
        service_categories: list[str] | None = None,
        excluded_service_categories: list[str] | None = None,
        service_category: str | None = None,
    ) -> NormalizedForecastSource | None:
        normalized_categories = normalize_service_categories(service_categories or ([service_category] if service_category else []))
        normalized_excluded_categories = normalize_service_categories(excluded_service_categories)
        if forecast_product == "daily_1_day":
            marker = self.forecast_repository.get_current_marker(self.settings.forecast_product_name)
            if marker is None:
                return None
            version = self.forecast_repository.get_forecast_version(marker.forecast_version_id)
            if version is None or version.storage_status != "stored":
                return None
            version_id = getattr(version, "forecast_version_id", marker.forecast_version_id)
            buckets = self.forecast_repository.list_buckets(version_id)
            return self.source_service.normalize_daily(
                marker=marker,
                version=version,
                buckets=buckets,
                service_categories=normalized_categories,
                excluded_service_categories=normalized_excluded_categories,
            )
        marker = self.weekly_forecast_repository.get_current_marker(self.settings.weekly_forecast_product_name)
        if marker is None:
            return None
        version = self.weekly_forecast_repository.get_forecast_version(marker.weekly_forecast_version_id)
        if version is None or version.storage_status != "stored":
            return None
        version_id = getattr(version, "weekly_forecast_version_id", marker.weekly_forecast_version_id)
        buckets = self.weekly_forecast_repository.list_buckets(version_id)
        return self.source_service.normalize_weekly(
            marker=marker,
            version=version,
            buckets=buckets,
            service_categories=normalized_categories,
            excluded_service_categories=normalized_excluded_categories,
        )

    @staticmethod
    def _build_alerts(degradation_type: str | None) -> list[StatusMessage]:
        if degradation_type == "history_missing":
            return [StatusMessage(code="history_missing", level="warning", message="Historical context is unavailable for this visualization.")]
        if degradation_type == "uncertainty_missing":
            return [StatusMessage(code="uncertainty_missing", level="warning", message="Uncertainty bands are unavailable for this visualization.")]
        return []

    @staticmethod
    def _build_pipeline_status(source: NormalizedForecastSource, degradation_type: str | None) -> list[StatusMessage]:
        messages = [StatusMessage(code="forecast_loaded", level="info", message=f"Loaded {source.forecast_product} forecast data.")]
        if degradation_type is None:
            messages.append(StatusMessage(code="visualization_ready", level="info", message="Visualization data is complete."))
        return messages

    @staticmethod
    def _build_summary(degradation_type: str | None) -> str:
        if degradation_type == "history_missing":
            return "Visualization is available without the historical overlay."
        if degradation_type == "uncertainty_missing":
            return "Visualization is available without uncertainty bands."
        return "Visualization is available."

    @staticmethod
    def _build_unavailable_response(
        *,
        load_record: VisualizationLoadRecord,
        forecast_product: str,
        granularity: str,
        service_categories: list[str] | None,
        history_window_start: datetime,
        history_window_end: datetime,
        failure_reason: str,
    ) -> ForecastVisualizationRead:
        normalized_categories = normalize_service_categories(service_categories)
        return ForecastVisualizationRead(
            visualizationLoadId=load_record.visualization_load_id,
            forecastProduct=forecast_product,
            forecastGranularity=granularity,
            categoryFilter=CategoryFilter(selectedCategory=normalized_categories[0] if normalized_categories else None, selectedCategories=normalized_categories),
            historyWindowStart=history_window_start,
            historyWindowEnd=history_window_end,
            alerts=[StatusMessage(code="visualization_unavailable", level="error", message=failure_reason)],
            pipelineStatus=[StatusMessage(code="forecast_missing", level="error", message="Current forecast data could not be resolved.")],
            forecastConfidence=build_unavailable_confidence_read(),
            viewStatus="unavailable",
            summary=failure_reason,
        )

    @staticmethod
    def _confidence_kwargs(confidence: ForecastConfidenceRead | None) -> dict[str, object]:
        if confidence is None:
            return {}
        return {
            "confidence_assessment_status": confidence.assessment_status,
            "confidence_indicator_state": confidence.indicator_state,
            "confidence_reason_categories": confidence.reason_categories,
            "confidence_supporting_signals": confidence.supporting_signals,
            "confidence_message": confidence.message,
            "confidence_signal_resolution_status": confidence_signal_resolution_status(confidence.assessment_status),
        }
