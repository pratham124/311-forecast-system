from __future__ import annotations

import json
from datetime import datetime, timezone

from app.models import VisualizationLoadRecord, VisualizationSnapshot
from app.repositories.visualization_repository import VisualizationRepository
from app.schemas.forecast_visualization import FallbackMetadata, ForecastVisualizationRead
from app.services.forecast_confidence_service import build_fallback_confidence_read
from app.services.forecast_visualization_sources import NormalizedForecastSource


class VisualizationSnapshotService:
    def __init__(self, visualization_repository: VisualizationRepository, fallback_age_hours: int) -> None:
        self.visualization_repository = visualization_repository
        self.fallback_age_hours = fallback_age_hours

    def store_snapshot(
        self,
        *,
        load_record: VisualizationLoadRecord,
        source: NormalizedForecastSource,
        response: ForecastVisualizationRead,
    ) -> VisualizationSnapshot:
        if hasattr(load_record, 'service_category_filter'):
            service_category_filter = load_record.service_category_filter
        else:
            service_category_filter = _serialize_category_filter(response.category_filter.selected_categories)
        return self.visualization_repository.create_snapshot(
            forecast_product_name=response.forecast_product,
            forecast_granularity=response.forecast_granularity,
            service_category_filter=service_category_filter,
            source_cleaned_dataset_version_id=response.source_cleaned_dataset_version_id or source.source_cleaned_dataset_version_id,
            source_forecast_version_id=response.source_forecast_version_id,
            source_weekly_forecast_version_id=response.source_weekly_forecast_version_id,
            source_forecast_run_id=source.source_forecast_run_id,
            source_weekly_forecast_run_id=source.source_weekly_forecast_run_id,
            history_window_start=response.history_window_start,
            history_window_end=response.history_window_end,
            forecast_window_start=response.forecast_window_start or source.forecast_window_start,
            forecast_window_end=response.forecast_window_end or source.forecast_window_end,
            payload=response.model_dump(by_alias=True, mode="json"),
            created_from_load_id=load_record.visualization_load_id,
            expires_in_hours=self.fallback_age_hours,
        )

    def get_fallback_visualization(
        self,
        *,
        forecast_product: str,
        service_categories: list[str] | None,
        excluded_service_categories: list[str] | None = None,
        visualization_load_id: str,
        now: datetime,
    ) -> tuple[ForecastVisualizationRead, VisualizationSnapshot] | None:
        snapshot = self.visualization_repository.get_latest_eligible_snapshot(
            forecast_product_name=forecast_product,
            service_category_filter=_serialize_category_filter(service_categories, excluded_service_categories),
            now=now,
        )
        if snapshot is None:
            return None
        payload = json.loads(snapshot.payload_json)
        payload["visualizationLoadId"] = visualization_load_id
        payload["viewStatus"] = "fallback_shown"
        payload["forecastConfidence"] = build_fallback_confidence_read().model_dump(by_alias=True, mode="json")
        payload["fallback"] = FallbackMetadata(
            snapshotId=snapshot.visualization_snapshot_id,
            createdAt=_as_utc(snapshot.created_at),
            expiresAt=_as_utc(snapshot.expires_at),
        ).model_dump(by_alias=True, mode="json")
        return ForecastVisualizationRead.model_validate(payload), snapshot


def _serialize_category_filter(service_categories: list[str] | None, excluded_service_categories: list[str] | None = None) -> str | None:
    included = sorted({category.strip() for category in (service_categories or []) if category.strip()})
    excluded = sorted({category.strip() for category in (excluded_service_categories or []) if category.strip()})
    if excluded:
        return f"exclude:{','.join(excluded)}"
    return ','.join(included) if included else None


def _as_utc(value: datetime) -> datetime:
    return value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc)
