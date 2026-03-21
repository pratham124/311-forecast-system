from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies.authz import require_operational_status_reader
from app.core.db import get_db_session
from app.repositories.approval_status_repository import ApprovalStatusRepository
from app.repositories.review_needed_repository import ReviewNeededRepository
from app.schemas.validation_status import ValidationRunStatus
from app.services.validation_status_service import ValidationStatusService

router = APIRouter(prefix="/api/v1", tags=["validation"])


@router.get("/validation-runs/{validation_run_id}", response_model=ValidationRunStatus)
def get_validation_run_status(
    validation_run_id: UUID,
    session: Session = Depends(get_db_session),
    _claims: dict = Depends(require_operational_status_reader),
) -> ValidationRunStatus:
    service = ValidationStatusService(ApprovalStatusRepository(session), ReviewNeededRepository(session))
    return service.get_validation_run_status(str(validation_run_id))
