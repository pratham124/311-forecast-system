from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class WeeklyForecastRun(Base):
    __tablename__ = "weekly_forecast_runs"

    weekly_forecast_run_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    trigger_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source_cleaned_dataset_version_id: Mapped[str | None] = mapped_column(
        ForeignKey("dataset_versions.dataset_version_id"),
        nullable=True,
    )
    week_start_local: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    week_end_local: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="running")
    result_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    generated_forecast_version_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    served_forecast_version_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    geography_scope: Mapped[str | None] = mapped_column(String(32), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)


class WeeklyForecastVersion(Base):
    __tablename__ = "weekly_forecast_versions"

    weekly_forecast_version_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    weekly_forecast_run_id: Mapped[str] = mapped_column(
        ForeignKey("weekly_forecast_runs.weekly_forecast_run_id"),
        nullable=False,
    )
    source_cleaned_dataset_version_id: Mapped[str] = mapped_column(
        ForeignKey("dataset_versions.dataset_version_id"),
        nullable=False,
    )
    week_start_local: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    week_end_local: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    bucket_granularity: Mapped[str] = mapped_column(String(16), nullable=False, default="daily")
    bucket_count_days: Mapped[int] = mapped_column(Integer, nullable=False, default=7)
    geography_scope: Mapped[str] = mapped_column(String(32), nullable=False)
    baseline_method: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    stored_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)


class WeeklyForecastBucket(Base):
    __tablename__ = "weekly_forecast_buckets"

    weekly_forecast_bucket_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    weekly_forecast_version_id: Mapped[str] = mapped_column(
        ForeignKey("weekly_forecast_versions.weekly_forecast_version_id"),
        nullable=False,
    )
    forecast_date_local: Mapped[date] = mapped_column(Date, nullable=False)
    service_category: Mapped[str] = mapped_column(String(255), nullable=False)
    geography_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    point_forecast: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    quantile_p10: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    quantile_p50: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    quantile_p90: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    baseline_value: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)


class CurrentWeeklyForecastMarker(Base):
    __tablename__ = "current_weekly_forecast_markers"

    forecast_product_name: Mapped[str] = mapped_column(String(64), primary_key=True)
    weekly_forecast_version_id: Mapped[str] = mapped_column(
        ForeignKey("weekly_forecast_versions.weekly_forecast_version_id"),
        nullable=False,
    )
    source_cleaned_dataset_version_id: Mapped[str] = mapped_column(
        ForeignKey("dataset_versions.dataset_version_id"),
        nullable=False,
    )
    week_start_local: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    week_end_local: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    geography_scope: Mapped[str] = mapped_column(String(32), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_by_run_id: Mapped[str] = mapped_column(
        ForeignKey("weekly_forecast_runs.weekly_forecast_run_id"),
        nullable=False,
    )
