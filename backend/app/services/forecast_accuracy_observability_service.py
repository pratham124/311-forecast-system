from __future__ import annotations

import logging

from fastapi import HTTPException, status

from app.core.logging import summarize_status
from app.repositories.forecast_accuracy_repository import ForecastAccuracyRepository
from app.schemas.forecast_accuracy import ForecastAccuracyRenderEvent, ForecastAccuracyRenderEventResponse


class ForecastAccuracyObservabilityService:
    def __init__(self, repository: ForecastAccuracyRepository, logger: logging.Logger | None = None) -> None:
        self.repository = repository
        self.logger = logger or logging.getLogger("forecast_accuracy.observability")

    def log_event(self, event: str, **fields) -> None:
        self.logger.info("%s", summarize_status(event, **fields))

    def record_render_event(
        self,
        *,
        forecast_accuracy_request_id: str,
        payload: ForecastAccuracyRenderEvent,
        claims: dict,
    ) -> ForecastAccuracyRenderEventResponse:
        request = self.repository.require_request(forecast_accuracy_request_id)
        result = self.repository.get_result_by_request(forecast_accuracy_request_id)
        if result is None:
            raise LookupError("Forecast accuracy result not found")
        roles = claims.get("roles", [])
        subject = str(claims.get("sub") or "")
        if "OperationalManager" not in roles and request.requested_by_subject != subject:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        self.repository.create_render_event(
            forecast_accuracy_request_id=forecast_accuracy_request_id,
            forecast_accuracy_result_id=result.forecast_accuracy_result_id,
            render_outcome=payload.render_status,
            failure_reason=payload.failure_reason,
            reported_by_subject=subject,
        )
        if payload.render_status == "render_failed":
            self.repository.finalize_request(
                forecast_accuracy_request_id,
                status="render_failed",
                failure_reason=payload.failure_reason,
                render_reported=True,
            )
            self.log_event(
                "forecast_accuracy.render_failed",
                forecast_accuracy_request_id=forecast_accuracy_request_id,
                failure_reason=payload.failure_reason,
            )
            return ForecastAccuracyRenderEventResponse(
                forecastAccuracyRequestId=forecast_accuracy_request_id,
                recordedOutcomeStatus="render_failed",
                message="Render failure recorded.",
            )
        self.repository.finalize_request(
            forecast_accuracy_request_id,
            status=request.status,
            failure_reason=request.failure_reason,
            render_reported=True,
        )
        self.log_event("forecast_accuracy.rendered", forecast_accuracy_request_id=forecast_accuracy_request_id)
        return ForecastAccuracyRenderEventResponse(
            forecastAccuracyRequestId=forecast_accuracy_request_id,
            recordedOutcomeStatus="rendered",
            message="Render success recorded.",
        )
