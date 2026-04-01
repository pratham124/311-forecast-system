from __future__ import annotations

import logging

from fastapi import HTTPException, status

from app.core.demand_comparison_observability import (
    summarize_demand_comparison_failure,
    summarize_demand_comparison_success,
)
from app.repositories.demand_comparison_repository import DemandComparisonRepository
from app.schemas.demand_comparison_api import DemandComparisonRenderEvent, DemandComparisonRenderEventResponse


class DemandComparisonRenderService:
    def __init__(self, repository: DemandComparisonRepository, logger: logging.Logger | None = None) -> None:
        self.repository = repository
        self.logger = logger or logging.getLogger("demand_comparison.render")

    def record_event(
        self,
        *,
        comparison_request_id: str,
        payload: DemandComparisonRenderEvent,
        claims: dict,
    ) -> DemandComparisonRenderEventResponse:
        request = self.repository.require_request(comparison_request_id)
        roles = claims.get("roles", [])
        subject = str(claims.get("sub") or "")
        if "OperationalManager" not in roles and request.requested_by_subject != subject:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        if payload.render_status == "render_failed":
            self.repository.finalize_request(
                comparison_request_id,
                status="render_failed",
                failure_reason=payload.failure_reason,
                render_reported=True,
            )
            self.repository.upsert_outcome(
                comparison_request_id=comparison_request_id,
                outcome_type="render_failed",
                warning_acknowledged=request.warning_status == "acknowledged",
                message=payload.failure_reason or "Demand comparison render failed.",
            )
            self.logger.info(
                "%s",
                summarize_demand_comparison_failure(
                    "demand_comparison.render_failed",
                    comparison_request_id=comparison_request_id,
                    failure_reason=payload.failure_reason,
                ),
            )
            return DemandComparisonRenderEventResponse(
                comparisonRequestId=comparison_request_id,
                recordedOutcomeStatus="render_failed",
                message="Render failure recorded.",
            )
        self.repository.finalize_request(
            comparison_request_id,
            status=request.status,
            warning_status=request.warning_status,
            failure_reason=request.failure_reason,
            render_reported=True,
        )
        self.repository.upsert_outcome(
            comparison_request_id=comparison_request_id,
            outcome_type=request.status,
            warning_acknowledged=request.warning_status == "acknowledged",
            message="Demand comparison rendered successfully.",
        )
        self.logger.info(
            "%s",
            summarize_demand_comparison_success(
                "demand_comparison.render_succeeded",
                comparison_request_id=comparison_request_id,
            ),
        )
        return DemandComparisonRenderEventResponse(
            comparisonRequestId=comparison_request_id,
            recordedOutcomeStatus="rendered",
            message="Render success recorded.",
        )
