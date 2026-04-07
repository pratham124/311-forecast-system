from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from app.schemas.weather_overlay import FailureCategory, OverlayStatus, StateSource, WeatherMeasure


@dataclass(slots=True)
class OverlaySelection:
    overlay_request_id: str
    geography_id: str
    time_range_start: datetime
    time_range_end: datetime
    overlay_enabled: bool
    weather_measure: WeatherMeasure | None
    requested_at: datetime


@dataclass(slots=True)
class OverlayStateRecord:
    overlay_request_id: str
    overlay_status: OverlayStatus
    geography_id: str
    time_range_start: datetime
    time_range_end: datetime
    weather_measure: WeatherMeasure | None
    status_message: str | None = None
    failure_category: FailureCategory | None = None
    state_source: StateSource = "overlay-assembly"
    last_updated_at: datetime = field(default_factory=datetime.utcnow)
