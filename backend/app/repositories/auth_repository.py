from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.auth_models import RefreshSession, SignupAllowlistEntry, UserAccount


class AuthRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_user_by_email(self, email: str) -> UserAccount | None:
        return self.session.query(UserAccount).filter(UserAccount.email == email).one_or_none()

    def get_user_by_id(self, user_account_id: str) -> UserAccount | None:
        return self.session.query(UserAccount).filter(UserAccount.user_account_id == user_account_id).one_or_none()

    def create_user(self, email: str, password_hash: str, roles: list[str]) -> UserAccount:
        user = UserAccount(email=email, password_hash=password_hash, roles_json=json.dumps(roles))
        self.session.add(user)
        self.session.flush()
        return user

    def get_allowlist_entry(self, email: str) -> SignupAllowlistEntry | None:
        return self.session.query(SignupAllowlistEntry).filter(SignupAllowlistEntry.email == email).one_or_none()

    def upsert_allowlist_entry(self, email: str, roles: list[str], enabled: bool = True) -> SignupAllowlistEntry:
        entry = self.get_allowlist_entry(email)
        roles_json = json.dumps(roles)
        if entry is None:
            entry = SignupAllowlistEntry(email=email, roles_json=roles_json, is_enabled=enabled)
            self.session.add(entry)
            self.session.flush()
            return entry
        entry.roles_json = roles_json
        entry.is_enabled = enabled
        self.session.flush()
        return entry

    def mark_allowlist_entry_registered(self, entry: SignupAllowlistEntry, user_account_id: str) -> SignupAllowlistEntry:
        entry.registered_user_account_id = user_account_id
        entry.registered_at = datetime.utcnow()
        self.session.flush()
        return entry

    def create_refresh_session(self, user_account_id: str, token_hash: str, expires_at: datetime) -> RefreshSession:
        session = RefreshSession(user_account_id=user_account_id, token_hash=token_hash, expires_at=expires_at)
        self.session.add(session)
        self.session.flush()
        return session

    def get_refresh_session_by_hash(self, token_hash: str) -> RefreshSession | None:
        return self.session.query(RefreshSession).filter(RefreshSession.token_hash == token_hash).one_or_none()

    def revoke_refresh_session(self, refresh_session: RefreshSession, revoked_at: datetime | None = None) -> RefreshSession:
        refresh_session.revoked_at = revoked_at or datetime.utcnow()
        self.session.flush()
        return refresh_session

    def rotate_refresh_session(self, refresh_session: RefreshSession, rotated_at: datetime | None = None) -> RefreshSession:
        refresh_session.rotated_at = rotated_at or datetime.utcnow()
        self.session.flush()
        return refresh_session
