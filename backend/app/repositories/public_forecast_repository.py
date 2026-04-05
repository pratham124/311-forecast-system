from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    PublicForecastDisplayEvent,
    PublicForecastPortalRequest,
    PublicForecastSanitizationOutcome,
    PublicForecastVisualizationPayload,
)


class PublicForecastRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_request(
        self,
        *,
        client_correlation_id: str | None,
        approved_forecast_version_id: str | None = None,
        approved_forecast_product: str | None = None,
    ) -> PublicForecastPortalRequest:
        record = PublicForecastPortalRequest(
            client_correlation_id=client_correlation_id,
            approved_forecast_version_id=approved_forecast_version_id,
            approved_forecast_product=approved_forecast_product,
            portal_status="error",
        )
        self.session.add(record)
        self.session.flush()
        return record

    def finalize_request(
        self,
        public_forecast_request_id: str,
        *,
        portal_status: str,
        approved_forecast_version_id: str | None = None,
        approved_forecast_product: str | None = None,
        forecast_window_label: str | None = None,
        published_at: datetime | None = None,
        failure_reason: str | None = None,
    ) -> PublicForecastPortalRequest:
        record = self.require_request(public_forecast_request_id)
        record.portal_status = portal_status
        record.approved_forecast_version_id = approved_forecast_version_id
        record.approved_forecast_product = approved_forecast_product
        record.forecast_window_label = forecast_window_label
        record.published_at = published_at
        record.failure_reason = failure_reason
        record.completed_at = datetime.utcnow()
        self.session.flush()
        return record

    def record_sanitization_outcome(
        self,
        *,
        public_forecast_request_id: str,
        sanitization_status: str,
        restricted_detail_detected: bool,
        removed_detail_count: int,
        sanitization_summary: str | None = None,
        failure_reason: str | None = None,
    ) -> PublicForecastSanitizationOutcome:
        record = self.session.scalar(
            select(PublicForecastSanitizationOutcome).where(
                PublicForecastSanitizationOutcome.public_forecast_request_id == public_forecast_request_id
            )
        )
        if record is None:
            record = PublicForecastSanitizationOutcome(
                public_forecast_request_id=public_forecast_request_id,
                sanitization_status=sanitization_status,
                restricted_detail_detected=restricted_detail_detected,
                removed_detail_count=removed_detail_count,
                sanitization_summary=sanitization_summary,
                failure_reason=failure_reason,
            )
            self.session.add(record)
        else:
            record.sanitization_status = sanitization_status
            record.restricted_detail_detected = restricted_detail_detected
            record.removed_detail_count = removed_detail_count
            record.sanitization_summary = sanitization_summary
            record.failure_reason = failure_reason
            record.evaluated_at = datetime.utcnow()
        self.session.flush()
        return record

    def create_payload(
        self,
        *,
        public_forecast_request_id: str,
        approved_forecast_version_id: str,
        forecast_window_label: str,
        published_at: datetime,
        coverage_status: str,
        coverage_message: str | None,
        category_summaries: list[dict[str, object]],
    ) -> PublicForecastVisualizationPayload:
        record = PublicForecastVisualizationPayload(
            public_forecast_request_id=public_forecast_request_id,
            approved_forecast_version_id=approved_forecast_version_id,
            forecast_window_label=forecast_window_label,
            published_at=published_at,
            coverage_status=coverage_status,
            coverage_message=coverage_message,
            category_summaries_json=json.dumps(category_summaries),
        )
        self.session.add(record)
        self.session.flush()
        return record

    def record_display_event(
        self,
        *,
        public_forecast_request_id: str,
        display_outcome: str,
        failure_reason: str | None = None,
    ) -> PublicForecastDisplayEvent:
        payload = self.session.scalar(
            select(PublicForecastVisualizationPayload).where(
                PublicForecastVisualizationPayload.public_forecast_request_id == public_forecast_request_id
            )
        )
        event = PublicForecastDisplayEvent(
            public_forecast_request_id=public_forecast_request_id,
            public_forecast_payload_id=payload.public_forecast_payload_id if payload is not None else None,
            display_outcome=display_outcome,
            failure_reason=failure_reason,
        )
        self.session.add(event)
        self.session.flush()
        return event

    def require_request(self, public_forecast_request_id: str) -> PublicForecastPortalRequest:
        record = self.session.get(PublicForecastPortalRequest, public_forecast_request_id)
        if record is None:
            raise LookupError("Public forecast request not found")
        return record
