from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies.authz import require_operational_status_reader
from app.core.db import get_db_session
from app.repositories.approval_status_repository import ApprovalStatusRepository
from app.repositories.review_needed_repository import ReviewNeededRepository
from app.schemas.validation_status import ReviewNeededStatusList
from app.services.validation_status_service import ValidationStatusService

router = APIRouter(prefix="/api/v1", tags=["validation"])


@router.get("/datasets/review-needed", response_model=ReviewNeededStatusList)
def list_review_needed_datasets(
    validation_run_id: UUID | None = Query(default=None, alias="validationRunId"),
    session: Session = Depends(get_db_session),
    _claims: dict = Depends(require_operational_status_reader),
) -> ReviewNeededStatusList:
    service = ValidationStatusService(ApprovalStatusRepository(session), ReviewNeededRepository(session))
    return service.list_review_needed(str(validation_run_id) if validation_run_id is not None else None)
