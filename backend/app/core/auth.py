from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError

from app.core.config import get_settings

security = HTTPBearer(auto_error=False)
JWT_ALGORITHMS = ["HS256"]


def _decode_jwt_payload(token: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=JWT_ALGORITHMS,
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
        )
    except InvalidTokenError as exc:  # pragma: no cover - normalized error branch
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc
    if not isinstance(payload, dict):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return payload


def create_access_token(subject: str, email: str, roles: list[str]) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "email": email,
        "roles": roles,
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.jwt_access_token_expires_minutes)).timestamp()),
        "token_type": "access",
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=JWT_ALGORITHMS[0])


def get_current_claims(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict[str, Any]:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    claims = _decode_jwt_payload(credentials.credentials)
    if claims.get("token_type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return claims


def get_optional_claims(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict[str, Any] | None:
    if credentials is None:
        return None
    claims = _decode_jwt_payload(credentials.credentials)
    if claims.get("token_type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return claims


def require_roles(*allowed_roles: str):
    def dependency(claims: dict[str, Any] = Depends(get_current_claims)) -> dict[str, Any]:
        roles = claims.get("roles", [])
        if not isinstance(roles, list):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid roles claim")
        if not any(role in allowed_roles for role in roles):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return claims

    return dependency


require_operational_manager = require_roles("OperationalManager")
require_planner_or_manager = require_roles("OperationalManager", "CityPlanner")
