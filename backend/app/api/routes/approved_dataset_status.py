from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies.authz import require_operational_status_reader
from app.core.config import get_settings
from app.core.db import get_db_session
from app.repositories.approval_status_repository import ApprovalStatusRepository
from app.schemas.validation_status import ApprovedDatasetStatus
from app.services.approval_status_service import ApprovalStatusService

router = APIRouter(prefix="/api/v1", tags=["validation"])


@router.get("/datasets/approved/current", response_model=ApprovedDatasetStatus)
def get_approved_dataset_status(
    session: Session = Depends(get_db_session),
    _claims: dict = Depends(require_operational_status_reader),
) -> ApprovedDatasetStatus:
    service = ApprovalStatusService(ApprovalStatusRepository(session))
    return service.get_current_approved_dataset(get_settings().source_name)
