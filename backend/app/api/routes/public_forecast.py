from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db_session
from app.repositories.forecast_repository import ForecastRepository
from app.repositories.public_forecast_repository import PublicForecastRepository
from app.repositories.weekly_forecast_repository import WeeklyForecastRepository
from app.schemas.public_forecast import PublicForecastDisplayEventRequest, PublicForecastView
from app.services.public_forecast_sanitization_service import PublicForecastSanitizationService
from app.services.public_forecast_service import PublicForecastService
from app.services.public_forecast_source_service import PublicForecastSourceService


router = APIRouter(prefix="/api/v1/public/forecast-categories", tags=["public-forecast"])


def build_public_forecast_service(session: Session) -> PublicForecastService:
    settings = get_settings()
    return PublicForecastService(
        repository=PublicForecastRepository(session),
        source_service=PublicForecastSourceService(
            forecast_repository=ForecastRepository(session),
            weekly_forecast_repository=WeeklyForecastRepository(session),
            settings=settings,
        ),
        sanitization_service=PublicForecastSanitizationService(),
        logger=logging.getLogger("public_forecast.api"),
    )


@router.get("/current", response_model=PublicForecastView)
def get_current_public_forecast(
    forecast_product: str = Query(default="daily", alias="forecastProduct"),
    x_client_correlation_id: str | None = Header(default=None, alias="X-Client-Correlation-Id"),
    session: Session = Depends(get_db_session),
) -> PublicForecastView:
    if forecast_product not in {"daily", "weekly"}:
        raise HTTPException(status_code=422, detail="forecastProduct must be one of daily or weekly")
    return build_public_forecast_service(session).get_current_public_forecast(
        client_correlation_id=x_client_correlation_id,
        forecast_product=forecast_product,
    )


@router.post("/{public_forecast_request_id}/display-events", status_code=status.HTTP_202_ACCEPTED)
def record_public_forecast_display_event(
    public_forecast_request_id: str,
    payload: PublicForecastDisplayEventRequest,
    session: Session = Depends(get_db_session),
) -> Response:
    service = build_public_forecast_service(session)
    try:
        service.record_display_event(public_forecast_request_id, payload)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Public forecast request not found") from exc
    return Response(status_code=status.HTTP_202_ACCEPTED)
