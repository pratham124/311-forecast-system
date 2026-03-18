from __future__ import annotations

import base64
import json
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer(auto_error=False)


def _decode_jwt_payload(token: str) -> dict[str, Any]:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Token must use JWT structure")
        payload = parts[1]
        payload += "=" * (-len(payload) % 4)
        decoded = base64.urlsafe_b64decode(payload.encode("utf-8"))
        return json.loads(decoded.decode("utf-8"))
    except Exception as exc:  # pragma: no cover - normalized error branch
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc


def get_current_claims(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict[str, Any]:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    return _decode_jwt_payload(credentials.credentials)


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
