from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import httpx
import pytest

from app.clients.geomet_client import GeoMetClient
from app.clients.open_meteo_client import OpenMeteoClient, OpenMeteoClientError, _coerce_float, _days_to_cover, _normalize_hourly_payload, _parse_timestamp
from app.clients.weather_client import WeatherClientError, build_weather_client, get_weather_enrichment_source


class _Response:
    def __init__(self, status_code: int, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


@pytest.mark.unit
def test_open_meteo_client_normalizes_forecast_and_history(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.clients.open_meteo_client.get_settings",
        lambda: SimpleNamespace(
            open_meteo_base_url="https://api.open-meteo.com/v1",
            open_meteo_latitude=53.5461,
            open_meteo_longitude=-113.4938,
            open_meteo_timeout_seconds=12.0,
            weekly_forecast_timezone="America/Edmonton",
        ),
    )

    def fake_get(url: str, *, params, timeout):
        assert timeout == 12.0
        if url.endswith("/forecast"):
            assert params["forecast_days"] >= 7
        return _Response(
            200,
            {
                "hourly": {
                    "time": ["2026-03-23T00:00", "2026-03-23T01:00", "bad"],
                    "temperature_2m": [1.5, 2.5, 9.0],
                    "precipitation": [0.2, 0.4, 9.0],
                    "snowfall": [0.0, 1.2, 9.0],
                    "precipitation_probability": [15, 65, 90],
                }
            },
        )

    monkeypatch.setattr("app.clients.open_meteo_client.httpx.get", fake_get)
    client = OpenMeteoClient()
    start = datetime(2026, 3, 23, 0, tzinfo=timezone.utc)
    end = datetime(2026, 3, 30, 0, tzinfo=timezone.utc)

    forecast_rows = client.fetch_forecast_hourly_conditions(start, end)
    historical_rows = client.fetch_historical_hourly_conditions(start, start.replace(hour=2))

    assert forecast_rows[:2] == [
        {
            "timestamp": datetime(2026, 3, 23, 0, tzinfo=timezone.utc),
            "temperature_c": 1.5,
            "precipitation_mm": 0.2,
            "snowfall_mm": 0.0,
            "precipitation_probability_pct": 15.0,
        },
        {
            "timestamp": datetime(2026, 3, 23, 1, tzinfo=timezone.utc),
            "temperature_c": 2.5,
            "precipitation_mm": 0.4,
            "snowfall_mm": 1.2,
            "precipitation_probability_pct": 65.0,
        },
    ]
    assert historical_rows == forecast_rows[:2]


@pytest.mark.unit
def test_open_meteo_client_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.clients.open_meteo_client.get_settings",
        lambda: SimpleNamespace(
            open_meteo_base_url="https://api.open-meteo.com/v1",
            open_meteo_latitude=53.5461,
            open_meteo_longitude=-113.4938,
            open_meteo_timeout_seconds=12.0,
            weekly_forecast_timezone="America/Edmonton",
        ),
    )

    monkeypatch.setattr("app.clients.open_meteo_client.httpx.get", lambda *args, **kwargs: _Response(503, {}))
    with pytest.raises(OpenMeteoClientError):
        OpenMeteoClient().fetch_forecast_hourly_conditions(
            datetime(2026, 3, 23, 0, tzinfo=timezone.utc),
            datetime(2026, 3, 24, 0, tzinfo=timezone.utc),
        )

    def raise_timeout(*args, **kwargs):
        raise httpx.TimeoutException("boom")

    monkeypatch.setattr("app.clients.open_meteo_client.httpx.get", raise_timeout)
    with pytest.raises(OpenMeteoClientError):
        OpenMeteoClient().fetch_historical_hourly_conditions(
            datetime(2026, 3, 23, 0, tzinfo=timezone.utc),
            datetime(2026, 3, 24, 0, tzinfo=timezone.utc),
        )


@pytest.mark.unit
def test_weather_client_factory_and_source(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.clients.weather_client.get_settings", lambda: SimpleNamespace(weather_provider="open_meteo"))
    client = build_weather_client()
    assert isinstance(client, OpenMeteoClient)
    assert get_weather_enrichment_source() == "open_meteo"


@pytest.mark.unit
def test_open_meteo_client_helper_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.clients.open_meteo_client.get_settings",
        lambda: SimpleNamespace(
            open_meteo_base_url="https://api.open-meteo.com",
            open_meteo_latitude=53.5461,
            open_meteo_longitude=-113.4938,
            open_meteo_timeout_seconds=12.0,
            weekly_forecast_timezone="America/Edmonton",
        ),
    )
    monkeypatch.setattr(
        "app.clients.open_meteo_client.httpx.get",
        lambda *args, **kwargs: _Response(
            200,
            {
                "hourly": {
                    "time": ["2026-03-23T00:00:00Z"],
                    "temperature_2m": [1.0],
                    "precipitation": [0.1],
                    "snowfall": [0.0],
                    "precipitation_probability": [20.0],
                }
            },
        ),
    )
    client = OpenMeteoClient()
    start = datetime(2026, 3, 23, 0, tzinfo=timezone.utc)
    end = datetime(2026, 3, 23, 2, tzinfo=timezone.utc)

    assert client._historical_url() == "https://archive-api.open-meteo.com/v1/archive"
    assert client.fetch_hourly_conditions(start, end) == client.fetch_historical_hourly_conditions(start, end)
    assert _days_to_cover(start, end, "America/Edmonton") >= 1
    assert _parse_timestamp("2026-03-23T00:00:00") == datetime(2026, 3, 23, 0, tzinfo=timezone.utc)
    assert _parse_timestamp("") is None
    assert _coerce_float(object()) == 0.0
    assert OpenMeteoClient(base_url="https://weather.example/v1")._historical_url() == "https://weather.example/v1/archive"


@pytest.mark.unit
def test_open_meteo_client_request_and_payload_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.clients.open_meteo_client.get_settings",
        lambda: SimpleNamespace(
            open_meteo_base_url="https://weather.example/api",
            open_meteo_latitude=53.5461,
            open_meteo_longitude=-113.4938,
            open_meteo_timeout_seconds=12.0,
            weekly_forecast_timezone="America/Edmonton",
        ),
    )

    def raise_http_error(*args, **kwargs):
        raise httpx.HTTPError("boom")

    monkeypatch.setattr("app.clients.open_meteo_client.httpx.get", raise_http_error)
    with pytest.raises(OpenMeteoClientError, match="request failed"):
        OpenMeteoClient().fetch_forecast_hourly_conditions(
            datetime(2026, 3, 23, 0, tzinfo=timezone.utc),
            datetime(2026, 3, 24, 0, tzinfo=timezone.utc),
        )

    monkeypatch.setattr("app.clients.open_meteo_client.httpx.get", lambda *args, **kwargs: _Response(200, []))
    with pytest.raises(OpenMeteoClientError, match="Unexpected Open-Meteo response payload"):
        OpenMeteoClient().fetch_historical_hourly_conditions(
            datetime(2026, 3, 23, 0, tzinfo=timezone.utc),
            datetime(2026, 3, 24, 0, tzinfo=timezone.utc),
        )

    with pytest.raises(OpenMeteoClientError, match="Unexpected Open-Meteo response payload"):
        _normalize_hourly_payload({}, datetime(2026, 3, 23, 0, tzinfo=timezone.utc), datetime(2026, 3, 24, 0, tzinfo=timezone.utc))

    with pytest.raises(OpenMeteoClientError, match="Unexpected Open-Meteo response payload"):
        _normalize_hourly_payload(
            {"hourly": {"time": [], "temperature_2m": [], "precipitation": [], "snowfall": [], "precipitation_probability": "bad"}},
            datetime(2026, 3, 23, 0, tzinfo=timezone.utc),
            datetime(2026, 3, 24, 0, tzinfo=timezone.utc),
        )

    rows = _normalize_hourly_payload(
        {
            "hourly": {
                "time": ["2026-03-23T00:00:00Z", "2026-03-23T01:00:00Z"],
                "temperature_2m": [1.0],
                "precipitation": [0.1],
                "snowfall": [0.0],
                "precipitation_probability": [20.0],
            }
        },
        datetime(2026, 3, 23, 0, tzinfo=timezone.utc),
        datetime(2026, 3, 24, 0, tzinfo=timezone.utc),
    )
    assert len(rows) == 1


@pytest.mark.unit
def test_weather_client_factory_geomet_and_unsupported_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.clients.weather_client.get_settings", lambda: SimpleNamespace(weather_provider="geomet"))
    monkeypatch.setattr(
        "app.clients.geomet_client.get_settings",
        lambda: SimpleNamespace(
            geomet_station_selector="edmonton_hourly_station",
            geomet_climate_identifier=None,
            geomet_base_url="https://api.weather.gc.ca",
            geomet_timeout_seconds=30.0,
        ),
    )
    assert isinstance(build_weather_client(), GeoMetClient)
    assert get_weather_enrichment_source() == "msc_geomet"

    monkeypatch.setattr("app.clients.weather_client.get_settings", lambda: SimpleNamespace(weather_provider="custom"))
    assert get_weather_enrichment_source() == "custom"
    with pytest.raises(WeatherClientError, match="Unsupported weather provider"):
        build_weather_client()
