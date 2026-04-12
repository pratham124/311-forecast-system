from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class VisualizationLoadRecord(Base):
    __tablename__ = "visualization_load_records"

    visualization_load_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    requested_by_actor: Mapped[str] = mapped_column(String(64), nullable=False)
    forecast_product_name: Mapped[str] = mapped_column(String(32), nullable=False)
    forecast_granularity: Mapped[str] = mapped_column(String(16), nullable=False)
    service_category_filter: Mapped[str | None] = mapped_column(String(255), nullable=True)
    history_window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    history_window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    forecast_window_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    forecast_window_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
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
    fallback_snapshot_id: Mapped[str | None] = mapped_column(
        ForeignKey("visualization_snapshots.visualization_snapshot_id"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="running")
    degradation_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    render_reported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_assessment_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    confidence_indicator_state: Mapped[str | None] = mapped_column(String(32), nullable=True)
    confidence_reason_categories_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_supporting_signals_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_signal_resolution_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    confidence_render_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    confidence_render_reported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    confidence_render_failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class VisualizationSnapshot(Base):
    __tablename__ = "visualization_snapshots"

    visualization_snapshot_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    forecast_product_name: Mapped[str] = mapped_column(String(32), nullable=False)
    forecast_granularity: Mapped[str] = mapped_column(String(16), nullable=False)
    service_category_filter: Mapped[str | None] = mapped_column(String(255), nullable=True)
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
    source_forecast_run_id: Mapped[str | None] = mapped_column(
        ForeignKey("forecast_runs.forecast_run_id"),
        nullable=True,
    )
    source_weekly_forecast_run_id: Mapped[str | None] = mapped_column(
        ForeignKey("weekly_forecast_runs.weekly_forecast_run_id"),
        nullable=True,
    )
    history_window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    history_window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    forecast_window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    forecast_window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    band_standard: Mapped[str] = mapped_column(String(32), nullable=False, default="p10_p50_p90")
    snapshot_status: Mapped[str] = mapped_column(String(16), nullable=False, default="stored")
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_from_load_id: Mapped[str] = mapped_column(
        ForeignKey("visualization_load_records.visualization_load_id"),
        nullable=False,
    )
