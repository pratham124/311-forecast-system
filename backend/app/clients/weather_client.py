from __future__ import annotations

from typing import Protocol

from app.core.config import get_settings


class WeatherClientError(RuntimeError):
    pass


class WeatherClient(Protocol):
    def fetch_historical_hourly_conditions(self, horizon_start, horizon_end) -> list[dict[str, object]]: ...

    def fetch_forecast_hourly_conditions(self, horizon_start, horizon_end) -> list[dict[str, object]]: ...

    def fetch_hourly_conditions(self, horizon_start, horizon_end) -> list[dict[str, object]]: ...


def build_weather_client():
    settings = get_settings()
    provider = getattr(settings, "weather_provider", "open_meteo")
    if provider == "open_meteo":
        from app.clients.open_meteo_client import OpenMeteoClient

        return OpenMeteoClient()
    if provider == "geomet":
        from app.clients.geomet_client import GeoMetClient

        return GeoMetClient()
    raise WeatherClientError(f"Unsupported weather provider: {provider}")


def get_weather_enrichment_source() -> str:
    settings = get_settings()
    provider = getattr(settings, "weather_provider", "open_meteo")
    if provider == "geomet":
        return "msc_geomet"
    if provider == "open_meteo":
        return "open_meteo"
    return provider
