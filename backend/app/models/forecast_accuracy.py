from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class ForecastAccuracyRequest(Base):
    __tablename__ = "forecast_accuracy_requests"

    forecast_accuracy_request_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    requested_by_actor: Mapped[str] = mapped_column(String(32), nullable=False)
    requested_by_subject: Mapped[str] = mapped_column(String(255), nullable=False)
    source_cleaned_dataset_version_id: Mapped[str | None] = mapped_column(
        ForeignKey("dataset_versions.dataset_version_id"),
        nullable=True,
    )
    source_forecast_version_id: Mapped[str | None] = mapped_column(
        ForeignKey("forecast_versions.forecast_version_id"),
        nullable=True,
    )
    source_evaluation_result_id: Mapped[str | None] = mapped_column(
        ForeignKey("evaluation_results.evaluation_result_id"),
        nullable=True,
    )
    forecast_product_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    comparison_granularity: Mapped[str] = mapped_column(String(16), nullable=False)
    time_range_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    time_range_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    service_category: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="running")
    correlation_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    render_reported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ForecastAccuracyMetricResolution(Base):
    __tablename__ = "forecast_accuracy_metric_resolutions"

    forecast_accuracy_metric_resolution_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    forecast_accuracy_request_id: Mapped[str] = mapped_column(
        ForeignKey("forecast_accuracy_requests.forecast_accuracy_request_id"),
        nullable=False,
        unique=True,
    )
    source_evaluation_result_id: Mapped[str | None] = mapped_column(
        ForeignKey("evaluation_results.evaluation_result_id"),
        nullable=True,
    )
    resolution_status: Mapped[str] = mapped_column(String(32), nullable=False)
    metric_names_json: Mapped[str] = mapped_column(Text, nullable=False)
    metric_values_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    status_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class ForecastAccuracyComparisonResult(Base):
    __tablename__ = "forecast_accuracy_results"

    forecast_accuracy_result_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    forecast_accuracy_request_id: Mapped[str] = mapped_column(
        ForeignKey("forecast_accuracy_requests.forecast_accuracy_request_id"),
        nullable=False,
        unique=True,
    )
    view_status: Mapped[str] = mapped_column(String(32), nullable=False)
    metric_resolution_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    aligned_bucket_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    excluded_bucket_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    stored_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class ForecastAccuracyAlignedBucket(Base):
    __tablename__ = "forecast_accuracy_aligned_buckets"

    forecast_accuracy_aligned_bucket_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    forecast_accuracy_result_id: Mapped[str] = mapped_column(
        ForeignKey("forecast_accuracy_results.forecast_accuracy_result_id"),
        nullable=False,
    )
    bucket_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    bucket_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    service_category: Mapped[str | None] = mapped_column(String(255), nullable=True)
    forecast_value: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    actual_value: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    absolute_error_value: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    percentage_error_value: Mapped[float | None] = mapped_column(Numeric(12, 4), nullable=True)


class ForecastAccuracyRenderEvent(Base):
    __tablename__ = "forecast_accuracy_render_events"

    forecast_accuracy_render_event_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    forecast_accuracy_request_id: Mapped[str] = mapped_column(
        ForeignKey("forecast_accuracy_requests.forecast_accuracy_request_id"),
        nullable=False,
    )
    forecast_accuracy_result_id: Mapped[str] = mapped_column(
        ForeignKey("forecast_accuracy_results.forecast_accuracy_result_id"),
        nullable=False,
    )
    render_outcome: Mapped[str] = mapped_column(String(32), nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    reported_by_subject: Mapped[str] = mapped_column(String(255), nullable=False)
    reported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
