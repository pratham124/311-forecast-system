from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.repositories.demand_lineage_repository import DemandLineageRepository
from app.schemas.demand_comparison_models import ComparisonGranularity, ForecastSourceResolution


class AlignmentResolutionError(RuntimeError):
    pass


@dataclass
class DemandComparisonSourceResolver:
    demand_lineage_repository: DemandLineageRepository
    source_name: str
    daily_forecast_product_name: str
    weekly_forecast_product_name: str

    def resolve(
        self,
        *,
        time_range_start: datetime,
        time_range_end: datetime,
        geography_level: str | None,
    ) -> tuple[str | None, ForecastSourceResolution | None]:
        approved_dataset = self.demand_lineage_repository.get_current_approved_dataset(self.source_name)
        source_cleaned_dataset_version_id = approved_dataset.dataset_version_id if approved_dataset is not None else None
        daily_marker = self.demand_lineage_repository.get_current_daily_forecast_marker(self.daily_forecast_product_name)
        if daily_marker and self._covers(daily_marker.horizon_start, daily_marker.horizon_end, time_range_start, time_range_end):
            comparison_granularity: ComparisonGranularity = "hourly" if (time_range_end - time_range_start) <= timedelta(days=2) else "daily"
            return source_cleaned_dataset_version_id, ForecastSourceResolution(
                forecast_product="daily_1_day",
                forecast_granularity="hourly",
                comparison_granularity=comparison_granularity,
                source_forecast_version_id=daily_marker.forecast_version_id,
                source_weekly_forecast_version_id=None,
                source_cleaned_dataset_version_id=source_cleaned_dataset_version_id,
            )
        weekly_marker = self.demand_lineage_repository.get_current_weekly_forecast_marker(self.weekly_forecast_product_name)
        if weekly_marker and self._covers(weekly_marker.week_start_local, weekly_marker.week_end_local, time_range_start, time_range_end):
            comparison_granularity = "weekly" if geography_level else "daily"
            return source_cleaned_dataset_version_id, ForecastSourceResolution(
                forecast_product="weekly_7_day",
                forecast_granularity="daily",
                comparison_granularity=comparison_granularity,
                source_forecast_version_id=None,
                source_weekly_forecast_version_id=weekly_marker.weekly_forecast_version_id,
                source_cleaned_dataset_version_id=source_cleaned_dataset_version_id,
            )
        return source_cleaned_dataset_version_id, None

    @staticmethod
    def ensure_alignment_supported(*, comparison_granularity: str | None, geography_level: str | None, forecast_has_geography: bool) -> None:
        if comparison_granularity is None:
            return
        if geography_level and not forecast_has_geography:
            raise AlignmentResolutionError("Forecast geography cannot be aligned to the requested geography level")

    @staticmethod
    def _covers(source_start: datetime, source_end: datetime, selected_start: datetime, selected_end: datetime) -> bool:
        def normalize(value: datetime) -> datetime:
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
            return value.astimezone(timezone.utc)

        return normalize(source_start) <= normalize(selected_start) and normalize(source_end) >= normalize(selected_end)
