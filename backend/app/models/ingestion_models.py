from __future__ import annotations

import json
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    run_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    trigger_type: Mapped[str] = mapped_column(String(32))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(16))
    result_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    source_window_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cursor_used: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cursor_advanced: Mapped[bool] = mapped_column(Boolean, default=False)
    records_received: Mapped[int | None] = mapped_column(Integer, nullable=True)
    candidate_dataset_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    dataset_version_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class SuccessfulPullCursor(Base):
    __tablename__ = "successful_pull_cursors"

    source_name: Mapped[str] = mapped_column(String(64), primary_key=True)
    cursor_value: Mapped[str] = mapped_column(String(255))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_by_run_id: Mapped[str] = mapped_column(String(36))


class CandidateDataset(Base):
    __tablename__ = "candidate_datasets"

    candidate_dataset_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    ingestion_run_id: Mapped[str] = mapped_column(ForeignKey("ingestion_runs.run_id"))
    record_count: Mapped[int] = mapped_column(Integer)
    validation_status: Mapped[str] = mapped_column(String(16))
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)


class DatasetVersion(Base):
    __tablename__ = "dataset_versions"

    dataset_version_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    source_name: Mapped[str] = mapped_column(String(64))
    ingestion_run_id: Mapped[str] = mapped_column(ForeignKey("ingestion_runs.run_id"))
    candidate_dataset_id: Mapped[str | None] = mapped_column(
        ForeignKey("candidate_datasets.candidate_dataset_id"),
        nullable=True,
    )
    source_dataset_version_id: Mapped[str | None] = mapped_column(
        ForeignKey("dataset_versions.dataset_version_id"),
        nullable=True,
    )
    record_count: Mapped[int] = mapped_column(Integer)
    validation_status: Mapped[str] = mapped_column(String(16))
    storage_status: Mapped[str] = mapped_column(String(16))
    dataset_kind: Mapped[str] = mapped_column(String(16), default="source")
    duplicate_group_count: Mapped[int] = mapped_column(Integer, default=0)
    approved_by_validation_run_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    stored_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class DatasetRecord(Base):
    __tablename__ = "dataset_records"

    record_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    dataset_version_id: Mapped[str] = mapped_column(ForeignKey("dataset_versions.dataset_version_id"))
    source_record_id: Mapped[str] = mapped_column(String(255))
    requested_at: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(255))
    record_payload: Mapped[str] = mapped_column(Text)

    @classmethod
    def from_normalized_row(cls, dataset_version_id: str, record: dict[str, object]) -> "DatasetRecord":
        return cls(
            dataset_version_id=dataset_version_id,
            source_record_id=str(record.get("service_request_id", "")),
            requested_at=str(record.get("requested_at", "")),
            category=str(record.get("category", "")),
            record_payload=json.dumps(record, sort_keys=True),
        )


class CurrentDatasetMarker(Base):
    __tablename__ = "current_dataset_markers"

    source_name: Mapped[str] = mapped_column(String(64), primary_key=True)
    dataset_version_id: Mapped[str] = mapped_column(ForeignKey("dataset_versions.dataset_version_id"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_by_run_id: Mapped[str] = mapped_column(String(36))
    record_count: Mapped[int] = mapped_column(Integer)


class FailureNotificationRecord(Base):
    __tablename__ = "failure_notification_records"

    notification_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    run_id: Mapped[str] = mapped_column(ForeignKey("ingestion_runs.run_id"))
    failure_category: Mapped[str] = mapped_column(String(32))
    run_status: Mapped[str] = mapped_column(String(16))
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    message: Mapped[str] = mapped_column(Text)
