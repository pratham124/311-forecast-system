from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Protocol

import httpx

from app.core.config import get_settings


class GeoMetClientError(RuntimeError):
    pass


SUPPORTED_STATION_SELECTORS = {"fixed_climate_identifier", "edmonton_hourly_station"}
EDMONTON_CENTER = (-113.4938, 53.5461)
EDMONTON_BBOX = (-113.75, 53.42, -113.2, 53.7)
CITYPAGE_WEATHER_COLLECTION = "citypageweather-realtime"
CITYPAGE_WEATHER_EDMONTON_ITEM = "ab-50"


class GeoMetTransport(Protocol):
    def fetch_historical_hourly_conditions(self, horizon_start: datetime, horizon_end: datetime) -> list[dict[str, object]]: ...

    def fetch_forecast_hourly_conditions(self, horizon_start: datetime, horizon_end: datetime) -> list[dict[str, object]]: ...

    def fetch_hourly_conditions(self, horizon_start: datetime, horizon_end: datetime) -> list[dict[str, object]]: ...


class GeoMetHttpTransport:
    def __init__(
        self,
        *,
        base_url: str,
        station_identifier: str | None = None,
        station_selector: str = "edmonton_hourly_station",
        timeout: float = 30.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.station_identifier = station_identifier
        self.station_selector = station_selector
        self.timeout = timeout
        self._resolved_station_identifier: str | None = None

    def fetch_historical_hourly_conditions(self, horizon_start: datetime, horizon_end: datetime) -> list[dict[str, object]]:
        station_identifier = self._resolve_station_identifier()
        print(
            f"[debug][forecast] geomet request start path=historical collection=climate-hourly station={station_identifier} "
            f"window={_format_datetime(horizon_start)}/{_format_datetime(horizon_end)}"
        )
        base_params = {
            "f": "json",
            "limit": 200,
            "datetime": f"{_format_datetime(horizon_start)}/{_format_datetime(horizon_end)}",
            "CLIMATE_IDENTIFIER": station_identifier,
        }
        url = f"{self.base_url}/collections/climate-hourly/items"

        features: list[object] = []
        offset = 0
        while True:
            params = dict(base_params)
            params["offset"] = offset
            response = self._request(url, params=params, accept="application/geo+json")
            payload = response.json()
            batch = payload.get("features", []) if isinstance(payload, dict) else []
            if not isinstance(batch, list):
                print("[debug][forecast] geomet request fail path=historical reason=unexpected_payload")
                raise GeoMetClientError("Unexpected GeoMet response payload")
            features.extend(batch)
            print(
                f"[debug][forecast] geomet request page path=historical offset={offset} features={len(batch)} total_features={len(features)}"
            )
            if len(batch) < int(base_params["limit"]):
                break
            offset += int(base_params["limit"])

        normalized = _normalize_weather_features(
            features,
            timestamp_keys=("UTC_DATE", "LOCAL_DATE"),
            temperature_keys=("TEMP",),
            precipitation_keys=("PRECIP_AMOUNT",),
        )
        print(
            f"[debug][forecast] geomet request end path=historical collection=climate-hourly station={station_identifier} "
            f"features={len(features)} rows={len(normalized)}"
        )
        return normalized

    def fetch_forecast_hourly_conditions(self, horizon_start: datetime, horizon_end: datetime) -> list[dict[str, object]]:
        print(
            f"[debug][forecast] geomet request start path=forecast collection={CITYPAGE_WEATHER_COLLECTION} item={CITYPAGE_WEATHER_EDMONTON_ITEM} "
            f"window={_format_datetime(horizon_start)}/{_format_datetime(horizon_end)}"
        )
        params = {
            "f": "json",
        }
        url = f"{self.base_url}/collections/{CITYPAGE_WEATHER_COLLECTION}/items/{CITYPAGE_WEATHER_EDMONTON_ITEM}"
        response = self._request(url, params=params, accept="application/geo+json")

        payload = response.json()
        normalized = _normalize_citypage_hourly_forecast(payload, horizon_start=horizon_start, horizon_end=horizon_end)
        print(
            f"[debug][forecast] geomet request end path=forecast collection={CITYPAGE_WEATHER_COLLECTION} item={CITYPAGE_WEATHER_EDMONTON_ITEM} "
            f"rows={len(normalized)}"
        )
        if normalized:
            return normalized

        print("[debug][forecast] geomet fallback path=forecast reason=empty_normalized_rows -> historical")
        return self.fetch_historical_hourly_conditions(horizon_start, horizon_end)

    def fetch_hourly_conditions(self, horizon_start: datetime, horizon_end: datetime) -> list[dict[str, object]]:
        print("[debug][forecast] geomet alias path=historical fetch_hourly_conditions")
        return self.fetch_historical_hourly_conditions(horizon_start, horizon_end)

    def _resolve_station_identifier(self) -> str:
        if self.station_selector == "fixed_climate_identifier":
            if not self.station_identifier:
                print("[debug][forecast] geomet station resolution fail selector=fixed_climate_identifier reason=missing_identifier")
                raise GeoMetClientError("GeoMet climate identifier is required for fixed station selection")
            print(f"[debug][forecast] geomet station resolved selector=fixed_climate_identifier station={self.station_identifier}")
            return self.station_identifier
        if self.station_selector != "edmonton_hourly_station":
            print(f"[debug][forecast] geomet station resolution fail selector={self.station_selector} reason=unsupported_selector")
            raise GeoMetClientError(f"Unsupported GeoMet station selector: {self.station_selector}")
        if self._resolved_station_identifier is None:
            self._resolved_station_identifier = self._discover_edmonton_station_identifier()
        print(f"[debug][forecast] geomet station resolved selector=edmonton_hourly_station station={self._resolved_station_identifier}")
        return self._resolved_station_identifier

    def _discover_edmonton_station_identifier(self) -> str:
        url = f"{self.base_url}/collections/climate-stations/items"
        bbox = ",".join(str(value) for value in EDMONTON_BBOX)
        params = {
            "f": "json",
            "limit": 100,
            "bbox": bbox,
        }
        print(
            f"[debug][forecast] geomet station discovery start collection=climate-stations bbox={bbox}"
        )
        response = self._request(url, params=params, accept="application/geo+json")
        payload = response.json()
        features = payload.get("features", []) if isinstance(payload, dict) else []
        if not isinstance(features, list):
            print("[debug][forecast] geomet station discovery fail reason=unexpected_payload")
            raise GeoMetClientError("Unexpected GeoMet station response payload")

        candidates: list[tuple[tuple[int, float, float], str]] = []
        for feature in features:
            if not isinstance(feature, dict):
                continue
            properties = feature.get("properties", {})
            geometry = feature.get("geometry", {})
            if not isinstance(properties, dict):
                continue
            if str(properties.get("HAS_HOURLY_DATA", "N")) != "Y":
                continue
            climate_identifier = properties.get("CLIMATE_IDENTIFIER")
            if not isinstance(climate_identifier, str) or not climate_identifier:
                continue
            station_name = str(properties.get("STATION_NAME") or "")
            lon, lat = _extract_coordinates(feature, geometry, properties)
            distance = _distance_squared((lon, lat), EDMONTON_CENTER)
            recency = _recency_score(properties.get("HLY_LAST_DATE") or properties.get("LAST_DATE"))
            name_score = 0 if "EDMONTON" in station_name.upper() else 1
            candidates.append(((name_score, recency, distance), climate_identifier))

        if not candidates:
            print("[debug][forecast] geomet station discovery fail reason=no_candidates")
            raise GeoMetClientError("No Edmonton-area hourly GeoMet station found")

        candidates.sort(key=lambda item: item[0])
        chosen = candidates[0][1]
        print(f"[debug][forecast] geomet station discovery end candidates={len(candidates)} station={chosen}")
        return chosen

    def _request(self, url: str, *, params: dict[str, object], accept: str) -> httpx.Response:
        try:
            response = httpx.get(url, params=params, headers={"Accept": accept}, timeout=self.timeout)
        except httpx.TimeoutException as exc:
            print(f"[debug][forecast] geomet request fail url={url} reason=timeout")
            raise GeoMetClientError("GeoMet request timed out") from exc
        except httpx.HTTPError as exc:
            print(f"[debug][forecast] geomet request fail url={url} reason=http_error")
            raise GeoMetClientError("GeoMet request failed") from exc

        if response.status_code >= 400:
            print(f"[debug][forecast] geomet request fail url={url} status={response.status_code}")
            raise GeoMetClientError(f"GeoMet request failed: {response.status_code}")
        return response


@dataclass
class GeoMetClient:
    transport: GeoMetTransport | None = None

    def __post_init__(self) -> None:
        if self.transport is None:
            settings = get_settings()
            station_selector = getattr(settings, "geomet_station_selector", "edmonton_hourly_station")
            if station_selector not in SUPPORTED_STATION_SELECTORS:
                raise GeoMetClientError(f"Unsupported GeoMet station selector: {station_selector}")
            station_identifier = getattr(settings, "geomet_climate_identifier", None)
            if station_selector == "fixed_climate_identifier" and not station_identifier:
                raise GeoMetClientError("GeoMet climate identifier is required for fixed station selection")
            self.transport = GeoMetHttpTransport(
                base_url=getattr(settings, "geomet_base_url", "https://api.weather.gc.ca"),
                station_identifier=station_identifier,
                station_selector=station_selector,
                timeout=float(getattr(settings, "geomet_timeout_seconds", 30.0)),
            )

    def fetch_historical_hourly_conditions(self, horizon_start: datetime, horizon_end: datetime) -> list[dict[str, object]]:
        print(
            f"[debug][forecast] geomet client request start path=historical window={_format_datetime(horizon_start)}/{_format_datetime(horizon_end)}"
        )
        if self.transport is not None:
            if hasattr(self.transport, "fetch_historical_hourly_conditions"):
                print("[debug][forecast] geomet client path=transport.fetch_historical_hourly_conditions")
                rows = list(self.transport.fetch_historical_hourly_conditions(horizon_start, horizon_end))
                print(f"[debug][forecast] geomet client request end path=historical rows={len(rows)}")
                return rows
            if hasattr(self.transport, "fetch_hourly_conditions"):
                print("[debug][forecast] geomet client path=transport.fetch_hourly_conditions")
                rows = list(self.transport.fetch_hourly_conditions(horizon_start, horizon_end))
                print(f"[debug][forecast] geomet client request end path=historical rows={len(rows)}")
                return rows
            if hasattr(self.transport, "fetch"):
                print("[debug][forecast] geomet client path=transport.fetch")
                rows = list(self.transport.fetch(horizon_start, horizon_end))
                print(f"[debug][forecast] geomet client request end path=historical rows={len(rows)}")
                return rows
        print("[debug][forecast] geomet client fallback=default path=historical")
        rows = _default_weather_rows(horizon_start, horizon_end)
        print(f"[debug][forecast] geomet client request end path=historical rows={len(rows)}")
        return rows

    def fetch_forecast_hourly_conditions(self, horizon_start: datetime, horizon_end: datetime) -> list[dict[str, object]]:
        print(
            f"[debug][forecast] geomet client request start path=forecast window={_format_datetime(horizon_start)}/{_format_datetime(horizon_end)}"
        )
        if self.transport is not None:
            if hasattr(self.transport, "fetch_forecast_hourly_conditions"):
                print("[debug][forecast] geomet client path=transport.fetch_forecast_hourly_conditions")
                rows = list(self.transport.fetch_forecast_hourly_conditions(horizon_start, horizon_end))
                print(f"[debug][forecast] geomet client request end path=forecast rows={len(rows)}")
                return rows
            if hasattr(self.transport, "fetch_hourly_conditions"):
                print("[debug][forecast] geomet client path=transport.fetch_hourly_conditions")
                rows = list(self.transport.fetch_hourly_conditions(horizon_start, horizon_end))
                print(f"[debug][forecast] geomet client request end path=forecast rows={len(rows)}")
                return rows
            if hasattr(self.transport, "fetch"):
                print("[debug][forecast] geomet client path=transport.fetch")
                rows = list(self.transport.fetch(horizon_start, horizon_end))
                print(f"[debug][forecast] geomet client request end path=forecast rows={len(rows)}")
                return rows
        print("[debug][forecast] geomet client fallback=default path=forecast")
        rows = _default_weather_rows(horizon_start, horizon_end)
        print(f"[debug][forecast] geomet client request end path=forecast rows={len(rows)}")
        return rows

    def fetch_hourly_conditions(self, horizon_start: datetime, horizon_end: datetime) -> list[dict[str, object]]:
        print("[debug][forecast] geomet alias path=historical fetch_hourly_conditions")
        return self.fetch_historical_hourly_conditions(horizon_start, horizon_end)


def _format_datetime(value: datetime) -> str:
    normalized = value.astimezone(timezone.utc).replace(microsecond=0)
    return normalized.isoformat().replace("+00:00", "Z")


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def _coerce_float(value: Any) -> float:
    if value in (None, ""):
        print("[debug][forecast] geomet feature fallback reason=missing_numeric_value value=None")
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        print(f"[debug][forecast] geomet feature fallback reason=invalid_numeric_value value={value!r}")
        return 0.0


def _nested_en_value(value: Any) -> Any:
    if isinstance(value, dict):
        inner = value.get("en")
        if inner is not None:
            return inner
    return value


def _normalize_citypage_hourly_forecast(
    payload: object,
    *,
    horizon_start: datetime,
    horizon_end: datetime,
) -> list[dict[str, object]]:
    if not isinstance(payload, dict):
        print("[debug][forecast] geomet request fail path=forecast reason=unexpected_payload")
        raise GeoMetClientError("Unexpected GeoMet forecast response payload")
    properties = payload.get("properties")
    if not isinstance(properties, dict):
        print("[debug][forecast] geomet request fail path=forecast reason=missing_properties")
        raise GeoMetClientError("Unexpected GeoMet forecast response payload")
    hourly_group = properties.get("hourlyForecastGroup")
    if not isinstance(hourly_group, dict):
        print("[debug][forecast] geomet request fail path=forecast reason=missing_hourly_group")
        raise GeoMetClientError("Unexpected GeoMet forecast response payload")
    hourly_forecasts = hourly_group.get("hourlyForecasts")
    if not isinstance(hourly_forecasts, list):
        print("[debug][forecast] geomet request fail path=forecast reason=missing_hourly_forecasts")
        raise GeoMetClientError("Unexpected GeoMet forecast response payload")

    normalized: list[dict[str, object]] = []
    print(f"[debug][forecast] geomet normalize start path=forecast hourly_rows={len(hourly_forecasts)}")
    for row in hourly_forecasts:
        if not isinstance(row, dict):
            continue
        timestamp = _parse_timestamp(row.get("timestamp"))
        if timestamp is None or timestamp < horizon_start or timestamp >= horizon_end:
            continue
        temperature = _nested_en_value(_nested_en_value(row.get("temperature")).get("value") if isinstance(row.get("temperature"), dict) else None)
        lop = _nested_en_value(_nested_en_value(row.get("lop")).get("value") if isinstance(row.get("lop"), dict) else None)
        normalized.append(
            {
                "timestamp": timestamp,
                "temperature_c": _coerce_float(temperature),
                "precipitation_mm": _coerce_float(lop) / 100.0,
            }
        )
    print(f"[debug][forecast] geomet normalize end path=forecast rows={len(normalized)}")
    return normalized


def _normalize_weather_features(
    features: list[object],
    *,
    timestamp_keys: tuple[str, ...],
    temperature_keys: tuple[str, ...],
    precipitation_keys: tuple[str, ...],
) -> list[dict[str, object]]:
    normalized: list[dict[str, object]] = []
    print(f"[debug][forecast] geomet normalize start features={len(features)}")
    for feature in features:
        if not isinstance(feature, dict):
            continue
        properties = feature.get("properties", {})
        if not isinstance(properties, dict):
            continue
        timestamp = None
        for key in timestamp_keys:
            if key in properties:
                timestamp = _parse_timestamp(properties.get(key))
                if timestamp is not None:
                    break
        if timestamp is None:
            continue
        temperature = next((properties.get(key) for key in temperature_keys if key in properties), None)
        precipitation = next((properties.get(key) for key in precipitation_keys if key in properties), None)
        normalized.append(
            {
                "timestamp": timestamp,
                "temperature_c": _coerce_float(temperature),
                "precipitation_mm": _coerce_float(precipitation),
            }
        )
    print(f"[debug][forecast] geomet normalize end rows={len(normalized)}")
    return normalized


def _default_weather_rows(horizon_start: datetime, horizon_end: datetime) -> list[dict[str, object]]:
    hours = int((horizon_end - horizon_start) / timedelta(hours=1))
    print(
        f"[debug][forecast] geomet fallback path=default window={_format_datetime(horizon_start)}/{_format_datetime(horizon_end)} hours={hours}"
    )
    return [
        {
            "timestamp": horizon_start + timedelta(hours=index),
            "temperature_c": 5.0,
            "precipitation_mm": 0.0,
        }
        for index in range(hours)
    ]


def _extract_coordinates(feature: dict[str, object], geometry: object, properties: dict[str, object]) -> tuple[float, float]:
    if isinstance(geometry, dict):
        coordinates = geometry.get("coordinates")
        if isinstance(coordinates, list) and len(coordinates) >= 2:
            return float(coordinates[0]), float(coordinates[1])
    longitude = properties.get("LONGITUDE")
    latitude = properties.get("LATITUDE")
    if longitude is not None and latitude is not None:
        return float(longitude) / 1_000_000, float(latitude) / 1_000_000
    return EDMONTON_CENTER


def _distance_squared(point: tuple[float, float], reference: tuple[float, float]) -> float:
    return (point[0] - reference[0]) ** 2 + (point[1] - reference[1]) ** 2


def _recency_score(value: Any) -> float:
    if not isinstance(value, str) or not value:
        return float("inf")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return float("inf")
    return -parsed.timestamp()
