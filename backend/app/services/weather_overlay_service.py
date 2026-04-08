from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.clients.geomet_client import GeoMetClient, GeoMetClientError
from app.repositories.weather_overlay_repository import WeatherOverlayRepository
from app.schemas.weather_overlay import (
    WeatherMeasure,
    WeatherObservationPoint,
    WeatherOverlayRenderEvent,
    WeatherOverlayResponse,
    WeatherOverlaySource,
)
from app.services.weather_overlay_alignment import WeatherOverlayAlignmentService


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _to_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class WeatherOverlayService:
    def __init__(
        self,
        *,
        repository: WeatherOverlayRepository,
        geomet_client: GeoMetClient,
        alignment_service: WeatherOverlayAlignmentService,
    ) -> None:
        self.repository = repository
        self.geomet_client = geomet_client
        self.alignment_service = alignment_service

    def get_overlay(
        self,
        *,
        geography_id: str,
        time_range_start: datetime,
        time_range_end: datetime,
        weather_measure: WeatherMeasure | None,
    ) -> WeatherOverlayResponse:
        request_id = str(uuid4())
        start = _to_utc(time_range_start)
        end = _to_utc(time_range_end)
        if weather_measure is None:
            self.repository.clear_latest_request()
            response = WeatherOverlayResponse(
                overlayRequestId=request_id,
                geographyId=geography_id,
                timeRangeStart=start,
                timeRangeEnd=end,
                weatherMeasure=None,
                overlayStatus="disabled",
                baseForecastPreserved=True,
                userVisible=True,
                stateSource="selection-read-model",
            )
            self.repository.save_state(response)
            return response

        superseded = self.repository.begin_request(request_id)
        if superseded:
            self.repository.mark_superseded(superseded)

        alignment = self.alignment_service.resolve(geography_id)
        if not alignment.supported:
            response = WeatherOverlayResponse(
                overlayRequestId=request_id,
                geographyId=geography_id,
                timeRangeStart=start,
                timeRangeEnd=end,
                weatherMeasure=weather_measure,
                overlayStatus="misaligned",
                statusMessage=alignment.message,
                baseForecastPreserved=True,
                userVisible=True,
                source=WeatherOverlaySource(provider="msc_geomet", stationId=None, alignmentStatus="misaligned"),
                failureCategory="misaligned",
                stateSource="overlay-assembly",
            )
            self.repository.save_state(response)
            return response

        try:
            weather_rows = list(self.geomet_client.fetch_forecast_hourly_conditions(start, end))
        except GeoMetClientError:
            response = WeatherOverlayResponse(
                overlayRequestId=request_id,
                geographyId=geography_id,
                matchedGeographyId=alignment.matched_geography_id,
                timeRangeStart=start,
                timeRangeEnd=end,
                weatherMeasure=weather_measure,
                overlayStatus="retrieval-failed",
                statusMessage="Weather provider retrieval failed for this selection.",
                baseForecastPreserved=True,
                userVisible=True,
                source=WeatherOverlaySource(provider="msc_geomet", stationId=alignment.station_id, alignmentStatus="aligned"),
                failureCategory="retrieval-failed",
                stateSource="overlay-assembly",
            )
            self.repository.save_state(response)
            return response

        observations = self._map_observations(weather_rows, weather_measure, start, end)
        if not observations:
            response = WeatherOverlayResponse(
                overlayRequestId=request_id,
                geographyId=geography_id,
                matchedGeographyId=alignment.matched_geography_id,
                timeRangeStart=start,
                timeRangeEnd=end,
                weatherMeasure=weather_measure,
                overlayStatus="unavailable",
                statusMessage="Weather data is unavailable for the selected range.",
                baseForecastPreserved=True,
                userVisible=True,
                source=WeatherOverlaySource(provider="msc_geomet", stationId=alignment.station_id, alignmentStatus="aligned"),
                failureCategory="weather-missing",
                stateSource="overlay-assembly",
            )
            self.repository.save_state(response)
            return response

        response = WeatherOverlayResponse(
            overlayRequestId=request_id,
            geographyId=geography_id,
            matchedGeographyId=alignment.matched_geography_id,
            timeRangeStart=start,
            timeRangeEnd=end,
            weatherMeasure=weather_measure,
            measurementUnit="°C" if weather_measure == "temperature" else "mm",
            overlayStatus="visible",
            baseForecastPreserved=True,
            userVisible=True,
            observationGranularity="hourly",
            observations=observations,
            source=WeatherOverlaySource(provider="msc_geomet", stationId=alignment.station_id, alignmentStatus="aligned"),
            stateSource="overlay-assembly",
            renderedAt=_utc_now(),
        )
        self.repository.save_state(response)
        return response

    def record_render_event(self, overlay_request_id: str, payload: WeatherOverlayRenderEvent) -> None:
        state = self.repository.get_state(overlay_request_id)
        if state is None:
            raise LookupError("Overlay request not found")
        if state.overlay_status in {"disabled", "superseded"}:
            raise ValueError("Cannot submit render events for disabled or superseded requests")
        self.repository.append_render_event(overlay_request_id, payload)
        if payload.render_status == "failed-to-render":
            self.repository.save_state(
                state.model_copy(
                    update={
                        "overlay_status": "failed-to-render",
                        "status_message": payload.failure_reason or "Overlay failed to render.",
                        "failure_category": "failed-to-render",
                        "state_source": "render-event",
                        "observations": [],
                        "rendered_at": None,
                    }
                )
            )
            return
        self.repository.save_state(state.model_copy(update={"state_source": "render-event", "rendered_at": payload.reported_at}))

    @staticmethod
    def _map_observations(
        rows: list[dict[str, object]],
        weather_measure: WeatherMeasure,
        start: datetime,
        end: datetime,
    ) -> list[WeatherObservationPoint]:
        points: list[WeatherObservationPoint] = []
        for row in rows:
            timestamp_raw = row.get("timestamp")
            if not isinstance(timestamp_raw, datetime):
                if not isinstance(timestamp_raw, str):
                    continue
                try:
                    timestamp = datetime.fromisoformat(timestamp_raw.replace("Z", "+00:00")).astimezone(timezone.utc)
                except ValueError:
                    continue
            else:
                timestamp = _to_utc(timestamp_raw)
            # Keep points inside the requested window [start, end).
            if timestamp < start or timestamp >= end:
                continue
            if weather_measure == "temperature":
                key = "temperature_c"
            elif weather_measure == "snowfall":
                key = "snowfall_mm"
            else:
                key = "precipitation_mm"
            value = row.get(key)
            if value is None and weather_measure == "snowfall":
                value = row.get("precipitation_mm")
            if value is None:
                continue
            try:
                casted = float(value)
            except (TypeError, ValueError):
                continue
            points.append(WeatherObservationPoint(timestamp=timestamp, value=casted))
        points.sort(key=lambda point: point.timestamp)
        return points
