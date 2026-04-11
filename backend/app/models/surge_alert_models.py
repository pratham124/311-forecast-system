from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class SurgeDetectionConfiguration(Base):
    __tablename__ = "surge_detection_configurations"

    surge_detection_configuration_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    service_category: Mapped[str] = mapped_column(String(255), nullable=False)
    forecast_product: Mapped[str] = mapped_column(String(16), nullable=False, default="daily")
    z_score_threshold: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    percent_above_forecast_floor: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    rolling_baseline_window_count: Mapped[int] = mapped_column(Integer, nullable=False, default=7)
    notification_channels_json: Mapped[str] = mapped_column(Text, nullable=False)
    operational_manager_id: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "service_category",
            "forecast_product",
            "operational_manager_id",
            "effective_from",
            name="uq_surge_detection_configurations_scope_effective_from",
        ),
    )


class SurgeEvaluationRun(Base):
    __tablename__ = "surge_evaluation_runs"

    surge_evaluation_run_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    ingestion_run_id: Mapped[str] = mapped_column(ForeignKey("ingestion_runs.run_id"), nullable=False)
    trigger_source: Mapped[str] = mapped_column(String(32), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="running")
    evaluated_scope_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    candidate_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    confirmed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    notification_created_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failure_summary: Mapped[str | None] = mapped_column(Text, nullable=True)


class SurgeCandidate(Base):
    __tablename__ = "surge_candidates"

    surge_candidate_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    surge_evaluation_run_id: Mapped[str] = mapped_column(
        ForeignKey("surge_evaluation_runs.surge_evaluation_run_id"),
        nullable=False,
    )
    surge_detection_configuration_id: Mapped[str | None] = mapped_column(
        ForeignKey("surge_detection_configurations.surge_detection_configuration_id"),
        nullable=True,
    )
    forecast_run_id: Mapped[str | None] = mapped_column(ForeignKey("forecast_runs.forecast_run_id"), nullable=True)
    forecast_version_id: Mapped[str | None] = mapped_column(ForeignKey("forecast_versions.forecast_version_id"), nullable=True)
    service_category: Mapped[str] = mapped_column(String(255), nullable=False)
    evaluation_window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    evaluation_window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actual_demand_value: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    forecast_p50_value: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    residual_value: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    residual_z_score: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    percent_above_forecast: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    rolling_baseline_mean: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    rolling_baseline_stddev: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    candidate_status: Mapped[str] = mapped_column(String(32), nullable=False)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    correlation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class SurgeNotificationEvent(Base):
    __tablename__ = "surge_notification_events"

    surge_notification_event_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    surge_evaluation_run_id: Mapped[str] = mapped_column(
        ForeignKey("surge_evaluation_runs.surge_evaluation_run_id"),
        nullable=False,
    )
    surge_candidate_id: Mapped[str] = mapped_column(ForeignKey("surge_candidates.surge_candidate_id"), nullable=False)
    surge_detection_configuration_id: Mapped[str] = mapped_column(
        ForeignKey("surge_detection_configurations.surge_detection_configuration_id"),
        nullable=False,
    )
    service_category: Mapped[str] = mapped_column(String(255), nullable=False)
    forecast_product: Mapped[str] = mapped_column(String(16), nullable=False, default="daily")
    evaluation_window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    evaluation_window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actual_demand_value: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    forecast_p50_value: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    residual_value: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    residual_z_score: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    percent_above_forecast: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    overall_delivery_status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    follow_up_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)


class SurgeConfirmationOutcome(Base):
    __tablename__ = "surge_confirmation_outcomes"

    surge_confirmation_outcome_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    surge_candidate_id: Mapped[str] = mapped_column(ForeignKey("surge_candidates.surge_candidate_id"), nullable=False)
    outcome: Mapped[str] = mapped_column(String(32), nullable=False)
    z_score_check_passed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    percent_floor_check_passed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    surge_notification_event_id: Mapped[str | None] = mapped_column(
        ForeignKey("surge_notification_events.surge_notification_event_id"),
        nullable=True,
    )
    confirmed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class SurgeState(Base):
    __tablename__ = "surge_states"

    surge_state_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    surge_detection_configuration_id: Mapped[str] = mapped_column(
        ForeignKey("surge_detection_configurations.surge_detection_configuration_id"),
        nullable=False,
    )
    service_category: Mapped[str] = mapped_column(String(255), nullable=False)
    forecast_product: Mapped[str] = mapped_column(String(16), nullable=False, default="daily")
    current_state: Mapped[str] = mapped_column(String(32), nullable=False, default="normal")
    notification_armed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    active_since: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    returned_to_normal_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_surge_candidate_id: Mapped[str | None] = mapped_column(ForeignKey("surge_candidates.surge_candidate_id"), nullable=True)
    last_confirmation_outcome_id: Mapped[str | None] = mapped_column(
        ForeignKey("surge_confirmation_outcomes.surge_confirmation_outcome_id"),
        nullable=True,
    )
    last_notification_event_id: Mapped[str | None] = mapped_column(
        ForeignKey("surge_notification_events.surge_notification_event_id"),
        nullable=True,
    )
    last_evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("service_category", "forecast_product", name="uq_surge_states_scope"),
    )


class SurgeNotificationChannelAttempt(Base):
    __tablename__ = "surge_notification_channel_attempts"

    surge_notification_channel_attempt_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    surge_notification_event_id: Mapped[str] = mapped_column(
        ForeignKey("surge_notification_events.surge_notification_event_id"),
        nullable=False,
    )
    channel_type: Mapped[str] = mapped_column(String(32), nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
