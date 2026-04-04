from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import httpx

from app.clients.weather_client import WeatherClientError
from app.core.config import get_settings


class OpenMeteoClientError(WeatherClientError):
    pass


@dataclass
class OpenMeteoClient:
    base_url: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    timezone_name: str | None = None
    timeout: float | None = None

    def __post_init__(self) -> None:
        settings = get_settings()
        self.base_url = (self.base_url or getattr(settings, "open_meteo_base_url", "https://api.open-meteo.com/v1")).rstrip("/")
        self.latitude = float(self.latitude if self.latitude is not None else getattr(settings, "open_meteo_latitude", 53.5461))
        self.longitude = float(self.longitude if self.longitude is not None else getattr(settings, "open_meteo_longitude", -113.4938))
        self.timezone_name = self.timezone_name or getattr(settings, "weekly_forecast_timezone", "America/Edmonton")
        self.timeout = float(self.timeout if self.timeout is not None else getattr(settings, "open_meteo_timeout_seconds", 30.0))

    def fetch_historical_hourly_conditions(self, horizon_start: datetime, horizon_end: datetime) -> list[dict[str, object]]:
        payload = self._request(
            self._historical_url(),
            params={
                "latitude": self.latitude,
                "longitude": self.longitude,
                "start_date": _as_local_date(horizon_start, self.timezone_name),
                "end_date": _as_local_date(horizon_end, self.timezone_name),
                "hourly": "temperature_2m,precipitation,snowfall,precipitation_probability",
                "timezone": "UTC",
            },
        )
        return _normalize_hourly_payload(payload, horizon_start, horizon_end)

    def fetch_forecast_hourly_conditions(self, horizon_start: datetime, horizon_end: datetime) -> list[dict[str, object]]:
        forecast_days = max(1, min(16, _days_to_cover(horizon_start, horizon_end, self.timezone_name)))
        payload = self._request(
            f"{self.base_url}/forecast",
            params={
                "latitude": self.latitude,
                "longitude": self.longitude,
                "hourly": "temperature_2m,precipitation,snowfall,precipitation_probability",
                "forecast_days": forecast_days,
                "timezone": "UTC",
            },
        )
        return _normalize_hourly_payload(payload, horizon_start, horizon_end)

    def fetch_hourly_conditions(self, horizon_start: datetime, horizon_end: datetime) -> list[dict[str, object]]:
        return self.fetch_historical_hourly_conditions(horizon_start, horizon_end)

    def _historical_url(self) -> str:
        if self.base_url.endswith("/v1"):
            prefix = self.base_url[:-3]
            if prefix == "https://api.open-meteo.com":
                return "https://archive-api.open-meteo.com/v1/archive"
        if self.base_url == "https://api.open-meteo.com":
            return "https://archive-api.open-meteo.com/v1/archive"
        return f"{self.base_url}/archive"

    def _request(self, url: str, *, params: dict[str, object]) -> dict[str, object]:
        try:
            response = httpx.get(url, params=params, timeout=self.timeout)
        except httpx.TimeoutException as exc:
            raise OpenMeteoClientError("Open-Meteo request timed out") from exc
        except httpx.HTTPError as exc:
            raise OpenMeteoClientError("Open-Meteo request failed") from exc

        if response.status_code >= 400:
            raise OpenMeteoClientError(f"Open-Meteo request failed: {response.status_code}")

        payload = response.json()
        if not isinstance(payload, dict):
            raise OpenMeteoClientError("Unexpected Open-Meteo response payload")
        return payload


def _as_local_date(value: datetime, timezone_name: str) -> str:
    return value.astimezone(_zoneinfo(timezone_name)).date().isoformat()


def _days_to_cover(horizon_start: datetime, horizon_end: datetime, timezone_name: str) -> int:
    start_date = horizon_start.astimezone(_zoneinfo(timezone_name)).date()
    end_date = horizon_end.astimezone(_zoneinfo(timezone_name)).date()
    return (end_date - start_date).days + 1


def _zoneinfo(timezone_name: str):
    from zoneinfo import ZoneInfo

    return ZoneInfo(timezone_name)


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _normalize_hourly_payload(
    payload: dict[str, object],
    horizon_start: datetime,
    horizon_end: datetime,
) -> list[dict[str, object]]:
    hourly = payload.get("hourly")
    if not isinstance(hourly, dict):
        raise OpenMeteoClientError("Unexpected Open-Meteo response payload")

    times = hourly.get("time")
    temperatures = hourly.get("temperature_2m")
    precipitation = hourly.get("precipitation")
    snowfall = hourly.get("snowfall")
    precipitation_probability = hourly.get("precipitation_probability")
    if (
        not isinstance(times, list)
        or not isinstance(temperatures, list)
        or not isinstance(precipitation, list)
        or not isinstance(snowfall, list)
        or not isinstance(precipitation_probability, list)
    ):
        raise OpenMeteoClientError("Unexpected Open-Meteo response payload")

    rows: list[dict[str, object]] = []
    for index, time_value in enumerate(times):
        if (
            index >= len(temperatures)
            or index >= len(precipitation)
            or index >= len(snowfall)
            or index >= len(precipitation_probability)
        ):
            break
        timestamp = _parse_timestamp(time_value)
        if timestamp is None or timestamp < horizon_start or timestamp >= horizon_end:
            continue
        rows.append(
            {
                "timestamp": timestamp,
                "temperature_c": _coerce_float(temperatures[index]),
                "precipitation_mm": _coerce_float(precipitation[index]),
                "snowfall_mm": _coerce_float(snowfall[index]),
                "precipitation_probability_pct": _coerce_float(precipitation_probability[index]),
            }
        )
    return rows


def _coerce_float(value: Any) -> float:
    if value in (None, ""):
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
