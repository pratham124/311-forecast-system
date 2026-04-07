from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


WeatherMeasure = Literal["temperature", "snowfall"]
OverlayStatus = Literal[
    "disabled",
    "loading",
    "visible",
    "unavailable",
    "retrieval-failed",
    "misaligned",
    "superseded",
    "failed-to-render",
]
FailureCategory = Literal[
    "weather-missing",
    "retrieval-failed",
    "misaligned",
    "failed-to-render",
    "superseded",
]
StateSource = Literal["selection-read-model", "overlay-assembly", "render-event"]


class WeatherObservationPoint(BaseModel):
    timestamp: datetime
    value: float


class WeatherOverlaySource(BaseModel):
    provider: Literal["msc_geomet"]
    station_id: str | None = Field(default=None, alias="stationId")
    alignment_status: Literal["aligned", "misaligned", "not-applicable"] = Field(alias="alignmentStatus")

    model_config = ConfigDict(populate_by_name=True)


class WeatherOverlayResponse(BaseModel):
    overlay_request_id: str = Field(alias="overlayRequestId")
    geography_id: str = Field(alias="geographyId")
    matched_geography_id: str | None = Field(default=None, alias="matchedGeographyId")
    time_range_start: datetime = Field(alias="timeRangeStart")
    time_range_end: datetime = Field(alias="timeRangeEnd")
    weather_measure: WeatherMeasure | None = Field(default=None, alias="weatherMeasure")
    measurement_unit: str | None = Field(default=None, alias="measurementUnit")
    overlay_status: OverlayStatus = Field(alias="overlayStatus")
    status_message: str | None = Field(default=None, alias="statusMessage")
    base_forecast_preserved: Literal[True] = Field(default=True, alias="baseForecastPreserved")
    user_visible: Literal[True] = Field(default=True, alias="userVisible")
    observation_granularity: Literal["hourly", "daily"] | None = Field(default=None, alias="observationGranularity")
    observations: list[WeatherObservationPoint] = Field(default_factory=list)
    source: WeatherOverlaySource | None = None
    failure_category: FailureCategory | None = Field(default=None, alias="failureCategory")
    state_source: StateSource = Field(alias="stateSource")
    rendered_at: datetime | None = Field(default=None, alias="renderedAt")

    model_config = ConfigDict(populate_by_name=True)


class WeatherOverlayRenderEvent(BaseModel):
    render_status: Literal["rendered", "failed-to-render"] = Field(alias="renderStatus")
    reported_at: datetime = Field(alias="reportedAt")
    failure_reason: str | None = Field(default=None, alias="failureReason")

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode="after")
    def validate_failure_reason(self):
        if self.render_status == "failed-to-render" and not self.failure_reason:
            raise ValueError("failureReason is required when renderStatus is failed-to-render")
        return self
