from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timezone

from app.models import CurrentForecastMarker, CurrentWeeklyForecastMarker, ForecastBucket, ForecastVersion, WeeklyForecastBucket, WeeklyForecastVersion
from app.schemas.forecast_visualization import UncertaintyBands, UncertaintyPoint, VisualizationForecastPoint


@dataclass
class NormalizedForecastSource:
    forecast_product: str
    forecast_granularity: str
    source_forecast_version_id: str | None
    source_weekly_forecast_version_id: str | None
    source_forecast_run_id: str | None
    source_weekly_forecast_run_id: str | None
    source_cleaned_dataset_version_id: str
    forecast_window_start: datetime
    forecast_window_end: datetime
    forecast_boundary: datetime
    last_updated_at: datetime | None
    forecast_series: list[VisualizationForecastPoint]
    uncertainty_bands: UncertaintyBands | None
    selected_categories: list[str] = field(default_factory=list)


class ForecastVisualizationSourceService:
    def normalize_daily(
        self,
        *,
        marker: CurrentForecastMarker,
        version: ForecastVersion,
        buckets: list[ForecastBucket],
        service_categories: list[str] | None = None,
        excluded_service_categories: list[str] | None = None,
        service_category: str | None = None,
    ) -> NormalizedForecastSource | None:
        selected_categories = service_categories or ([service_category] if service_category else [])
        excluded_categories = excluded_service_categories or []
        filtered = [
            bucket
            for bucket in buckets
            if (not selected_categories or bucket.service_category in selected_categories)
            and bucket.service_category not in excluded_categories
        ]
        if not filtered:
            return None
        aggregated = _aggregate_daily(filtered)
        if not aggregated:
            return None
        forecast_series = [
            VisualizationForecastPoint(timestamp=item['timestamp'], pointForecast=item['point_forecast'])
            for item in aggregated
        ]
        uncertainty = self._build_uncertainty_from_aggregates(aggregated)
        return NormalizedForecastSource(
            forecast_product="daily_1_day",
            forecast_granularity="hourly",
            source_forecast_version_id=version.forecast_version_id,
            source_weekly_forecast_version_id=None,
            source_forecast_run_id=version.forecast_run_id,
            source_weekly_forecast_run_id=None,
            source_cleaned_dataset_version_id=marker.source_cleaned_dataset_version_id,
            forecast_window_start=_coerce_timestamp(version.horizon_start) or _as_utc(version.horizon_start),
            forecast_window_end=_coerce_timestamp(version.horizon_end) or _as_utc(version.horizon_end),
            forecast_boundary=_coerce_timestamp(version.horizon_start) or _as_utc(version.horizon_start),
            last_updated_at=_coerce_timestamp(marker.updated_at),
            forecast_series=forecast_series,
            uncertainty_bands=uncertainty,
            selected_categories=self.list_daily_categories(filtered),
        )

    def normalize_weekly(
        self,
        *,
        marker: CurrentWeeklyForecastMarker,
        version: WeeklyForecastVersion,
        buckets: list[WeeklyForecastBucket],
        service_categories: list[str] | None = None,
        excluded_service_categories: list[str] | None = None,
        service_category: str | None = None,
    ) -> NormalizedForecastSource | None:
        selected_categories = service_categories or ([service_category] if service_category else [])
        excluded_categories = excluded_service_categories or []
        filtered = [
            bucket
            for bucket in buckets
            if (not selected_categories or bucket.service_category in selected_categories)
            and bucket.service_category not in excluded_categories
        ]
        if not filtered:
            return None
        aggregated = _aggregate_weekly(filtered)
        if not aggregated:
            return None
        forecast_series = [
            VisualizationForecastPoint(timestamp=item['timestamp'], pointForecast=item['point_forecast'])
            for item in aggregated
        ]
        uncertainty = self._build_uncertainty_from_aggregates(aggregated)
        return NormalizedForecastSource(
            forecast_product="weekly_7_day",
            forecast_granularity="daily",
            source_forecast_version_id=None,
            source_weekly_forecast_version_id=version.weekly_forecast_version_id,
            source_forecast_run_id=None,
            source_weekly_forecast_run_id=version.weekly_forecast_run_id,
            source_cleaned_dataset_version_id=marker.source_cleaned_dataset_version_id,
            forecast_window_start=_coerce_timestamp(version.week_start_local) or _as_utc(version.week_start_local),
            forecast_window_end=_coerce_timestamp(version.week_end_local) or _as_utc(version.week_end_local),
            forecast_boundary=_coerce_timestamp(version.week_start_local) or _as_utc(version.week_start_local),
            last_updated_at=_coerce_timestamp(marker.updated_at),
            forecast_series=forecast_series,
            uncertainty_bands=uncertainty,
            selected_categories=self.list_weekly_categories(filtered),
        )

    @staticmethod
    def list_daily_categories(buckets: list[ForecastBucket]) -> list[str]:
        return sorted({bucket.service_category for bucket in buckets if bucket.service_category})

    @staticmethod
    def list_weekly_categories(buckets: list[WeeklyForecastBucket]) -> list[str]:
        return sorted({bucket.service_category for bucket in buckets if bucket.service_category})

    @staticmethod
    def _build_uncertainty_daily(buckets: list[ForecastBucket]) -> UncertaintyBands | None:
        points = []
        for bucket in buckets:
            timestamp = _coerce_timestamp(bucket.bucket_start)
            values = [_coerce_float(bucket.quantile_p10), _coerce_float(bucket.quantile_p50), _coerce_float(bucket.quantile_p90)]
            if timestamp is None or any(value is None for value in values):
                return None
            points.append(
                UncertaintyPoint(
                    timestamp=timestamp,
                    p10=values[0],
                    p50=values[1],
                    p90=values[2],
                )
            )
        return UncertaintyBands(labels=["P10", "P50", "P90"], points=points)

    @staticmethod
    def _build_uncertainty_weekly(buckets: list[WeeklyForecastBucket]) -> UncertaintyBands | None:
        points = []
        for bucket in buckets:
            timestamp = _coerce_timestamp(bucket.forecast_date_local)
            values = [_coerce_float(bucket.quantile_p10), _coerce_float(bucket.quantile_p50), _coerce_float(bucket.quantile_p90)]
            if timestamp is None or any(value is None for value in values):
                return None
            points.append(
                UncertaintyPoint(
                    timestamp=timestamp,
                    p10=values[0],
                    p50=values[1],
                    p90=values[2],
                )
            )
        return UncertaintyBands(labels=["P10", "P50", "P90"], points=points)

    @staticmethod
    def _build_uncertainty_from_aggregates(aggregated: list[dict[str, float | datetime | None]]) -> UncertaintyBands | None:
        points = []
        for item in aggregated:
            values = [item['p10'], item['p50'], item['p90']]
            if any(value is None for value in values):
                return None
            points.append(
                UncertaintyPoint(
                    timestamp=item['timestamp'],
                    p10=item['p10'],
                    p50=item['p50'],
                    p90=item['p90'],
                )
            )
        return UncertaintyBands(labels=["P10", "P50", "P90"], points=points)


def _aggregate_daily(buckets: list[ForecastBucket]) -> list[dict[str, float | datetime | None]]:
    aggregated: dict[datetime, dict[str, float | datetime | None]] = {}
    for bucket in buckets:
        timestamp = _coerce_timestamp(bucket.bucket_start)
        point_forecast = _coerce_float(bucket.point_forecast)
        if timestamp is None or point_forecast is None:
            continue
        entry = aggregated.setdefault(
            timestamp,
            {'timestamp': timestamp, 'point_forecast': 0.0, 'p10': 0.0, 'p50': 0.0, 'p90': 0.0, 'has_uncertainty': True},
        )
        entry['point_forecast'] += point_forecast
        values = [_coerce_float(bucket.quantile_p10), _coerce_float(bucket.quantile_p50), _coerce_float(bucket.quantile_p90)]
        if any(value is None for value in values):
            entry['has_uncertainty'] = False
            entry['p10'] = None
            entry['p50'] = None
            entry['p90'] = None
        elif entry['has_uncertainty']:
            entry['p10'] += values[0]
            entry['p50'] += values[1]
            entry['p90'] += values[2]
    result = []
    for timestamp in sorted(aggregated):
        entry = aggregated[timestamp]
        if not entry['has_uncertainty']:
            entry['p10'] = None
            entry['p50'] = None
            entry['p90'] = None
        result.append(entry)
    return result


def _aggregate_weekly(buckets: list[WeeklyForecastBucket]) -> list[dict[str, float | datetime | None]]:
    aggregated: dict[datetime, dict[str, float | datetime | None]] = {}
    for bucket in buckets:
        timestamp = _coerce_timestamp(bucket.forecast_date_local)
        point_forecast = _coerce_float(bucket.point_forecast)
        if timestamp is None or point_forecast is None:
            continue
        entry = aggregated.setdefault(
            timestamp,
            {'timestamp': timestamp, 'point_forecast': 0.0, 'p10': 0.0, 'p50': 0.0, 'p90': 0.0, 'has_uncertainty': True},
        )
        entry['point_forecast'] += point_forecast
        values = [_coerce_float(bucket.quantile_p10), _coerce_float(bucket.quantile_p50), _coerce_float(bucket.quantile_p90)]
        if any(value is None for value in values):
            entry['has_uncertainty'] = False
            entry['p10'] = None
            entry['p50'] = None
            entry['p90'] = None
        elif entry['has_uncertainty']:
            entry['p10'] += values[0]
            entry['p50'] += values[1]
            entry['p90'] += values[2]
    result = []
    for timestamp in sorted(aggregated):
        entry = aggregated[timestamp]
        if not entry['has_uncertainty']:
            entry['p10'] = None
            entry['p50'] = None
            entry['p90'] = None
        result.append(entry)
    return result


def _coerce_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _coerce_timestamp(value: object) -> datetime | None:
    if isinstance(value, datetime):
        return _as_utc(value)
    if isinstance(value, date):
        return datetime.combine(value, time.min, tzinfo=timezone.utc)
    return None


def _as_utc(value: datetime | date) -> datetime:
    if isinstance(value, date) and not isinstance(value, datetime):
        return datetime.combine(value, time.min, tzinfo=timezone.utc)
    return value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc)
