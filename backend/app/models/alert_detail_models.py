from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class AlertDetailLoadRecord(Base):
    __tablename__ = "alert_detail_load_records"

    alert_detail_load_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    alert_source: Mapped[str] = mapped_column(String(32), nullable=False)
    alert_id: Mapped[str] = mapped_column(String(36), nullable=False)
    requested_by_subject: Mapped[str] = mapped_column(String(255), nullable=False)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_forecast_version_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    source_weekly_forecast_version_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    source_threshold_evaluation_run_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    source_surge_evaluation_run_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    source_surge_candidate_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    view_status: Mapped[str] = mapped_column(String(24), nullable=False, default="loading")
    distribution_status: Mapped[str] = mapped_column(String(24), nullable=False, default="loading")
    drivers_status: Mapped[str] = mapped_column(String(24), nullable=False, default="loading")
    anomalies_status: Mapped[str] = mapped_column(String(24), nullable=False, default="loading")
    preparation_status: Mapped[str] = mapped_column(String(24), nullable=False, default="loading")
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    render_status: Mapped[str | None] = mapped_column(String(24), nullable=True)
    render_failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    render_reported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
