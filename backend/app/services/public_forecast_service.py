from __future__ import annotations

import logging

from app.core.logging import (
    summarize_public_forecast_error,
    summarize_public_forecast_event,
    summarize_public_forecast_success,
)
from app.repositories.public_forecast_repository import PublicForecastRepository
from app.schemas.public_forecast import PublicForecastCategorySummary, PublicForecastDisplayEventRequest, PublicForecastView
from app.services.public_forecast_sanitization_service import PublicForecastSanitizationService
from app.services.public_forecast_source_service import PublicForecastSourceService


def _coverage_message(removed_categories: list[str]) -> str:
    if not removed_categories:
        return "Some forecast categories are unavailable in the current public view."
    names = ", ".join(removed_categories[:3])
    suffix = "" if len(removed_categories) <= 3 else ", and more"
    return f"Some categories are not shown in this public forecast: {names}{suffix}."


def _demand_level(value: float, forecast_product: str) -> str:
    if forecast_product == "weekly":
        if value >= 400:
            return "Very high demand expected"
        if value >= 200:
            return "High demand expected"
        if value >= 80:
            return "Moderate demand expected"
        return "Lower demand expected"
    if value >= 100:
        return "Very high demand expected"
    if value >= 50:
        return "High demand expected"
    if value >= 20:
        return "Moderate demand expected"
    return "Lower demand expected"


class PublicForecastService:
    def __init__(
        self,
        *,
        repository: PublicForecastRepository,
        source_service: PublicForecastSourceService,
        sanitization_service: PublicForecastSanitizationService,
        logger: logging.Logger | None = None,
    ) -> None:
        self.repository = repository
        self.source_service = source_service
        self.sanitization_service = sanitization_service
        self.logger = logger or logging.getLogger("public_forecast")

    def get_current_public_forecast(self, *, client_correlation_id: str | None, forecast_product: str = "daily") -> PublicForecastView:
        request = self.repository.create_request(client_correlation_id=client_correlation_id)
        self.logger.info(
            "%s",
            summarize_public_forecast_event(
                "public_forecast.request_started",
                public_forecast_request_id=request.public_forecast_request_id,
                client_correlation_id=client_correlation_id,
            ),
        )
        try:
            source = self.source_service.resolve_current_source(forecast_product=forecast_product)
            if source is None:
                self.repository.record_sanitization_outcome(
                    public_forecast_request_id=request.public_forecast_request_id,
                    sanitization_status="failed",
                    restricted_detail_detected=False,
                    removed_detail_count=0,
                    failure_reason=f"No approved {forecast_product} public forecast is currently available.",
                )
                self.repository.finalize_request(
                    request.public_forecast_request_id,
                    portal_status="unavailable",
                    failure_reason=f"No approved {forecast_product} public forecast is currently available.",
                )
                return PublicForecastView(
                    publicForecastRequestId=request.public_forecast_request_id,
                    status="unavailable",
                    statusMessage=f"No approved {forecast_product} public forecast is currently available.",
                    clientCorrelationId=client_correlation_id,
                )

            request = self.repository.finalize_request(
                request.public_forecast_request_id,
                portal_status="error",
                approved_forecast_version_id=source.approved_forecast_version_id,
                approved_forecast_product=source.forecast_product,
            )
            sanitized = self.sanitization_service.sanitize(source)
            self.repository.record_sanitization_outcome(
                public_forecast_request_id=request.public_forecast_request_id,
                sanitization_status=sanitized.sanitization_status,
                restricted_detail_detected=sanitized.restricted_detail_detected,
                removed_detail_count=sanitized.removed_detail_count,
                sanitization_summary=sanitized.sanitization_summary,
                failure_reason=sanitized.failure_reason,
            )
            if sanitized.sanitization_status in {"blocked", "failed"}:
                self.repository.finalize_request(
                    request.public_forecast_request_id,
                    portal_status="error",
                    approved_forecast_version_id=source.approved_forecast_version_id,
                    approved_forecast_product=source.forecast_product,
                    failure_reason=sanitized.failure_reason,
                )
                self.logger.info(
                    "%s",
                    summarize_public_forecast_error(
                        "public_forecast.preparation_failed",
                        public_forecast_request_id=request.public_forecast_request_id,
                        failure_reason=sanitized.failure_reason,
                    ),
                )
                return PublicForecastView(
                    publicForecastRequestId=request.public_forecast_request_id,
                    status="error",
                    statusMessage=sanitized.failure_reason or "The public forecast could not be prepared.",
                    clientCorrelationId=client_correlation_id,
                )

            category_summaries = [
                PublicForecastCategorySummary(
                    serviceCategory=row.service_category,
                    forecastDemandValue=round(row.forecast_demand_value, 2),
                    demandLevelSummary=_demand_level(row.forecast_demand_value, source.forecast_product),
                )
                for row in sanitized.category_rows
            ]
            coverage_status = "incomplete" if sanitized.removed_categories or len(category_summaries) < source.source_category_count else "complete"
            coverage_message = _coverage_message(sanitized.removed_categories) if coverage_status == "incomplete" else None
            self.repository.create_payload(
                public_forecast_request_id=request.public_forecast_request_id,
                approved_forecast_version_id=source.approved_forecast_version_id,
                forecast_window_label=source.forecast_window_label,
                published_at=source.published_at,
                coverage_status=coverage_status,
                coverage_message=coverage_message,
                category_summaries=[item.model_dump(by_alias=True, mode="json") for item in category_summaries],
            )
            self.repository.finalize_request(
                request.public_forecast_request_id,
                portal_status="available",
                approved_forecast_version_id=source.approved_forecast_version_id,
                approved_forecast_product=source.forecast_product,
                forecast_window_label=source.forecast_window_label,
                published_at=source.published_at,
            )
            self.logger.info(
                "%s",
                summarize_public_forecast_success(
                    "public_forecast.available",
                    public_forecast_request_id=request.public_forecast_request_id,
                    approved_forecast_version_id=source.approved_forecast_version_id,
                    coverage_status=coverage_status,
                    sanitization_status=sanitized.sanitization_status,
                    category_count=len(category_summaries),
                ),
            )
            return PublicForecastView(
                publicForecastRequestId=request.public_forecast_request_id,
                status="available",
                forecastWindowLabel=source.forecast_window_label,
                publishedAt=source.published_at,
                coverageStatus=coverage_status,
                coverageMessage=coverage_message,
                sanitizationStatus=sanitized.sanitization_status,
                sanitizationSummary=sanitized.sanitization_summary,
                categorySummaries=category_summaries,
                clientCorrelationId=client_correlation_id,
            )
        except Exception as exc:
            self.repository.record_sanitization_outcome(
                public_forecast_request_id=request.public_forecast_request_id,
                sanitization_status="failed",
                restricted_detail_detected=False,
                removed_detail_count=0,
                failure_reason=str(exc),
            )
            self.repository.finalize_request(
                request.public_forecast_request_id,
                portal_status="error",
                failure_reason=str(exc),
            )
            self.logger.exception(
                "%s",
                summarize_public_forecast_error(
                    "public_forecast.request_failed",
                    public_forecast_request_id=request.public_forecast_request_id,
                    failure_reason=str(exc),
                ),
            )
            return PublicForecastView(
                publicForecastRequestId=request.public_forecast_request_id,
                status="error",
                statusMessage="The public forecast is temporarily unavailable.",
                clientCorrelationId=client_correlation_id,
            )

    def record_display_event(self, public_forecast_request_id: str, payload: PublicForecastDisplayEventRequest) -> None:
        self.repository.require_request(public_forecast_request_id)
        self.repository.record_display_event(
            public_forecast_request_id=public_forecast_request_id,
            display_outcome=payload.display_outcome,
            failure_reason=payload.failure_reason,
        )
        logger_fn = summarize_public_forecast_success if payload.display_outcome == "rendered" else summarize_public_forecast_error
        self.logger.info(
            "%s",
            logger_fn(
                "public_forecast.display_event",
                public_forecast_request_id=public_forecast_request_id,
                display_outcome=payload.display_outcome,
                failure_reason=payload.failure_reason,
            ),
        )
