from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any

LAG_HOURS = (1, 24, 168)
ROLLING_WINDOWS = (24, 168)


def _extract_geography_key(record: dict[str, object]) -> str | None:
    for key in ("geography_key", "neighbourhood", "ward", "district"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _parse_requested_at(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def _hour_floor(value: datetime) -> datetime:
    return value.astimezone(timezone.utc).replace(minute=0, second=0, microsecond=0)


def _empty_lag_features() -> dict[str, float]:
    features: dict[str, float] = {}
    for lag_hour in LAG_HOURS:
        features[f"lag_{lag_hour}h"] = 0.0
    for window in ROLLING_WINDOWS:
        features[f"rolling_mean_{window}h"] = 0.0
    return features


def _compute_lag_features(
    *,
    bucket_start: datetime,
    hourly_history: dict[datetime, float],
) -> dict[str, float]:
    features: dict[str, float] = {}
    for lag_hour in LAG_HOURS:
        features[f"lag_{lag_hour}h"] = float(hourly_history.get(bucket_start - timedelta(hours=lag_hour), 0.0))
    for window in ROLLING_WINDOWS:
        window_total = 0.0
        for offset in range(1, window + 1):
            window_total += float(hourly_history.get(bucket_start - timedelta(hours=offset), 0.0))
        features[f"rolling_mean_{window}h"] = window_total / float(window)
    return features


def _build_row(
    *,
    bucket_start: datetime,
    category: str,
    geography_key: str | None,
    observed_count: float,
    historical_mean: float,
    weather_by_hour: dict[datetime, dict[str, object]],
    holiday_dates: set[str],
    lag_features: dict[str, float] | None = None,
) -> dict[str, object]:
    weather = weather_by_hour.get(bucket_start, {})
    weather_is_missing = not weather
    row = {
        "bucket_start": bucket_start,
        "bucket_end": bucket_start + timedelta(hours=1),
        "service_category": category,
        "geography_key": geography_key,
        "observed_count": float(observed_count),
        "historical_mean": historical_mean,
        "weather_temperature_c": (float(weather.get("temperature_c")) if "temperature_c" in weather else None),
        "weather_precipitation_mm": (float(weather.get("precipitation_mm")) if "precipitation_mm" in weather else None),
        "weather_snowfall_mm": (float(weather.get("snowfall_mm")) if "snowfall_mm" in weather else None),
        "weather_precipitation_probability_pct": (
            float(weather.get("precipitation_probability_pct"))
            if "precipitation_probability_pct" in weather
            else None
        ),
        "weather_is_missing": weather_is_missing,
        "is_holiday": bucket_start.date().isoformat() in holiday_dates,
        "hour_of_day": bucket_start.hour,
        "day_of_week": bucket_start.weekday(),
        "day_of_year": bucket_start.timetuple().tm_yday,
        "month": bucket_start.month,
        "is_weekend": bucket_start.weekday() >= 5,
    }
    row.update(lag_features or _empty_lag_features())
    return row


def prepare_forecast_features(
    *,
    dataset_records: list[dict[str, object]],
    horizon_start: datetime,
    horizon_end: datetime,
    weather_rows: list[dict[str, object]],
    holidays: list[dict[str, object]],
    max_history_hours: int = 24 * 56,
) -> dict[str, object]:
    geography_complete = True
    parsed_records: list[tuple[datetime, str, str | None]] = []

    for record in dataset_records:
        requested_at = _parse_requested_at(record.get("requested_at"))
        if requested_at is None:
            continue
        bucket_start = _hour_floor(requested_at)
        if bucket_start >= horizon_start:
            continue
        category = str(record.get("category") or "Uncategorized")
        geography_key = _extract_geography_key(record)
        if geography_key is None:
            geography_complete = False
        parsed_records.append((bucket_start, category, geography_key))

    categories = sorted({category for _, category, _ in parsed_records}) or ["Uncategorized"]
    weather_by_hour = {
        row["timestamp"]: row
        for row in weather_rows
        if isinstance(row, dict) and isinstance(row.get("timestamp"), datetime)
    }
    holiday_dates = {
        row["date"]
        for row in holidays
        if isinstance(row, dict) and isinstance(row.get("date"), str)
    }

    scoped_records: list[tuple[datetime, str, str | None]] = []
    hourly_counts: Counter[tuple[datetime, str, str | None]] = Counter()
    scoped_geographies: dict[str, list[str | None]] = {}

    for bucket_start, category, geography_key in parsed_records:
        scoped_geography = geography_key if geography_complete else None
        scoped_records.append((bucket_start, category, scoped_geography))
        hourly_counts[(bucket_start, category, scoped_geography)] += 1

    for category in categories:
        if geography_complete:
            options = sorted({geo for _, cat, geo in scoped_records if cat == category and geo is not None})
            scoped_geographies[category] = options or [None]
        else:
            scoped_geographies[category] = [None]

    if scoped_records:
        latest_history = max(bucket_start for bucket_start, _, _ in scoped_records)
        history_start = max(
            _hour_floor(horizon_start - timedelta(hours=max_history_hours)),
            latest_history - timedelta(hours=max_history_hours - 1),
        )
    else:
        history_start = _hour_floor(horizon_start - timedelta(hours=max_history_hours))

    hours_in_window = max(int((horizon_start - history_start) / timedelta(hours=1)), 1)
    history_by_scope: dict[tuple[str, str | None], dict[datetime, float]] = {}
    historical_means: dict[tuple[str, str | None], float] = {}

    for category in categories:
        for geography_key in scoped_geographies[category]:
            scope_key = (category, geography_key)
            scoped_history: dict[datetime, float] = {}
            total = 0.0
            current = history_start
            while current < horizon_start:
                observed_count = float(hourly_counts.get((current, category, geography_key), 0.0))
                scoped_history[current] = observed_count
                total += observed_count
                current += timedelta(hours=1)
            history_by_scope[scope_key] = scoped_history
            historical_means[scope_key] = total / float(hours_in_window)

    training_rows: list[dict[str, object]] = []
    for category in categories:
        for geography_key in scoped_geographies[category]:
            scope_key = (category, geography_key)
            scoped_history = history_by_scope[scope_key]
            historical_mean = historical_means[scope_key]
            current = history_start
            while current < horizon_start:
                training_rows.append(
                    _build_row(
                        bucket_start=current,
                        category=category,
                        geography_key=geography_key,
                        observed_count=scoped_history[current],
                        historical_mean=historical_mean,
                        weather_by_hour=weather_by_hour,
                        holiday_dates=holiday_dates,
                        lag_features=_compute_lag_features(bucket_start=current, hourly_history=scoped_history),
                    )
                )
                current += timedelta(hours=1)

    rows: list[dict[str, object]] = []
    current = horizon_start
    while current < horizon_end:
        for category in categories:
            for geography_key in scoped_geographies[category]:
                scope_key = (category, geography_key)
                rows.append(
                    _build_row(
                        bucket_start=current,
                        category=category,
                        geography_key=geography_key,
                        observed_count=0.0,
                        historical_mean=historical_means.get(scope_key, 0.0),
                        weather_by_hour=weather_by_hour,
                        holiday_dates=holiday_dates,
                    )
                )
        current += timedelta(hours=1)

    return {
        "rows": rows,
        "training_rows": training_rows,
        "geography_scope": "category_and_geography" if geography_complete else "category_only",
        "categories": categories,
    }
