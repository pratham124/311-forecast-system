from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

from app.schemas.demand_comparison_models import ComparisonPoint, ComparisonSeries, MissingCombinationRecord
from app.services.demand_comparison_context_service import DemandComparisonContextService


class DemandComparisonAlignmentError(RuntimeError):
    pass


class DemandComparisonResultBuilder:
    def build(
        self,
        *,
        historical_records: list[dict[str, object]],
        forecast_records: list[dict[str, object]],
        categories: list[str],
        geography_level: str | None,
        geography_values: list[str],
        comparison_granularity: str,
    ) -> tuple[list[ComparisonSeries], list[MissingCombinationRecord], str | None]:
        historical_series = self._build_historical_series(historical_records, geography_level, comparison_granularity)
        forecast_series = self._build_forecast_series(forecast_records, comparison_granularity)
        forecast_has_geography = any(series.geography_key is not None for series in forecast_series)
        if geography_level and forecast_records and not forecast_has_geography:
            raise DemandComparisonAlignmentError("Forecast geography cannot be aligned to the requested geography selection")
        selected_pairs = [
            (category, geography)
            for category in categories
            for geography in (geography_values or [None])
        ]
        forecast_keys = {(series.service_category, series.geography_key) for series in forecast_series}
        missing: list[MissingCombinationRecord] = []
        for category, geography in selected_pairs:
            if forecast_records and (category, geography) not in forecast_keys:
                missing.append(
                    MissingCombinationRecord(
                        service_category=category,
                        geography_key=geography,
                        missing_source="forecast",
                        message=f"Forecast data is unavailable for {category}{f' in {geography}' if geography else ''}.",
                    )
                )
        uncovered_interval = None
        if historical_records:
            timestamps = [
                self._parse_historical_timestamp(str(record.get("requested_at", "")))
                for record in historical_records
            ]
            history_end = max(timestamp for timestamp in timestamps if timestamp is not None)
            uncovered_interval = None if history_end is None else history_end.isoformat().replace("+00:00", "Z")
        return historical_series + forecast_series, missing, uncovered_interval

    def flatten_points(self, series: list[ComparisonSeries]) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        for item in series:
            for point in item.points:
                rows.append(
                    {
                        "series_type": item.series_type,
                        "service_category": item.service_category,
                        "geography_key": item.geography_key,
                        "bucket_start": point.bucket_start,
                        "bucket_end": point.bucket_end,
                        "value": point.value,
                    }
                )
        return rows

    def flatten_missing_combinations(self, rows: list[MissingCombinationRecord]) -> list[dict[str, object]]:
        return [
            {
                "service_category": row.service_category,
                "geography_key": row.geography_key,
                "missing_source": row.missing_source,
                "message": row.message,
            }
            for row in rows
        ]

    def _build_historical_series(
        self,
        records: list[dict[str, object]],
        geography_level: str | None,
        comparison_granularity: str,
    ) -> list[ComparisonSeries]:
        grouped: dict[tuple[str, str | None, datetime], int] = defaultdict(int)
        for record in records:
            timestamp = self._parse_historical_timestamp(str(record.get("requested_at", "")))
            if timestamp is None:
                continue
            bucket_start = self._bucket_start(timestamp, comparison_granularity)
            geography_key = DemandComparisonContextService.extract_geography_value(record, geography_level) if geography_level else None
            category = str(record.get("category", "")).strip()
            grouped[(category, geography_key, bucket_start)] += 1
        return self._to_series(grouped, "historical", comparison_granularity)

    def _build_forecast_series(self, rows: list[dict[str, object]], comparison_granularity: str) -> list[ComparisonSeries]:
        grouped: dict[tuple[str, str | None, datetime], float] = defaultdict(float)
        for row in rows:
            raw_bucket = row.get("bucket_start") or row.get("forecast_date_local")
            bucket_start = self._parse_forecast_bucket(raw_bucket)
            if bucket_start is None:
                continue
            bucket_start = self._bucket_start(bucket_start, comparison_granularity)
            category = str(row.get("service_category", "")).strip()
            geography_key = row.get("geography_key")
            if geography_key is not None:
                geography_key = str(geography_key)
            grouped[(category, geography_key, bucket_start)] += float(row.get("point_forecast", 0.0))
        return self._to_series(grouped, "forecast", comparison_granularity)

    def _to_series(
        self,
        grouped: dict[tuple[str, str | None, datetime], float | int],
        series_type: str,
        comparison_granularity: str,
    ) -> list[ComparisonSeries]:
        series_map: dict[tuple[str, str | None], list[ComparisonPoint]] = defaultdict(list)
        for (category, geography_key, bucket_start), value in sorted(grouped.items(), key=lambda item: item[0]):
            series_map[(category, geography_key)].append(
                ComparisonPoint(
                    bucket_start=bucket_start,
                    bucket_end=self._bucket_end(bucket_start, comparison_granularity),
                    value=float(value),
                )
            )
        return [
            ComparisonSeries(
                series_type=series_type, service_category=category, geography_key=geography_key, points=points
            )
            for (category, geography_key), points in series_map.items()
        ]

    @staticmethod
    def _parse_historical_timestamp(value: str) -> datetime | None:
        if not value:
            return None
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        return parsed.astimezone(timezone.utc) if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)

    @staticmethod
    def _parse_forecast_bucket(value: object) -> datetime | None:
        if isinstance(value, datetime):
            return value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc)
        if isinstance(value, date):
            return datetime(value.year, value.month, value.day, tzinfo=timezone.utc)
        return None

    @staticmethod
    def _bucket_start(timestamp: datetime, comparison_granularity: str) -> datetime:
        if comparison_granularity == "weekly":
            start = timestamp - timedelta(days=timestamp.weekday())
            return start.replace(hour=0, minute=0, second=0, microsecond=0)
        if comparison_granularity == "daily":
            return timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
        return timestamp.replace(minute=0, second=0, microsecond=0)

    @staticmethod
    def _bucket_end(bucket_start: datetime, comparison_granularity: str) -> datetime:
        if comparison_granularity == "weekly":
            return bucket_start + timedelta(days=7)
        if comparison_granularity == "daily":
            return bucket_start + timedelta(days=1)
        return bucket_start + timedelta(hours=1)
