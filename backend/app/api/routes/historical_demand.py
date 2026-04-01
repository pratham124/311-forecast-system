from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_historical_demand_reader
from app.core.config import get_settings
from app.core.db import get_db_session
from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
from app.repositories.historical_demand_repository import HistoricalDemandRepository
from app.schemas.historical_demand import (
    HistoricalDemandContextRead,
    HistoricalDemandQueryRequest,
    HistoricalDemandRenderEvent,
    HistoricalDemandResponseRead,
)
from app.services.historical_context_service import HistoricalContextService
from app.services.historical_demand_service import HistoricalDemandAnalysisService
from app.services.historical_warning_service import HistoricalWarningService

router = APIRouter(prefix="/api/v1/historical-demand", tags=["historical-demand"])


def build_historical_demand_service(session: Session) -> HistoricalDemandAnalysisService:
    settings = get_settings()
    cleaned_repository = CleanedDatasetRepository(session)
    return HistoricalDemandAnalysisService(
        historical_demand_repository=HistoricalDemandRepository(session),
        cleaned_dataset_repository=cleaned_repository,
        context_service=HistoricalContextService(cleaned_repository, settings.source_name),
        warning_service=HistoricalWarningService(),
        source_name=settings.source_name,
        logger=logging.getLogger("historical_demand.api"),
    )


@router.get("/context", response_model=HistoricalDemandContextRead)
def get_historical_demand_context(
    session: Session = Depends(get_db_session),
    _claims: dict = Depends(require_historical_demand_reader),
) -> HistoricalDemandContextRead:
    return build_historical_demand_service(session).context_service.get_context()


@router.post("/queries", response_model=HistoricalDemandResponseRead)
def create_historical_demand_query(
    payload: HistoricalDemandQueryRequest,
    session: Session = Depends(get_db_session),
    _claims: dict = Depends(require_historical_demand_reader),
) -> HistoricalDemandResponseRead:
    try:
        return build_historical_demand_service(session).execute_query(payload)
    except LookupError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/queries/{analysis_request_id}/render-events", status_code=status.HTTP_202_ACCEPTED)
def record_historical_demand_render_event(
    analysis_request_id: str,
    payload: HistoricalDemandRenderEvent,
    session: Session = Depends(get_db_session),
    _claims: dict = Depends(require_historical_demand_reader),
) -> Response:
    try:
        build_historical_demand_service(session).record_render_event(analysis_request_id, payload)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Historical demand analysis request not found") from exc
    return Response(status_code=status.HTTP_202_ACCEPTED)
