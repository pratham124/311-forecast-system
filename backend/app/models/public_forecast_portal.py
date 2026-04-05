from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class PublicForecastPortalRequest(Base):
    __tablename__ = "public_forecast_portal_requests"

    public_forecast_request_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    approved_forecast_version_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    approved_forecast_product: Mapped[str | None] = mapped_column(String(16), nullable=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    portal_status: Mapped[str] = mapped_column(String(16), nullable=False, default="error")
    forecast_window_label: Mapped[str | None] = mapped_column(String(128), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    client_correlation_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class PublicForecastSanitizationOutcome(Base):
    __tablename__ = "public_forecast_sanitization_outcomes"

    public_forecast_sanitization_outcome_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    public_forecast_request_id: Mapped[str] = mapped_column(
        ForeignKey("public_forecast_portal_requests.public_forecast_request_id"),
        nullable=False,
        unique=True,
    )
    sanitization_status: Mapped[str] = mapped_column(String(16), nullable=False)
    restricted_detail_detected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    removed_detail_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sanitization_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class PublicForecastVisualizationPayload(Base):
    __tablename__ = "public_forecast_visualization_payloads"

    public_forecast_payload_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    public_forecast_request_id: Mapped[str] = mapped_column(
        ForeignKey("public_forecast_portal_requests.public_forecast_request_id"),
        nullable=False,
        unique=True,
    )
    approved_forecast_version_id: Mapped[str] = mapped_column(String(36), nullable=False)
    forecast_window_label: Mapped[str] = mapped_column(String(128), nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    coverage_status: Mapped[str] = mapped_column(String(16), nullable=False)
    coverage_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    category_summaries_json: Mapped[str] = mapped_column(Text, nullable=False)
    prepared_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class PublicForecastDisplayEvent(Base):
    __tablename__ = "public_forecast_display_events"

    public_forecast_display_event_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    public_forecast_request_id: Mapped[str] = mapped_column(
        ForeignKey("public_forecast_portal_requests.public_forecast_request_id"),
        nullable=False,
    )
    public_forecast_payload_id: Mapped[str | None] = mapped_column(
        ForeignKey("public_forecast_visualization_payloads.public_forecast_payload_id"),
        nullable=True,
    )
    display_outcome: Mapped[str] = mapped_column(String(16), nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    reported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
