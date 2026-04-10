from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class ThresholdConfiguration(Base):
    __tablename__ = "threshold_configurations"

    threshold_configuration_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    service_category: Mapped[str] = mapped_column(String(255), nullable=False)
    geography_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    geography_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    forecast_window_type: Mapped[str] = mapped_column(String(32), nullable=False)
    threshold_value: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    notification_channels_json: Mapped[str] = mapped_column(Text, nullable=False)
    operational_manager_id: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "service_category",
            "geography_type",
            "geography_value",
            "forecast_window_type",
            "operational_manager_id",
            "effective_from",
            name="uq_threshold_configurations_scope_effective_from",
        ),
    )


class ThresholdEvaluationRun(Base):
    __tablename__ = "threshold_evaluation_runs"

    threshold_evaluation_run_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    forecast_run_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    forecast_version_reference: Mapped[str] = mapped_column(String(36), nullable=False)
    forecast_product: Mapped[str] = mapped_column(String(16), nullable=False)
    trigger_source: Mapped[str] = mapped_column(String(32), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="running")
    evaluated_scope_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    alert_created_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failure_summary: Mapped[str | None] = mapped_column(Text, nullable=True)


class ThresholdScopeEvaluation(Base):
    __tablename__ = "threshold_scope_evaluations"

    threshold_scope_evaluation_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    threshold_evaluation_run_id: Mapped[str] = mapped_column(
        ForeignKey("threshold_evaluation_runs.threshold_evaluation_run_id"),
        nullable=False,
    )
    threshold_configuration_id: Mapped[str | None] = mapped_column(
        ForeignKey("threshold_configurations.threshold_configuration_id"),
        nullable=True,
    )
    service_category: Mapped[str] = mapped_column(String(255), nullable=False)
    geography_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    geography_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    forecast_window_type: Mapped[str] = mapped_column(String(32), nullable=False)
    forecast_window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    forecast_window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    forecast_bucket_value: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    threshold_value: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    outcome: Mapped[str] = mapped_column(String(32), nullable=False)
    notification_event_id: Mapped[str | None] = mapped_column(
        ForeignKey("notification_events.notification_event_id"),
        nullable=True,
    )
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


class ThresholdState(Base):
    __tablename__ = "threshold_states"

    threshold_state_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    threshold_configuration_id: Mapped[str] = mapped_column(
        ForeignKey("threshold_configurations.threshold_configuration_id"),
        nullable=False,
    )
    service_category: Mapped[str] = mapped_column(String(255), nullable=False)
    geography_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    geography_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    forecast_window_type: Mapped[str] = mapped_column(String(32), nullable=False)
    forecast_window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    forecast_window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    current_state: Mapped[str] = mapped_column(String(32), nullable=False)
    last_forecast_bucket_value: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    last_threshold_value: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    last_evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    last_notification_event_id: Mapped[str | None] = mapped_column(
        ForeignKey("notification_events.notification_event_id"),
        nullable=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "service_category",
            "geography_type",
            "geography_value",
            "forecast_window_type",
            "forecast_window_start",
            "forecast_window_end",
            name="uq_threshold_states_scope_window",
        ),
    )


class NotificationEvent(Base):
    __tablename__ = "notification_events"

    notification_event_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    threshold_evaluation_run_id: Mapped[str] = mapped_column(
        ForeignKey("threshold_evaluation_runs.threshold_evaluation_run_id"),
        nullable=False,
    )
    threshold_configuration_id: Mapped[str] = mapped_column(
        ForeignKey("threshold_configurations.threshold_configuration_id"),
        nullable=False,
    )
    service_category: Mapped[str] = mapped_column(String(255), nullable=False)
    geography_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    geography_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    forecast_window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    forecast_window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    forecast_window_type: Mapped[str] = mapped_column(String(32), nullable=False)
    forecast_value: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    threshold_value: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    overall_delivery_status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    follow_up_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class NotificationChannelAttempt(Base):
    __tablename__ = "notification_channel_attempts"

    notification_channel_attempt_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    notification_event_id: Mapped[str] = mapped_column(
        ForeignKey("notification_events.notification_event_id"),
        nullable=False,
    )
    channel_type: Mapped[str] = mapped_column(String(32), nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
