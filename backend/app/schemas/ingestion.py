from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class IngestionRunAccepted(BaseModel):
    run_id: str
    status: str


class IngestionRunStatus(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    run_id: str
    status: str
    result_type: str | None = None
    started_at: datetime
    completed_at: datetime | None = None
    cursor_used: str | None = None
    cursor_advanced: bool
    candidate_dataset_id: str | None = None
    dataset_version_id: str | None = None
    records_received: int | None = None
    failure_reason: str | None = None


class CurrentDataset(BaseModel):
    source_name: str
    dataset_version_id: str
    updated_at: datetime
    updated_by_run_id: str
    record_count: int
    latest_requested_at: datetime | None = None
