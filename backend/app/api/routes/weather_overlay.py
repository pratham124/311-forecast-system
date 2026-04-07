from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.api.dependencies.auth import require_visualization_reader
from app.clients.geomet_client import GeoMetClient
from app.schemas.weather_overlay import WeatherOverlayRenderEvent, WeatherOverlayResponse
from app.services.weather_overlay_alignment import WeatherOverlayAlignmentService
from app.services.weather_overlay_service import WeatherOverlayService
from app.repositories.weather_overlay_repository import WeatherOverlayRepository

router = APIRouter(prefix="/api/v1/forecast-explorer/weather-overlay", tags=["weather-overlay"])


def build_weather_overlay_service() -> WeatherOverlayService:
    return WeatherOverlayService(
        repository=WeatherOverlayRepository(),
        geomet_client=GeoMetClient(),
        alignment_service=WeatherOverlayAlignmentService(),
    )


@router.get("", response_model=WeatherOverlayResponse)
def get_weather_overlay(
    geography_id: str = Query(alias="geographyId"),
    time_range_start: datetime = Query(alias="timeRangeStart"),
    time_range_end: datetime = Query(alias="timeRangeEnd"),
    weather_measure: str | None = Query(default=None, alias="weatherMeasure"),
    _claims: dict = Depends(require_visualization_reader),
) -> WeatherOverlayResponse:
    if time_range_end <= time_range_start:
        raise HTTPException(status_code=422, detail="timeRangeEnd must be later than timeRangeStart")
    if weather_measure not in {None, "temperature", "snowfall", "precipitation"}:
        raise HTTPException(status_code=422, detail="weatherMeasure must be one of temperature, snowfall, or precipitation")
    service = build_weather_overlay_service()
    return service.get_overlay(
        geography_id=geography_id,
        time_range_start=time_range_start,
        time_range_end=time_range_end,
        weather_measure=weather_measure,
    )


@router.post("/{overlay_request_id}/render-events", status_code=status.HTTP_202_ACCEPTED)
def record_weather_overlay_render_event(
    overlay_request_id: str,
    payload: WeatherOverlayRenderEvent,
    _claims: dict = Depends(require_visualization_reader),
) -> Response:
    service = build_weather_overlay_service()
    try:
        service.record_render_event(overlay_request_id, payload)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Overlay request not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_202_ACCEPTED)
