from __future__ import annotations

import pytest


@pytest.mark.contract
def test_register_login_refresh_logout_and_me_flow(app_client) -> None:
    register_response = app_client.post(
        '/api/v1/auth/register',
        json={'email': 'planner@example.com', 'password': 'super-secret-password'},
    )
    assert register_response.status_code == 201
    register_body = register_response.json()
    assert register_body['user']['roles'] == ['CityPlanner']
    assert register_body['accessToken']
    assert 'refreshToken' not in register_body
    assert 'forecast_refresh_token=' in register_response.headers['set-cookie']

    login_response = app_client.post(
        '/api/v1/auth/login',
        json={'email': 'planner@example.com', 'password': 'super-secret-password'},
    )
    assert login_response.status_code == 200
    login_body = login_response.json()
    assert login_body['user']['email'] == 'planner@example.com'
    assert 'refreshToken' not in login_body
    first_cookie = app_client.cookies.get('forecast_refresh_token')
    assert first_cookie

    refresh_response = app_client.post('/api/v1/auth/refresh')
    assert refresh_response.status_code == 200
    refresh_body = refresh_response.json()
    assert refresh_body['accessToken']
    second_cookie = app_client.cookies.get('forecast_refresh_token')
    assert second_cookie
    assert second_cookie != first_cookie

    app_client.cookies.set('forecast_refresh_token', first_cookie)
    stale_refresh_response = app_client.post('/api/v1/auth/refresh')
    assert stale_refresh_response.status_code == 401
    app_client.cookies.set('forecast_refresh_token', second_cookie)

    me_response = app_client.get(
        '/api/v1/auth/me',
        headers={'Authorization': f"Bearer {refresh_body['accessToken']}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()['roles'] == ['CityPlanner']

    logout_response = app_client.post('/api/v1/auth/logout')
    assert logout_response.status_code == 202
    cleared_cookie = logout_response.headers['set-cookie']
    assert 'forecast_refresh_token=""' in cleared_cookie or 'forecast_refresh_token=null' in cleared_cookie or 'forecast_refresh_token=' in cleared_cookie

    revoked_refresh_response = app_client.post('/api/v1/auth/refresh')
    assert revoked_refresh_response.status_code == 401


@pytest.mark.contract
def test_refresh_rejects_when_cookie_missing(app_client) -> None:
    response = app_client.post('/api/v1/auth/refresh')
    assert response.status_code == 401


@pytest.mark.contract
def test_register_rejects_email_not_in_allowlist(app_client) -> None:
    response = app_client.post(
        '/api/v1/auth/register',
        json={'email': 'outsider@example.com', 'password': 'super-secret-password'},
    )
    assert response.status_code == 403


@pytest.mark.contract
def test_login_rejects_bad_credentials(app_client) -> None:
    response = app_client.post(
        '/api/v1/auth/login',
        json={'email': 'planner@example.com', 'password': 'super-secret-password'},
    )
    assert response.status_code == 401
