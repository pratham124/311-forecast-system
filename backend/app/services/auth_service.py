from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.core.auth import create_access_token
from app.core.config import get_settings
from app.repositories.auth_repository import AuthRepository


class AuthenticationError(ValueError):
    pass


class RegistrationError(ValueError):
    pass


@dataclass(frozen=True)
class AuthenticatedUser:
    user_account_id: str
    email: str
    roles: list[str]
    access_token: str
    refresh_token: str


class AuthService:
    def __init__(self, repository: AuthRepository) -> None:
        self.repository = repository

    def register(self, email: str, password: str) -> AuthenticatedUser:
        normalized_email = _normalize_email(email)
        _validate_password(password)

        if self.repository.get_user_by_email(normalized_email):
            raise RegistrationError('An account with that email already exists')

        allowlist_entry = self.repository.get_allowlist_entry(normalized_email)
        if allowlist_entry is None or not allowlist_entry.is_enabled:
            raise RegistrationError('That email is not permitted to register')

        roles = _load_roles(allowlist_entry.roles_json)
        user = self.repository.create_user(
            email=normalized_email,
            password_hash=_hash_password(password),
            roles=roles,
        )
        self.repository.mark_allowlist_entry_registered(allowlist_entry, user.user_account_id)
        authenticated = self._issue_tokens(user.user_account_id, user.email, roles)
        self.repository.session.commit()
        return authenticated

    def login(self, email: str, password: str) -> AuthenticatedUser:
        normalized_email = _normalize_email(email)
        user = self.repository.get_user_by_email(normalized_email)
        if user is None or not user.is_active or not _verify_password(password, user.password_hash):
            raise AuthenticationError('Invalid email or password')
        roles = _load_roles(user.roles_json)
        authenticated = self._issue_tokens(user.user_account_id, user.email, roles)
        self.repository.session.commit()
        return authenticated

    def refresh(self, refresh_token: str) -> AuthenticatedUser:
        refresh_session = self.repository.get_refresh_session_by_hash(_hash_refresh_token(refresh_token))
        if refresh_session is None:
            raise AuthenticationError('Invalid refresh token')
        if refresh_session.revoked_at is not None or refresh_session.rotated_at is not None:
            raise AuthenticationError('Invalid refresh token')
        if refresh_session.expires_at.replace(tzinfo=timezone.utc) <= datetime.now(timezone.utc):
            raise AuthenticationError('Refresh token expired')
        user = self.get_user(refresh_session.user_account_id)
        roles = _load_roles(user.roles_json)
        self.repository.rotate_refresh_session(refresh_session)
        authenticated = self._issue_tokens(user.user_account_id, user.email, roles)
        self.repository.session.commit()
        return authenticated

    def logout(self, refresh_token: str) -> None:
        refresh_session = self.repository.get_refresh_session_by_hash(_hash_refresh_token(refresh_token))
        if refresh_session is None:
            return
        if refresh_session.revoked_at is None:
            self.repository.revoke_refresh_session(refresh_session)
            self.repository.session.commit()

    def get_user(self, user_account_id: str):
        user = self.repository.get_user_by_id(user_account_id)
        if user is None or not user.is_active:
            raise AuthenticationError('User not found')
        return user

    def _issue_tokens(self, user_account_id: str, email: str, roles: list[str]) -> AuthenticatedUser:
        refresh_token = _generate_refresh_token()
        expires_at = datetime.now(timezone.utc) + timedelta(days=get_settings().jwt_refresh_token_expires_days)
        self.repository.create_refresh_session(
            user_account_id=user_account_id,
            token_hash=_hash_refresh_token(refresh_token),
            expires_at=expires_at,
        )
        return AuthenticatedUser(
            user_account_id=user_account_id,
            email=email,
            roles=roles,
            access_token=create_access_token(subject=user_account_id, email=email, roles=roles),
            refresh_token=refresh_token,
        )


class AuthBootstrapService:
    def __init__(self, repository: AuthRepository) -> None:
        self.repository = repository

    def sync_allowlist(self, entries: list[tuple[str, list[str]]]) -> None:
        changed = False
        for email, roles in entries:
            self.repository.upsert_allowlist_entry(email=email, roles=roles, enabled=True)
            changed = True
        if changed:
            self.repository.session.commit()


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _validate_password(password: str) -> None:
    if len(password) < 8:
        raise RegistrationError('Password must be at least 8 characters long')


PBKDF2_ITERATIONS = 600_000


def _hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    derived = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, PBKDF2_ITERATIONS)
    salt_b64 = base64.b64encode(salt).decode('ascii')
    derived_b64 = base64.b64encode(derived).decode('ascii')
    return f'pbkdf2_sha256${PBKDF2_ITERATIONS}${salt_b64}${derived_b64}'


def _verify_password(password: str, stored_value: str) -> bool:
    try:
        algorithm, iterations, salt_b64, expected_b64 = stored_value.split('$', 3)
        if algorithm != 'pbkdf2_sha256':
            return False
        salt = base64.b64decode(salt_b64.encode('ascii'))
        expected = base64.b64decode(expected_b64.encode('ascii'))
        derived = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, int(iterations))
        return hmac.compare_digest(derived, expected)
    except Exception:
        return False


def _load_roles(value: str) -> list[str]:
    decoded = json.loads(value)
    return [str(role) for role in decoded]


def _generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def _hash_refresh_token(refresh_token: str) -> str:
    return hashlib.sha256(refresh_token.encode('utf-8')).hexdigest()
