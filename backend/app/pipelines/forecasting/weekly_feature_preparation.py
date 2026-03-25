from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


def _parse_requested_at(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _normalize_geography(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _extract_geography(record: dict[str, object]) -> str | None:
    for key in ("geography_key", "ward", "neighbourhood", "district"):
        geography = _normalize_geography(record.get(key))
        if geography is not None:
            return geography
    return None


def _daily_weather_summary(weather_rows: list[dict[str, object]], timezone_name: str) -> dict[object, dict[str, float]]:
    timezone = ZoneInfo(timezone_name)
    grouped: dict[object, dict[str, float]] = defaultdict(lambda: {"temp_total": 0.0, "precip_total": 0.0, "count": 0.0})
    for row in weather_rows:
        if not isinstance(row, dict):
            continue
        timestamp = row.get("timestamp")
        if not isinstance(timestamp, datetime):
            continue
        local_date = timestamp.astimezone(timezone).date()
        grouped[local_date]["temp_total"] += float(row.get("temperature_c", 0.0))
        grouped[local_date]["precip_total"] += float(row.get("precipitation_mm", 0.0))
        grouped[local_date]["count"] += 1.0
    return {
        local_date: {
            "avg_temperature_c": values["temp_total"] / values["count"] if values["count"] else 0.0,
            "total_precipitation_mm": values["precip_total"],
        }
        for local_date, values in grouped.items()
    }


def prepare_weekly_forecast_features(
    *,
    dataset_records: list[dict[str, object]],
    week_start_local: datetime,
    week_end_local: datetime,
    timezone_name: str,
    weather_rows: list[dict[str, object]] | None = None,
    holidays: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    timezone = ZoneInfo(timezone_name)
    scope_counts: dict[tuple[str, str | None], dict[object, int]] = defaultdict(lambda: defaultdict(int))
    category_counts: dict[str, dict[object, int]] = defaultdict(lambda: defaultdict(int))
    geography_present = 0
    geography_missing = 0

    for record in dataset_records:
        requested_at = _parse_requested_at(record.get("requested_at"))
        category = str(record.get("category", "")).strip()
        if requested_at is None or not category:
            continue
        local_date = requested_at.astimezone(timezone).date()
        geography_key = _extract_geography(record)
        if geography_key is None:
            geography_missing += 1
        else:
            geography_present += 1
        category_counts[category][local_date] += 1
        scope_counts[(category, geography_key)][local_date] += 1

    geography_scope = "category_and_geography" if geography_present > 0 and geography_missing == 0 else "category_only"
    target_dates = [(week_start_local + timedelta(days=offset)).date() for offset in range(7)]
    if geography_scope == "category_and_geography":
        scopes = sorted(scope_counts)
    else:
        scopes = [(category, None) for category in sorted(category_counts)]

    holiday_dates = {
        row["date"]
        for row in (holidays or [])
        if isinstance(row, dict) and isinstance(row.get("date"), str)
    }
    weather_by_date = _daily_weather_summary(weather_rows or [], timezone_name)
    target_context = {
        target_date: {
            "has_weather": target_date in weather_by_date,
            "avg_temperature_c": (
                float(weather_by_date[target_date]["avg_temperature_c"])
                if target_date in weather_by_date
                else None
            ),
            "total_precipitation_mm": (
                float(weather_by_date[target_date]["total_precipitation_mm"])
                if target_date in weather_by_date
                else None
            ),
            "is_holiday": target_date.isoformat() in holiday_dates,
        }
        for target_date in target_dates
    }

    return {
        "geography_scope": geography_scope,
        "week_start_local": week_start_local,
        "week_end_local": week_end_local,
        "target_dates": target_dates,
        "target_context": target_context,
        "scopes": scopes,
        "category_counts": {key: dict(value) for key, value in category_counts.items()},
        "scope_counts": {key: dict(value) for key, value in scope_counts.items()},
    }
