from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ValidationRunStatus(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    validation_run_id: str = Field(alias="validationRunId")
    ingestion_run_id: str = Field(alias="ingestionRunId")
    source_dataset_version_id: str = Field(alias="sourceDatasetVersionId")
    approved_dataset_version_id: str | None = Field(default=None, alias="approvedDatasetVersionId")
    status: str
    failure_stage: str | None = Field(default=None, alias="failureStage")
    visibility_state: str = Field(alias="visibilityState")
    duplicate_percentage: float | None = Field(default=None, alias="duplicatePercentage")
    started_at: datetime = Field(alias="startedAt")
    completed_at: datetime | None = Field(default=None, alias="completedAt")
    review_reason: str | None = Field(default=None, alias="reviewReason")
    summary: str | None = None


class ApprovedDatasetStatus(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    dataset_version_id: str = Field(alias="datasetVersionId")
    source_dataset_version_id: str | None = Field(default=None, alias="sourceDatasetVersionId")
    approved_at: datetime = Field(alias="approvedAt")
    approved_by_validation_run_id: str | None = Field(default=None, alias="approvedByValidationRunId")
    cleaned_record_count: int = Field(alias="cleanedRecordCount")
    duplicate_group_count: int = Field(default=0, alias="duplicateGroupCount")
    summary: str


class ReviewNeededStatus(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    review_record_id: str = Field(alias="reviewRecordId")
    validation_run_id: str = Field(alias="validationRunId")
    duplicate_percentage: float = Field(alias="duplicatePercentage")
    threshold_percentage: float = Field(alias="thresholdPercentage")
    recorded_at: datetime = Field(alias="recordedAt")
    reason: str
    summary: str


class ReviewNeededStatusList(BaseModel):
    items: list[ReviewNeededStatus]
