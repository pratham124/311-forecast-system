from __future__ import annotations

import pytest

from app.repositories.auth_repository import AuthRepository
from app.services.auth_service import AuthService, AuthenticationError, RegistrationError


@pytest.mark.unit
def test_register_and_login_issue_access_and_refresh_tokens(session) -> None:
    repository = AuthRepository(session)
    repository.upsert_allowlist_entry('planner@example.com', ['CityPlanner'])
    session.commit()

    service = AuthService(repository)
    registered = service.register('planner@example.com', 'super-secret-password')

    assert registered.email == 'planner@example.com'
    assert registered.roles == ['CityPlanner']
    assert registered.access_token
    assert registered.refresh_token

    authenticated = service.login('planner@example.com', 'super-secret-password')
    assert authenticated.user_account_id == registered.user_account_id
    assert authenticated.roles == ['CityPlanner']
    assert authenticated.refresh_token


@pytest.mark.unit
def test_refresh_rotates_refresh_token(session) -> None:
    repository = AuthRepository(session)
    repository.upsert_allowlist_entry('planner@example.com', ['CityPlanner'])
    session.commit()
    service = AuthService(repository)

    registered = service.register('planner@example.com', 'super-secret-password')
    refreshed = service.refresh(registered.refresh_token)

    assert refreshed.user_account_id == registered.user_account_id
    assert refreshed.refresh_token != registered.refresh_token

    with pytest.raises(AuthenticationError):
        service.refresh(registered.refresh_token)


@pytest.mark.unit
def test_logout_revokes_refresh_token(session) -> None:
    repository = AuthRepository(session)
    repository.upsert_allowlist_entry('manager@example.com', ['OperationalManager'])
    session.commit()
    service = AuthService(repository)

    registered = service.register('manager@example.com', 'super-secret-password')
    service.logout(registered.refresh_token)

    with pytest.raises(AuthenticationError):
        service.refresh(registered.refresh_token)


@pytest.mark.unit
def test_register_rejects_email_not_in_allowlist(session) -> None:
    service = AuthService(AuthRepository(session))

    with pytest.raises(RegistrationError):
        service.register('outsider@example.com', 'super-secret-password')


@pytest.mark.unit
def test_login_rejects_invalid_password(session) -> None:
    repository = AuthRepository(session)
    repository.upsert_allowlist_entry('manager@example.com', ['OperationalManager'])
    session.commit()
    service = AuthService(repository)
    service.register('manager@example.com', 'super-secret-password')

    with pytest.raises(AuthenticationError):
        service.login('manager@example.com', 'wrong-password')
