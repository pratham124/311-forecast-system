from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from threading import Lock

from app.schemas.weather_overlay import WeatherOverlayRenderEvent, WeatherOverlayResponse


@dataclass(slots=True)
class OverlayRenderLog:
    overlay_request_id: str
    render_status: str
    reported_at: datetime
    failure_reason: str | None


class WeatherOverlayRepository:
    _lock = Lock()
    _states: dict[str, WeatherOverlayResponse] = {}
    _latest_request_id: str | None = None
    _render_logs: list[OverlayRenderLog] = []

    def begin_request(self, request_id: str) -> str | None:
        with self._lock:
            superseded = self._latest_request_id
            self._latest_request_id = request_id
            return superseded

    def clear_latest_request(self) -> None:
        with self._lock:
            self._latest_request_id = None

    def save_state(self, response: WeatherOverlayResponse) -> None:
        with self._lock:
            self._states[response.overlay_request_id] = response

    def get_state(self, overlay_request_id: str) -> WeatherOverlayResponse | None:
        with self._lock:
            return self._states.get(overlay_request_id)

    def mark_superseded(self, overlay_request_id: str) -> None:
        with self._lock:
            existing = self._states.get(overlay_request_id)
            if existing is None:
                return
            self._states[overlay_request_id] = existing.model_copy(
                update={
                    "overlay_status": "superseded",
                    "status_message": "A newer weather-overlay selection replaced this request.",
                    "failure_category": "superseded",
                    "state_source": "overlay-assembly",
                    "observations": [],
                }
            )

    def append_render_event(self, overlay_request_id: str, payload: WeatherOverlayRenderEvent) -> None:
        with self._lock:
            self._render_logs.append(
                OverlayRenderLog(
                    overlay_request_id=overlay_request_id,
                    render_status=payload.render_status,
                    reported_at=payload.reported_at,
                    failure_reason=payload.failure_reason,
                )
            )

    def list_render_events(self, overlay_request_id: str) -> list[OverlayRenderLog]:
        with self._lock:
            return [event for event in self._render_logs if event.overlay_request_id == overlay_request_id]

    @classmethod
    def reset_for_tests(cls) -> None:
        with cls._lock:
            cls._states = {}
            cls._latest_request_id = None
            cls._render_logs = []
