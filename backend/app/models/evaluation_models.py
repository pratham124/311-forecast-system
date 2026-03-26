from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    evaluation_run_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    trigger_type: Mapped[str] = mapped_column(String(32), nullable=False)
    forecast_product_name: Mapped[str] = mapped_column(String(64), nullable=False)
    source_cleaned_dataset_version_id: Mapped[str | None] = mapped_column(
        ForeignKey("dataset_versions.dataset_version_id"),
        nullable=True,
    )
    source_forecast_version_id: Mapped[str | None] = mapped_column(
        ForeignKey("forecast_versions.forecast_version_id"),
        nullable=True,
    )
    source_weekly_forecast_version_id: Mapped[str | None] = mapped_column(
        ForeignKey("weekly_forecast_versions.weekly_forecast_version_id"),
        nullable=True,
    )
    evaluation_window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    evaluation_window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="running")
    result_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    evaluation_result_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    evaluation_result_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    evaluation_run_id: Mapped[str] = mapped_column(
        ForeignKey("evaluation_runs.evaluation_run_id"),
        nullable=False,
    )
    forecast_product_name: Mapped[str] = mapped_column(String(64), nullable=False)
    source_cleaned_dataset_version_id: Mapped[str] = mapped_column(
        ForeignKey("dataset_versions.dataset_version_id"),
        nullable=False,
    )
    source_forecast_version_id: Mapped[str | None] = mapped_column(
        ForeignKey("forecast_versions.forecast_version_id"),
        nullable=True,
    )
    source_weekly_forecast_version_id: Mapped[str | None] = mapped_column(
        ForeignKey("weekly_forecast_versions.weekly_forecast_version_id"),
        nullable=True,
    )
    evaluation_window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    evaluation_window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    comparison_status: Mapped[str] = mapped_column(String(16), nullable=False)
    baseline_methods_json: Mapped[str] = mapped_column(Text, nullable=False)
    metric_set_json: Mapped[str] = mapped_column(Text, nullable=False)
    storage_status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    comparison_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    stored_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class EvaluationSegment(Base):
    __tablename__ = "evaluation_segments"

    evaluation_segment_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    evaluation_result_id: Mapped[str] = mapped_column(
        ForeignKey("evaluation_results.evaluation_result_id"),
        nullable=False,
    )
    segment_type: Mapped[str] = mapped_column(String(32), nullable=False)
    segment_key: Mapped[str] = mapped_column(String(255), nullable=False)
    segment_status: Mapped[str] = mapped_column(String(16), nullable=False)
    comparison_row_count: Mapped[int] = mapped_column(Integer, nullable=False)
    excluded_metric_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class MetricComparisonValue(Base):
    __tablename__ = "metric_comparison_values"

    metric_comparison_value_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    evaluation_segment_id: Mapped[str] = mapped_column(
        ForeignKey("evaluation_segments.evaluation_segment_id"),
        nullable=False,
    )
    compared_method: Mapped[str] = mapped_column(String(32), nullable=False)
    compared_method_label: Mapped[str] = mapped_column(String(128), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(16), nullable=False)
    metric_value: Mapped[float | None] = mapped_column(Numeric(12, 4), nullable=True)
    is_excluded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    exclusion_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class CurrentEvaluationMarker(Base):
    __tablename__ = "current_evaluation_markers"

    forecast_product_name: Mapped[str] = mapped_column(String(64), primary_key=True)
    evaluation_result_id: Mapped[str] = mapped_column(
        ForeignKey("evaluation_results.evaluation_result_id"),
        nullable=False,
    )
    source_cleaned_dataset_version_id: Mapped[str] = mapped_column(
        ForeignKey("dataset_versions.dataset_version_id"),
        nullable=False,
    )
    source_forecast_version_id: Mapped[str | None] = mapped_column(
        ForeignKey("forecast_versions.forecast_version_id"),
        nullable=True,
    )
    source_weekly_forecast_version_id: Mapped[str | None] = mapped_column(
        ForeignKey("weekly_forecast_versions.weekly_forecast_version_id"),
        nullable=True,
    )
    evaluation_window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    evaluation_window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    comparison_status: Mapped[str] = mapped_column(String(16), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_by_run_id: Mapped[str] = mapped_column(
        ForeignKey("evaluation_runs.evaluation_run_id"),
        nullable=False,
    )
