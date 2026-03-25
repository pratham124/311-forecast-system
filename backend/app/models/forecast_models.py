from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class ForecastRun(Base):
    __tablename__ = "forecast_runs"

    forecast_run_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    trigger_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source_cleaned_dataset_version_id: Mapped[str | None] = mapped_column(
        ForeignKey("dataset_versions.dataset_version_id"),
        nullable=True,
    )
    weather_enrichment_source: Mapped[str | None] = mapped_column(String(32), nullable=True)
    holiday_enrichment_source: Mapped[str | None] = mapped_column(String(32), nullable=True)
    requested_horizon_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    requested_horizon_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="running")
    result_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    forecast_version_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    served_forecast_version_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    geography_scope: Mapped[str | None] = mapped_column(String(32), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)


class ForecastVersion(Base):
    __tablename__ = "forecast_versions"

    forecast_version_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    forecast_run_id: Mapped[str] = mapped_column(ForeignKey("forecast_runs.forecast_run_id"), nullable=False)
    source_cleaned_dataset_version_id: Mapped[str] = mapped_column(
        ForeignKey("dataset_versions.dataset_version_id"),
        nullable=False,
    )
    weather_enrichment_source: Mapped[str | None] = mapped_column(String(32), nullable=True)
    holiday_enrichment_source: Mapped[str | None] = mapped_column(String(32), nullable=True)
    horizon_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    horizon_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    bucket_granularity: Mapped[str] = mapped_column(String(16), nullable=False, default="hourly")
    bucket_count: Mapped[int] = mapped_column(Integer, nullable=False, default=24)
    geography_scope: Mapped[str] = mapped_column(String(32), nullable=False)
    model_family: Mapped[str] = mapped_column(String(32), nullable=False, default="lightgbm_global")
    baseline_method: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    stored_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)


class ForecastBucket(Base):
    __tablename__ = "forecast_buckets"

    forecast_bucket_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    forecast_version_id: Mapped[str] = mapped_column(
        ForeignKey("forecast_versions.forecast_version_id"),
        nullable=False,
    )
    bucket_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    bucket_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    service_category: Mapped[str] = mapped_column(String(255), nullable=False)
    geography_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    point_forecast: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    quantile_p10: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    quantile_p50: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    quantile_p90: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    baseline_value: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)


class CurrentForecastMarker(Base):
    __tablename__ = "current_forecast_markers"

    forecast_product_name: Mapped[str] = mapped_column(String(64), primary_key=True)
    forecast_version_id: Mapped[str] = mapped_column(
        ForeignKey("forecast_versions.forecast_version_id"),
        nullable=False,
    )
    source_cleaned_dataset_version_id: Mapped[str] = mapped_column(
        ForeignKey("dataset_versions.dataset_version_id"),
        nullable=False,
    )
    horizon_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    horizon_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_by_run_id: Mapped[str] = mapped_column(ForeignKey("forecast_runs.forecast_run_id"), nullable=False)
    geography_scope: Mapped[str] = mapped_column(String(32), nullable=False)


class ForecastModelRun(Base):
    __tablename__ = "forecast_model_runs"

    forecast_model_run_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    forecast_product_name: Mapped[str] = mapped_column(String(64), nullable=False)
    trigger_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source_cleaned_dataset_version_id: Mapped[str | None] = mapped_column(
        ForeignKey("dataset_versions.dataset_version_id"),
        nullable=True,
    )
    training_window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    training_window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="running")
    result_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    forecast_model_artifact_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    geography_scope: Mapped[str | None] = mapped_column(String(32), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)


class ForecastModelArtifact(Base):
    __tablename__ = "forecast_model_artifacts"

    forecast_model_artifact_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    forecast_product_name: Mapped[str] = mapped_column(String(64), nullable=False)
    forecast_model_run_id: Mapped[str] = mapped_column(
        ForeignKey("forecast_model_runs.forecast_model_run_id"),
        nullable=False,
    )
    source_cleaned_dataset_version_id: Mapped[str] = mapped_column(
        ForeignKey("dataset_versions.dataset_version_id"),
        nullable=False,
    )
    geography_scope: Mapped[str] = mapped_column(String(32), nullable=False)
    model_family: Mapped[str] = mapped_column(String(32), nullable=False)
    baseline_method: Mapped[str] = mapped_column(String(64), nullable=False)
    feature_schema_version: Mapped[str] = mapped_column(String(32), nullable=False)
    artifact_path: Mapped[str] = mapped_column(Text, nullable=False)
    storage_status: Mapped[str] = mapped_column(String(16), nullable=False, default="stored")
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    trained_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)


class CurrentForecastModelMarker(Base):
    __tablename__ = "current_forecast_model_markers"

    forecast_product_name: Mapped[str] = mapped_column(String(64), primary_key=True)
    forecast_model_artifact_id: Mapped[str] = mapped_column(
        ForeignKey("forecast_model_artifacts.forecast_model_artifact_id"),
        nullable=False,
    )
    source_cleaned_dataset_version_id: Mapped[str] = mapped_column(
        ForeignKey("dataset_versions.dataset_version_id"),
        nullable=False,
    )
    training_window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    training_window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_by_run_id: Mapped[str] = mapped_column(
        ForeignKey("forecast_model_runs.forecast_model_run_id"),
        nullable=False,
    )
    geography_scope: Mapped[str] = mapped_column(String(32), nullable=False)
