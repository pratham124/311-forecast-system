from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class HistoricalDemandAnalysisRequest(Base):
    __tablename__ = "historical_demand_analysis_requests"

    analysis_request_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    requested_by_actor: Mapped[str] = mapped_column(String(32), nullable=False)
    source_cleaned_dataset_version_id: Mapped[str | None] = mapped_column(
        ForeignKey("dataset_versions.dataset_version_id"),
        nullable=True,
    )
    service_category_filter: Mapped[str | None] = mapped_column(String(255), nullable=True)
    time_range_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    time_range_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    geography_filter_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    geography_filter_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    warning_status: Mapped[str] = mapped_column(String(16), nullable=False, default="not_needed")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="running")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class HistoricalDemandAnalysisResult(Base):
    __tablename__ = "historical_demand_analysis_results"

    analysis_result_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    analysis_request_id: Mapped[str] = mapped_column(
        ForeignKey("historical_demand_analysis_requests.analysis_request_id"),
        nullable=False,
        unique=True,
    )
    source_cleaned_dataset_version_id: Mapped[str] = mapped_column(
        ForeignKey("dataset_versions.dataset_version_id"),
        nullable=False,
    )
    aggregation_granularity: Mapped[str] = mapped_column(String(16), nullable=False)
    result_mode: Mapped[str] = mapped_column(String(16), nullable=False)
    service_category_filter: Mapped[str | None] = mapped_column(String(255), nullable=True)
    time_range_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    time_range_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    geography_filter_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    geography_filter_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    record_count: Mapped[int] = mapped_column(Integer, nullable=False)
    stored_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class HistoricalDemandSummaryPoint(Base):
    __tablename__ = "historical_demand_summary_points"

    summary_point_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    analysis_result_id: Mapped[str] = mapped_column(
        ForeignKey("historical_demand_analysis_results.analysis_result_id"),
        nullable=False,
    )
    bucket_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    bucket_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    service_category: Mapped[str] = mapped_column(String(255), nullable=False)
    geography_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    demand_count: Mapped[int] = mapped_column(Integer, nullable=False)


class HistoricalAnalysisOutcomeRecord(Base):
    __tablename__ = "historical_analysis_outcome_records"

    analysis_outcome_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    analysis_request_id: Mapped[str] = mapped_column(
        ForeignKey("historical_demand_analysis_requests.analysis_request_id"),
        nullable=False,
        unique=True,
    )
    outcome_type: Mapped[str] = mapped_column(String(32), nullable=False)
    warning_acknowledged: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    message: Mapped[str] = mapped_column(Text, nullable=False)
