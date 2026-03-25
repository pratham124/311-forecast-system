from __future__ import annotations

import json
from datetime import timedelta

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_claims
from app.core.config import get_settings
from app.core.db import get_db_session
from app.repositories.auth_repository import AuthRepository
from app.schemas.auth import AuthResponse, CurrentUserRead, LoginRequest, RegisterRequest
from app.services.auth_service import AuthService, AuthenticationError, RegistrationError

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def _build_auth_response(user) -> AuthResponse:
    return AuthResponse(
        accessToken=user.access_token,
        user=CurrentUserRead(
            userAccountId=user.user_account_id,
            email=user.email,
            roles=user.roles,
        ),
    )


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=settings.auth_refresh_cookie_name,
        value=refresh_token,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
        max_age=int(timedelta(days=settings.jwt_refresh_token_expires_days).total_seconds()),
        path="/api/v1/auth",
    )


def _clear_refresh_cookie(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(
        key=settings.auth_refresh_cookie_name,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
        path="/api/v1/auth",
    )


@router.post('/register', response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, response: Response, session: Session = Depends(get_db_session)) -> AuthResponse:
    service = AuthService(AuthRepository(session))
    try:
        authenticated = service.register(payload.email, payload.password)
    except RegistrationError as exc:
        message = str(exc)
        status_code = status.HTTP_409_CONFLICT if 'already exists' in message else status.HTTP_403_FORBIDDEN
        raise HTTPException(status_code=status_code, detail=message) from exc
    _set_refresh_cookie(response, authenticated.refresh_token)
    return _build_auth_response(authenticated)


@router.post('/login', response_model=AuthResponse)
def login(payload: LoginRequest, response: Response, session: Session = Depends(get_db_session)) -> AuthResponse:
    service = AuthService(AuthRepository(session))
    try:
        authenticated = service.login(payload.email, payload.password)
    except AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    _set_refresh_cookie(response, authenticated.refresh_token)
    return _build_auth_response(authenticated)


@router.post('/refresh', response_model=AuthResponse)
def refresh(
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias=get_settings().auth_refresh_cookie_name),
    session: Session = Depends(get_db_session),
) -> AuthResponse:
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Missing refresh token')
    service = AuthService(AuthRepository(session))
    try:
        authenticated = service.refresh(refresh_token)
    except AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    _set_refresh_cookie(response, authenticated.refresh_token)
    return _build_auth_response(authenticated)


@router.post('/logout', status_code=status.HTTP_202_ACCEPTED)
def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias=get_settings().auth_refresh_cookie_name),
    session: Session = Depends(get_db_session),
) -> Response:
    if refresh_token:
        AuthService(AuthRepository(session)).logout(refresh_token)
    _clear_refresh_cookie(response)
    response.status_code = status.HTTP_202_ACCEPTED
    return response


@router.get('/me', response_model=CurrentUserRead)
def get_me(claims: dict = Depends(get_current_claims), session: Session = Depends(get_db_session)) -> CurrentUserRead:
    subject = claims.get('sub')
    if not isinstance(subject, str) or not subject:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token')
    service = AuthService(AuthRepository(session))
    try:
        user = service.get_user(subject)
    except AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    roles = json.loads(user.roles_json)
    return CurrentUserRead(userAccountId=user.user_account_id, email=user.email, roles=[str(role) for role in roles])
