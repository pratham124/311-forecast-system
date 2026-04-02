from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
from app.repositories.forecast_repository import ForecastRepository
from app.repositories.weekly_forecast_repository import WeeklyForecastRepository
from app.schemas.demand_comparison_api import (
    CategoryGeographyAvailability,
    DateConstraints,
    DatePreset,
    DemandComparisonAvailability,
)


def _parse_iso_to_utc(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None


def _normalize_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _normalize_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


class DemandComparisonAvailabilityService:
    SUPPORTED_LEVELS = ("ward", "district", "neighbourhood", "geography_key")

    def __init__(
        self,
        cleaned_dataset_repository: CleanedDatasetRepository,
        forecast_repository: ForecastRepository,
        weekly_forecast_repository: WeeklyForecastRepository,
        source_name: str,
        daily_forecast_product_name: str,
        weekly_forecast_product_name: str,
    ) -> None:
        self.cleaned_dataset_repository = cleaned_dataset_repository
        self.forecast_repository = forecast_repository
        self.weekly_forecast_repository = weekly_forecast_repository
        self.source_name = source_name
        self.daily_forecast_product_name = daily_forecast_product_name
        self.weekly_forecast_product_name = weekly_forecast_product_name

    def get_availability(self) -> DemandComparisonAvailability:
        records = self.cleaned_dataset_repository.list_current_cleaned_records(self.source_name)

        hist_min: datetime | None = None
        hist_max: datetime | None = None
        hist_categories: set[str] = set()
        found_levels: set[str] = set()
        hist_geo_by_cat: dict[str, set[str]] = defaultdict(set)
        hist_level_geo_map: dict[str, dict[str, dict[str, set[str]]]] = defaultdict(
            lambda: defaultdict(lambda: defaultdict(set))
        )

        for record in records:
            requested_at = _parse_iso_to_utc(_normalize_str(record.get("requested_at")))
            if requested_at is not None:
                if hist_min is None or requested_at < hist_min:
                    hist_min = requested_at
                if hist_max is None or requested_at > hist_max:
                    hist_max = requested_at

            category = _normalize_str(record.get("category"))
            if category is None:
                continue
            hist_categories.add(category)

            geo_key = self._extract_geography_value(record, "geography_key")
            if geo_key is not None:
                hist_geo_by_cat[category].add(geo_key)

            for level in self.SUPPORTED_LEVELS:
                level_value = self._extract_geography_value(record, level)
                if level_value is None:
                    continue
                found_levels.add(level)
                if geo_key is not None:
                    hist_level_geo_map[category][level][level_value].add(geo_key)
                else:
                    # Keep the value even if no canonical geography key was extracted.
                    hist_level_geo_map[category][level][level_value]

        # Forecast coverage from active marker
        forecast_product: str | None = None
        forecast_min: datetime | None = None
        forecast_max: datetime | None = None
        forecast_geo_by_cat: dict[str, set[str]] = defaultdict(set)
        forecast_categories: set[str] = set()

        daily_marker = self.forecast_repository.get_current_marker(self.daily_forecast_product_name)
        weekly_marker = self.weekly_forecast_repository.get_current_marker(self.weekly_forecast_product_name)

        if daily_marker is not None:
            forecast_product = "daily_1_day"
            forecast_min = _normalize_utc(daily_marker.horizon_start)
            forecast_max = _normalize_utc(daily_marker.horizon_end)
            for bucket in self.forecast_repository.list_buckets(daily_marker.forecast_version_id):
                category = _normalize_str(bucket.service_category)
                if category is None:
                    continue
                forecast_categories.add(category)
                geography_key = _normalize_str(bucket.geography_key)
                if geography_key is not None:
                    forecast_geo_by_cat[category].add(geography_key)
        elif weekly_marker is not None:
            forecast_product = "weekly_7_day"
            forecast_min = _normalize_utc(weekly_marker.week_start_local)
            forecast_max = _normalize_utc(weekly_marker.week_end_local)
            for bucket in self.weekly_forecast_repository.list_buckets(weekly_marker.weekly_forecast_version_id):
                category = _normalize_str(bucket.service_category)
                if category is None:
                    continue
                forecast_categories.add(category)
                geography_key = _normalize_str(bucket.geography_key)
                if geography_key is not None:
                    forecast_geo_by_cat[category].add(geography_key)

        # Overlap window = intersection of historical and forecast ranges
        overlap_start: datetime | None = None
        overlap_end: datetime | None = None
        if hist_min and hist_max and forecast_min and forecast_max:
            ov_start = max(hist_min, forecast_min)
            ov_end = min(hist_max, forecast_max)
            if ov_start <= ov_end:
                overlap_start = ov_start
                overlap_end = ov_end

        date_constraints = DateConstraints(
            historicalMin=hist_min,
            historicalMax=hist_max,
            forecastMin=forecast_min,
            forecastMax=forecast_max,
            overlapStart=overlap_start,
            overlapEnd=overlap_end,
        )

        presets = self._build_presets(overlap_start, overlap_end, forecast_min, forecast_max)

        # Build per-category geography availability from real category/geography intersections.
        candidate_categories = sorted(hist_categories & forecast_categories) if forecast_categories else []
        service_categories: list[str] = []
        by_category_geography: dict[str, CategoryGeographyAvailability] = {}

        for category in candidate_categories:
            historical_geo_keys = hist_geo_by_cat.get(category, set())
            forecast_geo_keys = forecast_geo_by_cat.get(category, set())
            if forecast_geo_keys and not (historical_geo_keys & forecast_geo_keys):
                continue

            geo_options: dict[str, list[str]] = {}
            valid_levels: list[str] = []
            for level in sorted(found_levels):
                values_to_geo_keys = hist_level_geo_map.get(category, {}).get(level, {})
                if not values_to_geo_keys:
                    continue
                if forecast_geo_keys:
                    values = sorted(
                        value
                        for value, geo_keys in values_to_geo_keys.items()
                        if geo_keys and geo_keys.intersection(forecast_geo_keys)
                    )
                else:
                    # Active forecast lineage is category-only for this category, so geography
                    # filters would produce dead selections in compare queries.
                    values = []
                if values:
                    geo_options[level] = values
                    valid_levels.append(level)

            service_categories.append(category)
            by_category_geography[category] = CategoryGeographyAvailability(
                geographyLevels=valid_levels,
                geographyOptions=geo_options,
            )

        return DemandComparisonAvailability(
            serviceCategories=service_categories,
            byCategoryGeography=by_category_geography,
            dateConstraints=date_constraints,
            presets=presets,
            forecastProduct=forecast_product,
            summary="Availability derived from active cleaned dataset and forecast lineage.",
        )

    def _build_presets(
        self,
        overlap_start: datetime | None,
        overlap_end: datetime | None,
        forecast_min: datetime | None,
        forecast_max: datetime | None,
    ) -> list[DatePreset]:
        presets: list[DatePreset] = []
        if forecast_min is not None and forecast_max is not None:
            presets.append(DatePreset(
                label="Active forecast window",
                timeRangeStart=forecast_min,
                timeRangeEnd=forecast_max,
            ))
        if overlap_start is not None and overlap_end is not None:
            presets.append(DatePreset(
                label="Overlap window",
                timeRangeStart=overlap_start,
                timeRangeEnd=overlap_end,
            ))
        return presets

    @staticmethod
    def _extract_geography_value(record: dict[str, object], geography_level: str | None) -> str | None:
        if geography_level is None:
            return None
        aliases = {
            "ward": ("ward",),
            "district": ("district",),
            "neighbourhood": ("neighbourhood", "neighborhood"),
            "geography_key": ("geography_key", "ward", "district", "neighbourhood", "neighborhood"),
        }
        for key in aliases.get(geography_level, (geography_level,)):
            value = record.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None
