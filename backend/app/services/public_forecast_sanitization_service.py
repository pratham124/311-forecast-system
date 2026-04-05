from __future__ import annotations

from dataclasses import dataclass

from app.services.public_forecast_source_service import PublicForecastBucketRow, ResolvedPublicForecastSource


@dataclass(frozen=True)
class SanitizedPublicForecast:
    sanitization_status: str
    restricted_detail_detected: bool
    removed_detail_count: int
    sanitization_summary: str | None
    failure_reason: str | None
    category_rows: list[PublicForecastBucketRow]
    removed_categories: list[str]


class PublicForecastSanitizationService:
    def sanitize(self, source: ResolvedPublicForecastSource) -> SanitizedPublicForecast:
        safe_rows: list[PublicForecastBucketRow] = []
        removed_rows = 0
        removed_categories: set[str] = set()
        for row in source.category_rows:
            if row.geography_key:
                removed_rows += 1
                removed_categories.add(row.service_category)
                continue
            safe_rows.append(row)

        if not safe_rows:
            return SanitizedPublicForecast(
                sanitization_status="blocked" if removed_rows else "failed",
                restricted_detail_detected=removed_rows > 0,
                removed_detail_count=removed_rows,
                sanitization_summary=None,
                failure_reason="Forecast data could not be prepared safely for public display.",
                category_rows=[],
                removed_categories=sorted(removed_categories),
            )

        if removed_rows:
            return SanitizedPublicForecast(
                sanitization_status="sanitized",
                restricted_detail_detected=True,
                removed_detail_count=removed_rows,
                sanitization_summary=f"Removed {removed_rows} restricted forecast detail records before publication.",
                failure_reason=None,
                category_rows=safe_rows,
                removed_categories=sorted(removed_categories),
            )

        return SanitizedPublicForecast(
            sanitization_status="passed_as_is",
            restricted_detail_detected=False,
            removed_detail_count=0,
            sanitization_summary=None,
            failure_reason=None,
            category_rows=safe_rows,
            removed_categories=[],
        )
