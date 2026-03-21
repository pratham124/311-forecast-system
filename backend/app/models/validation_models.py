from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class ValidationRun(Base):
    __tablename__ = "validation_runs"

    validation_run_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    ingestion_run_id: Mapped[str] = mapped_column(ForeignKey("ingestion_runs.run_id"), nullable=False)
    source_dataset_version_id: Mapped[str] = mapped_column(ForeignKey("dataset_versions.dataset_version_id"), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="running")
    failure_stage: Mapped[str | None] = mapped_column(String(32), nullable=True)
    duplicate_threshold_type: Mapped[str] = mapped_column(String(32), nullable=False, default="percentage")
    duplicate_percentage: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    approved_dataset_version_id: Mapped[str | None] = mapped_column(
        ForeignKey("dataset_versions.dataset_version_id"),
        nullable=True,
    )
    review_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)


class ValidationResultRecord(Base):
    __tablename__ = "validation_results"

    validation_result_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    validation_run_id: Mapped[str] = mapped_column(
        ForeignKey("validation_runs.validation_run_id"),
        nullable=False,
        unique=True,
    )
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    required_field_check: Mapped[str] = mapped_column(String(16), nullable=False)
    type_check: Mapped[str] = mapped_column(String(16), nullable=False)
    format_check: Mapped[str] = mapped_column(String(16), nullable=False)
    completeness_check: Mapped[str] = mapped_column(String(16), nullable=False)
    issue_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class DuplicateAnalysisResult(Base):
    __tablename__ = "duplicate_analysis_results"

    duplicate_analysis_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    validation_run_id: Mapped[str] = mapped_column(
        ForeignKey("validation_runs.validation_run_id"),
        nullable=False,
        unique=True,
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    total_record_count: Mapped[int] = mapped_column(Integer, nullable=False)
    duplicate_record_count: Mapped[int] = mapped_column(Integer, nullable=False)
    duplicate_percentage: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    threshold_percentage: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    duplicate_group_count: Mapped[int] = mapped_column(Integer, nullable=False)
    issue_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class DuplicateGroup(Base):
    __tablename__ = "duplicate_groups"

    duplicate_group_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    duplicate_analysis_id: Mapped[str] = mapped_column(
        ForeignKey("duplicate_analysis_results.duplicate_analysis_id"),
        nullable=False,
    )
    group_key: Mapped[str] = mapped_column(String(255), nullable=False)
    source_record_count: Mapped[int] = mapped_column(Integer, nullable=False)
    resolution_status: Mapped[str] = mapped_column(String(32), nullable=False)
    cleaned_record_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    resolution_summary: Mapped[str | None] = mapped_column(Text, nullable=True)


class ReviewNeededRecord(Base):
    __tablename__ = "review_needed_records"

    review_record_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    validation_run_id: Mapped[str] = mapped_column(
        ForeignKey("validation_runs.validation_run_id"),
        nullable=False,
        unique=True,
    )
    duplicate_analysis_id: Mapped[str] = mapped_column(
        ForeignKey("duplicate_analysis_results.duplicate_analysis_id"),
        nullable=False,
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
