from __future__ import annotations

from dataclasses import dataclass


APPROVED_GEOGRAPHY_STATIONS: dict[str, str] = {
    "citywide": "edmonton-hourly",
    "downtown": "edmonton-hourly",
    "southwest": "edmonton-hourly",
    "northeast": "edmonton-hourly",
}


@dataclass(frozen=True, slots=True)
class AlignmentResult:
    supported: bool
    matched_geography_id: str | None
    station_id: str | None
    alignment_status: str
    message: str | None = None


class WeatherOverlayAlignmentService:
    def resolve(self, geography_id: str) -> AlignmentResult:
        token = geography_id.strip().lower()
        station = APPROVED_GEOGRAPHY_STATIONS.get(token)
        if station is None:
            return AlignmentResult(
                supported=False,
                matched_geography_id=None,
                station_id=None,
                alignment_status="misaligned",
                message="Weather overlay is unavailable for this geography.",
            )
        return AlignmentResult(
            supported=True,
            matched_geography_id=token,
            station_id=station,
            alignment_status="aligned",
            message=None,
        )
