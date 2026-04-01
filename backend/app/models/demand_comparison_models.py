from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class DemandComparisonRequest(Base):
    __tablename__ = "demand_comparison_requests"

    comparison_request_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
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
    source_weekly_forecast_version_id: Mapped[str | None] = mapped_column(
        ForeignKey("weekly_forecast_versions.weekly_forecast_version_id"),
        nullable=True,
    )
    forecast_product_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    forecast_granularity: Mapped[str | None] = mapped_column(String(16), nullable=True)
    geography_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    service_category_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    geography_value_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    time_range_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    time_range_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    warning_status: Mapped[str] = mapped_column(String(16), nullable=False, default="not_needed")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="running")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    render_reported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class DemandComparisonResult(Base):
    __tablename__ = "demand_comparison_results"

    comparison_result_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    comparison_request_id: Mapped[str] = mapped_column(
        ForeignKey("demand_comparison_requests.comparison_request_id"),
        nullable=False,
        unique=True,
    )
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
    forecast_product_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    forecast_granularity: Mapped[str | None] = mapped_column(String(16), nullable=True)
    result_mode: Mapped[str] = mapped_column(String(16), nullable=False)
    comparison_granularity: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    stored_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class DemandComparisonSeriesPoint(Base):
    __tablename__ = "demand_comparison_series_points"

    comparison_point_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    comparison_result_id: Mapped[str] = mapped_column(
        ForeignKey("demand_comparison_results.comparison_result_id"),
        nullable=False,
    )
    series_type: Mapped[str] = mapped_column(String(16), nullable=False)
    bucket_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    bucket_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    service_category: Mapped[str] = mapped_column(String(255), nullable=False)
    geography_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    value: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)


class ComparisonMissingCombination(Base):
    __tablename__ = "comparison_missing_combinations"

    missing_combination_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    comparison_result_id: Mapped[str] = mapped_column(
        ForeignKey("demand_comparison_results.comparison_result_id"),
        nullable=False,
    )
    service_category: Mapped[str] = mapped_column(String(255), nullable=False)
    geography_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    missing_source: Mapped[str] = mapped_column(String(32), nullable=False, default="forecast")
    message: Mapped[str] = mapped_column(Text, nullable=False)


class DemandComparisonOutcomeRecord(Base):
    __tablename__ = "demand_comparison_outcome_records"

    comparison_outcome_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    comparison_request_id: Mapped[str] = mapped_column(
        ForeignKey("demand_comparison_requests.comparison_request_id"),
        nullable=False,
        unique=True,
    )
    outcome_type: Mapped[str] = mapped_column(String(32), nullable=False)
    warning_acknowledged: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    message: Mapped[str] = mapped_column(Text, nullable=False)
