from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_authenticated_user
from app.core.db import get_db_session
from app.repositories.user_guide_repository import UserGuideRepository
from app.schemas.user_guide import GuideRenderOutcomeRequest, UserGuideView
from app.services.user_guide_service import UserGuideService


router = APIRouter(prefix="/api/v1/help/user-guide", tags=["user-guide"])


def build_user_guide_service(session: Session) -> UserGuideService:
    return UserGuideService(
        repository=UserGuideRepository(session),
        logger=logging.getLogger("user_guide.api"),
    )


@router.get("", response_model=UserGuideView)
def get_user_guide(
    entry_point: str = Query(alias="entryPoint", min_length=1),
    x_client_correlation_id: str | None = Header(default=None, alias="X-Client-Correlation-Id"),
    claims: dict = Depends(require_authenticated_user),
    session: Session = Depends(get_db_session),
) -> UserGuideView:
    return build_user_guide_service(session).get_current_user_guide(
        user_id=str(claims.get("sub") or claims.get("email") or "anonymous"),
        entry_point=entry_point,
        correlation_id=x_client_correlation_id,
    )


@router.post("/{guide_access_event_id}/render-events", status_code=status.HTTP_202_ACCEPTED)
def post_user_guide_render_event(
    guide_access_event_id: str,
    payload: GuideRenderOutcomeRequest,
    _claims: dict = Depends(require_authenticated_user),
    session: Session = Depends(get_db_session),
) -> Response:
    service = build_user_guide_service(session)
    try:
        service.record_render_outcome(guide_access_event_id, payload)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Guide access event not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_202_ACCEPTED)
