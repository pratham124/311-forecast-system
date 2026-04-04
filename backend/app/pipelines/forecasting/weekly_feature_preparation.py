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
    grouped: dict[object, dict[str, float]] = defaultdict(
        lambda: {
            "temp_total": 0.0,
            "precip_total": 0.0,
            "snowfall_total": 0.0,
            "precip_probability_total": 0.0,
            "count": 0.0,
        }
    )
    for row in weather_rows:
        if not isinstance(row, dict):
            continue
        timestamp = row.get("timestamp")
        if not isinstance(timestamp, datetime):
            continue
        local_date = timestamp.astimezone(timezone).date()
        grouped[local_date]["temp_total"] += float(row.get("temperature_c", 0.0))
        grouped[local_date]["precip_total"] += float(row.get("precipitation_mm", 0.0))
        grouped[local_date]["snowfall_total"] += float(row.get("snowfall_mm", 0.0))
        grouped[local_date]["precip_probability_total"] += float(row.get("precipitation_probability_pct", 0.0))
        grouped[local_date]["count"] += 1.0
    return {
        local_date: {
            "avg_temperature_c": values["temp_total"] / values["count"] if values["count"] else 0.0,
            "total_precipitation_mm": values["precip_total"],
            "total_snowfall_mm": values["snowfall_total"],
            "avg_precipitation_probability_pct": (
                values["precip_probability_total"] / values["count"] if values["count"] else 0.0
            ),
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
    historical_dates = sorted({history_date for counts in category_counts.values() for history_date in counts.keys()})
    historical_context = {
        history_date: {
            "has_weather": history_date in weather_by_date,
            "avg_temperature_c": (
                float(weather_by_date[history_date]["avg_temperature_c"])
                if history_date in weather_by_date
                else None
            ),
            "total_precipitation_mm": (
                float(weather_by_date[history_date]["total_precipitation_mm"])
                if history_date in weather_by_date
                else None
            ),
            "total_snowfall_mm": (
                float(weather_by_date[history_date]["total_snowfall_mm"])
                if history_date in weather_by_date
                else None
            ),
            "avg_precipitation_probability_pct": (
                float(weather_by_date[history_date]["avg_precipitation_probability_pct"])
                if history_date in weather_by_date
                else None
            ),
            "is_holiday": history_date.isoformat() in holiday_dates,
        }
        for history_date in historical_dates
    }
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
            "total_snowfall_mm": (
                float(weather_by_date[target_date]["total_snowfall_mm"])
                if target_date in weather_by_date
                else None
            ),
            "avg_precipitation_probability_pct": (
                float(weather_by_date[target_date]["avg_precipitation_probability_pct"])
                if target_date in weather_by_date
                else None
            ),
            "is_holiday": target_date.isoformat() in holiday_dates,
        }
        for target_date in target_dates
    }

    training_rows: list[dict[str, object]] = []
    rows: list[dict[str, object]] = []

    for service_category, geography_key in scopes:
        history = scope_counts.get((service_category, geography_key)) or category_counts.get(service_category, {})
        history_start = min(history, default=week_start_local.date())
        history_end = week_start_local.date() - timedelta(days=1)
        history_days = max((history_end - history_start).days + 1, 1)
        historical_mean = (
            sum(float(value) for value in history.values()) / float(history_days)
            if history
            else 0.0
        )

        current_date = history_start
        while current_date <= history_end:
            context = historical_context.get(current_date, {})
            training_rows.append(
                _build_weekly_row(
                    target_date=current_date,
                    service_category=service_category,
                    geography_key=geography_key,
                    observed_count=float(history.get(current_date, 0.0)),
                    historical_mean=historical_mean,
                    context=context,
                    history=history,
                )
            )
            current_date += timedelta(days=1)

        for target_date in target_dates:
            rows.append(
                _build_weekly_row(
                    target_date=target_date,
                    service_category=service_category,
                    geography_key=geography_key,
                    observed_count=0.0,
                    historical_mean=historical_mean,
                    context=target_context.get(target_date, {}),
                    history=history,
                )
            )

    return {
        "geography_scope": geography_scope,
        "week_start_local": week_start_local,
        "week_end_local": week_end_local,
        "target_dates": target_dates,
        "historical_context": historical_context,
        "target_context": target_context,
        "training_rows": training_rows,
        "rows": rows,
        "scopes": scopes,
        "category_counts": {key: dict(value) for key, value in category_counts.items()},
        "scope_counts": {key: dict(value) for key, value in scope_counts.items()},
    }


def _build_weekly_row(
    *,
    target_date,
    service_category: str,
    geography_key: str | None,
    observed_count: float,
    historical_mean: float,
    context: dict[str, object],
    history: dict[object, int],
) -> dict[str, object]:
    lag_7d = float(history.get(target_date - timedelta(days=7), 0.0))
    rolling_mean_7d = _rolling_mean(history, target_date, 7)
    rolling_mean_28d = _rolling_mean(history, target_date, 28)
    has_weather = bool(context.get("has_weather"))
    return {
        "forecast_date_local": target_date,
        "service_category": service_category,
        "geography_key": geography_key,
        "observed_count": float(observed_count),
        "historical_mean": float(historical_mean),
        "day_of_week": target_date.weekday(),
        "day_of_year": target_date.timetuple().tm_yday,
        "month": target_date.month,
        "is_weekend": target_date.weekday() >= 5,
        "is_holiday": bool(context.get("is_holiday")),
        "weather_is_missing": not has_weather,
        "avg_temperature_c": float(context.get("avg_temperature_c")) if context.get("avg_temperature_c") is not None else None,
        "total_precipitation_mm": float(context.get("total_precipitation_mm")) if context.get("total_precipitation_mm") is not None else None,
        "total_snowfall_mm": float(context.get("total_snowfall_mm")) if context.get("total_snowfall_mm") is not None else None,
        "avg_precipitation_probability_pct": (
            float(context.get("avg_precipitation_probability_pct"))
            if context.get("avg_precipitation_probability_pct") is not None
            else None
        ),
        "lag_7d": lag_7d,
        "rolling_mean_7d": rolling_mean_7d,
        "rolling_mean_28d": rolling_mean_28d,
    }


def _rolling_mean(history: dict[object, int], target_date, window_days: int) -> float:
    total = 0.0
    for offset in range(1, window_days + 1):
        total += float(history.get(target_date - timedelta(days=offset), 0.0))
    return total / float(window_days)
