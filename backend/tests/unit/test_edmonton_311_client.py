from __future__ import annotations

from datetime import datetime

import httpx
import pytest

from app.clients.edmonton_311 import (
    Edmonton311AuthError,
    Edmonton311Client,
    Edmonton311Transport,
    Edmonton311UnavailableError,
    SocrataEdmonton311Transport,
)


class DummyResponse:
    def __init__(self, status_code: int, payload) -> None:
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


@pytest.mark.unit
def test_transport_returns_empty_when_sample_rows_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, object]] = []

    def fake_get(url, params, headers, timeout):
        calls.append(params)
        return DummyResponse(200, [])

    monkeypatch.setattr(httpx, "get", fake_get)
    transport = SocrataEdmonton311Transport("https://example.invalid")

    assert transport.fetch(None) == []
    assert calls == [{"$limit": 1}]


@pytest.mark.unit
def test_transport_fetches_multiple_pages_with_cursor(monkeypatch: pytest.MonkeyPatch) -> None:
    responses = [
        DummyResponse(200, [{"submitted_date": "2026-03-01T00:00:00Z", ":id": 1}]),
        DummyResponse(200, [{"submitted_date": "2026-03-02T00:00:00Z", ":id": idx} for idx in range(1000)]),
        DummyResponse(200, [{"submitted_date": "2026-03-03T00:00:00Z", ":id": 1001}]),
    ]
    calls: list[dict[str, object]] = []

    def fake_get(url, params, headers, timeout):
        calls.append(dict(params))
        return responses.pop(0)

    monkeypatch.setattr(httpx, "get", fake_get)
    transport = SocrataEdmonton311Transport("https://example.invalid", api_token="abc")

    rows = transport.fetch("2026-02-28T00:00:00Z")

    assert len(rows) == 1001
    assert calls[1]["$order"] == "submitted_date ASC, :id ASC"
    assert calls[1]["$where"] == "submitted_date > '2026-02-28T00:00:00Z'"
    assert calls[2]["$where"] == "(submitted_date > '2026-02-28T00:00:00Z') AND (submitted_date > '2026-03-02T00:00:00Z' OR (submitted_date = '2026-03-02T00:00:00Z' AND :id > 999))"


@pytest.mark.unit
def test_transport_fetches_without_timestamp_field(monkeypatch: pytest.MonkeyPatch) -> None:
    responses = [
        DummyResponse(200, [{"other": "value"}]),
        DummyResponse(200, [{"other": "value"}]),
    ]

    def fake_get(url, params, headers, timeout):
        return responses.pop(0)

    monkeypatch.setattr(httpx, "get", fake_get)
    transport = SocrataEdmonton311Transport("https://example.invalid")

    assert transport.fetch("ignored") == [{"other": "value"}]


@pytest.mark.unit
def test_transport_uses_offset_pagination_without_timestamp_field(monkeypatch: pytest.MonkeyPatch) -> None:
    responses = [
        DummyResponse(200, [{"other": "value"}]),
        DummyResponse(200, [{"other": "value"}] * 1000),
        DummyResponse(200, [{"other": "value"}]),
    ]
    calls: list[dict[str, object]] = []

    def fake_get(url, params, headers, timeout):
        calls.append(dict(params))
        return responses.pop(0)

    monkeypatch.setattr(httpx, "get", fake_get)
    transport = SocrataEdmonton311Transport("https://example.invalid")

    rows = transport.fetch(None)

    assert len(rows) == 1001
    assert calls[1] == {"$limit": 1000, "$offset": 0}
    assert calls[2] == {"$limit": 1000, "$offset": 1000}


@pytest.mark.unit
def test_transport_breaks_offset_pagination_on_empty_followup_page(monkeypatch: pytest.MonkeyPatch) -> None:
    responses = [
        DummyResponse(200, [{"other": "value"}]),
        DummyResponse(200, [{"other": "value"}] * 1000),
        DummyResponse(200, []),
    ]

    monkeypatch.setattr(httpx, "get", lambda *args, **kwargs: responses.pop(0))
    transport = SocrataEdmonton311Transport("https://example.invalid")

    assert transport.fetch(None) == [{"other": "value"}] * 1000


@pytest.mark.unit
def test_transport_uses_first_run_lookback_when_no_cursor(monkeypatch: pytest.MonkeyPatch) -> None:
    responses = [
        DummyResponse(200, [{"date_created": "2026-03-01T00:00:00Z"}]),
        DummyResponse(200, [{"date_created": "2026-03-02T00:00:00Z"}]),
    ]
    calls: list[dict[str, object]] = []

    def fake_get(url, params, headers, timeout):
        calls.append(dict(params))
        return responses.pop(0)

    monkeypatch.setattr(httpx, "get", fake_get)
    transport = SocrataEdmonton311Transport("https://example.invalid", first_run_lookback_days=30)

    transport.fetch(None)

    assert calls[1]["$order"] == "date_created ASC"
    assert "$where" in calls[1]
    assert "date_created >=" in str(calls[1]["$where"])


@pytest.mark.unit
def test_transport_skips_first_run_lookback_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    responses = [
        DummyResponse(200, [{"date_created": "2026-03-01T00:00:00Z"}]),
        DummyResponse(200, [{"date_created": "2026-03-02T00:00:00Z"}]),
    ]
    calls: list[dict[str, object]] = []

    def fake_get(url, params, headers, timeout):
        calls.append(dict(params))
        return responses.pop(0)

    monkeypatch.setattr(httpx, "get", fake_get)
    transport = SocrataEdmonton311Transport("https://example.invalid", first_run_lookback_days=0)

    transport.fetch(None)

    assert "$where" not in calls[1]


@pytest.mark.unit
def test_transport_breaks_on_empty_batch_after_sample(monkeypatch: pytest.MonkeyPatch) -> None:
    responses = [
        DummyResponse(200, [{"submitted_date": "2026-03-01T00:00:00Z"}]),
        DummyResponse(200, []),
    ]

    monkeypatch.setattr(httpx, "get", lambda *args, **kwargs: responses.pop(0))
    transport = SocrataEdmonton311Transport("https://example.invalid")

    assert transport.fetch(None) == []


@pytest.mark.unit
def test_transport_breaks_keyset_pagination_when_last_timestamp_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    responses = [
        DummyResponse(200, [{"submitted_date": "2026-03-01T00:00:00Z", ":id": 1}]),
        DummyResponse(200, [{"submitted_date": "2026-03-02T00:00:00Z", ":id": idx} for idx in range(999)] + [{":id": 999}]),
    ]

    monkeypatch.setattr(httpx, "get", lambda *args, **kwargs: responses.pop(0))
    transport = SocrataEdmonton311Transport("https://example.invalid")

    rows = transport.fetch(None)

    assert len(rows) == 1000
    assert rows[-1] == {":id": 999}


@pytest.mark.unit
@pytest.mark.parametrize(
    ("status_code", "error_type"),
    [
        (401, Edmonton311AuthError),
        (403, Edmonton311AuthError),
        (404, Edmonton311UnavailableError),
        (500, Edmonton311UnavailableError),
    ],
)
def test_request_json_maps_http_statuses(monkeypatch: pytest.MonkeyPatch, status_code: int, error_type: type[Exception]) -> None:
    monkeypatch.setattr(httpx, "get", lambda *args, **kwargs: DummyResponse(status_code, []))
    transport = SocrataEdmonton311Transport("https://example.invalid")

    with pytest.raises(error_type):
        transport._request_json({"$limit": 1})


@pytest.mark.unit
def test_request_json_maps_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(*args, **kwargs):
        raise httpx.TimeoutException("timeout")

    monkeypatch.setattr(httpx, "get", fake_get)
    monkeypatch.setattr("app.clients.edmonton_311.time.sleep", lambda *_args, **_kwargs: None)
    transport = SocrataEdmonton311Transport("https://example.invalid", retry_attempts=1)

    with pytest.raises(Edmonton311UnavailableError):
        transport._request_json({"$limit": 1})


@pytest.mark.unit
def test_request_json_retries_timeout_then_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    responses = [
        httpx.TimeoutException("timeout"),
        DummyResponse(200, [{"id": "ok"}]),
    ]
    sleep_calls: list[float] = []

    def fake_get(*args, **kwargs):
        response = responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    monkeypatch.setattr(httpx, "get", fake_get)
    monkeypatch.setattr("app.clients.edmonton_311.time.sleep", lambda seconds: sleep_calls.append(seconds))
    transport = SocrataEdmonton311Transport("https://example.invalid", retry_attempts=2, retry_backoff_seconds=0.25)

    assert transport._request_json({"$limit": 1}) == [{"id": "ok"}]
    assert sleep_calls == [0.25]


@pytest.mark.unit
def test_request_json_maps_generic_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(*args, **kwargs):
        raise httpx.HTTPError("boom")

    monkeypatch.setattr(httpx, "get", fake_get)
    monkeypatch.setattr("app.clients.edmonton_311.time.sleep", lambda *_args, **_kwargs: None)
    transport = SocrataEdmonton311Transport("https://example.invalid", retry_attempts=1)

    with pytest.raises(Edmonton311UnavailableError):
        transport._request_json({"$limit": 1})


@pytest.mark.unit
def test_request_json_retries_http_error_then_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    responses = [
        httpx.HTTPError("boom"),
        DummyResponse(200, [{"id": "ok"}]),
    ]
    sleep_calls: list[float] = []

    def fake_get(*args, **kwargs):
        response = responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    monkeypatch.setattr(httpx, "get", fake_get)
    monkeypatch.setattr("app.clients.edmonton_311.time.sleep", lambda seconds: sleep_calls.append(seconds))
    transport = SocrataEdmonton311Transport("https://example.invalid", retry_attempts=2, retry_backoff_seconds=0.25)

    assert transport._request_json({"$limit": 1}) == [{"id": "ok"}]
    assert sleep_calls == [0.25]


@pytest.mark.unit
def test_request_json_rejects_non_list_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(httpx, "get", lambda *args, **kwargs: DummyResponse(200, {"items": []}))
    transport = SocrataEdmonton311Transport("https://example.invalid")

    with pytest.raises(Edmonton311UnavailableError):
        transport._request_json({"$limit": 1})


@pytest.mark.unit
def test_request_json_retries_on_500_then_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    responses = [
        DummyResponse(500, []),
        DummyResponse(500, []),
        DummyResponse(200, [{"id": "ok"}]),
    ]
    sleep_calls: list[float] = []

    monkeypatch.setattr(httpx, "get", lambda *args, **kwargs: responses.pop(0))
    monkeypatch.setattr("app.clients.edmonton_311.time.sleep", lambda seconds: sleep_calls.append(seconds))
    transport = SocrataEdmonton311Transport(
        "https://example.invalid",
        retry_attempts=3,
        retry_backoff_seconds=0.25,
    )

    payload = transport._request_json({"$limit": 1})

    assert payload == [{"id": "ok"}]
    assert sleep_calls == [0.25, 0.5]


@pytest.mark.unit
def test_request_json_raises_after_retry_exhausted_on_500(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(httpx, "get", lambda *args, **kwargs: DummyResponse(500, []))
    monkeypatch.setattr("app.clients.edmonton_311.time.sleep", lambda *_args, **_kwargs: None)
    transport = SocrataEdmonton311Transport("https://example.invalid", retry_attempts=2)

    with pytest.raises(Edmonton311UnavailableError, match="500"):
        transport._request_json({"$limit": 1})


@pytest.mark.unit
def test_request_json_raises_unavailable_when_retry_loop_is_skipped() -> None:
    transport = SocrataEdmonton311Transport("https://example.invalid")
    transport.retry_attempts = 0

    with pytest.raises(Edmonton311UnavailableError, match="source unavailable"):
        transport._request_json({"$limit": 1})


@pytest.mark.unit
def test_sleep_before_retry_returns_when_backoff_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    sleep_calls: list[float] = []
    monkeypatch.setattr("app.clients.edmonton_311.time.sleep", lambda seconds: sleep_calls.append(seconds))
    transport = SocrataEdmonton311Transport("https://example.invalid", retry_backoff_seconds=0)

    transport._sleep_before_retry(3)

    assert sleep_calls == []


@pytest.mark.unit
def test_build_page_where_without_identifier_uses_timestamp_only() -> None:
    transport = SocrataEdmonton311Transport("https://example.invalid")

    where = transport._build_page_where(
        base_where="submitted_date > '2026-02-28T00:00:00Z'",
        timestamp_field="submitted_date",
        identifier_field=None,
        last_timestamp="2026-03-02T00:00:00Z",
        last_identifier=None,
    )

    assert where == "(submitted_date > '2026-02-28T00:00:00Z') AND submitted_date > '2026-03-02T00:00:00Z'"


@pytest.mark.unit
def test_build_page_where_without_base_where_returns_progression_only() -> None:
    transport = SocrataEdmonton311Transport("https://example.invalid")

    where = transport._build_page_where(
        base_where=None,
        timestamp_field="submitted_date",
        identifier_field=None,
        last_timestamp="2026-03-02T00:00:00Z",
        last_identifier=None,
    )

    assert where == "submitted_date > '2026-03-02T00:00:00Z'"


@pytest.mark.unit
def test_format_soql_literal_formats_booleans() -> None:
    assert SocrataEdmonton311Transport._format_soql_literal(True) == "true"
    assert SocrataEdmonton311Transport._format_soql_literal(False) == "false"


@pytest.mark.unit
def test_pick_field_returns_none_when_missing() -> None:
    assert SocrataEdmonton311Transport._pick_field({"x": 1}, ("a", "b")) is None


class FakeTransport(Edmonton311Transport):
    def __init__(self, rows):
        self.rows = rows

    def fetch(self, cursor: str | None):
        return self.rows


@pytest.mark.unit
def test_fake_transport_fetch_returns_rows() -> None:
    rows = [{"service_request_id": "SR-1"}]
    assert FakeTransport(rows).fetch(None) == rows


@pytest.mark.unit
def test_client_uses_real_transport_by_default() -> None:
    client = Edmonton311Client()
    assert isinstance(client.transport, SocrataEdmonton311Transport)


@pytest.mark.unit
def test_compute_cursor_handles_datetime() -> None:
    client = Edmonton311Client(FakeTransport([]))
    cursor = client._compute_cursor([{"requested_at": datetime(2026, 3, 1, 12, 0, 0)}])
    assert cursor == "2026-03-01T12:00:00"


@pytest.mark.unit
def test_compute_cursor_handles_empty_records() -> None:
    client = Edmonton311Client(FakeTransport([]))
    assert client._compute_cursor([]) is None


@pytest.mark.unit
def test_normalize_row_uses_fallback_fields() -> None:
    client = Edmonton311Client(FakeTransport([]))
    normalized = client._normalize_row(
        {
            ":id": 5,
            "submitted_date": "2026-03-02T00:00:00Z",
            "service_name": "Waste",
        }
    )

    assert normalized["service_request_id"] == "5"
    assert normalized["requested_at"] == "2026-03-02T00:00:00Z"
    assert normalized["category"] == "Waste"


@pytest.mark.unit
def test_normalize_row_uses_unknown_defaults() -> None:
    client = Edmonton311Client(FakeTransport([]))
    normalized = client._normalize_row({"foo": "bar"})

    assert normalized["service_request_id"] == ""
    assert normalized["requested_at"] == ""
    assert normalized["category"] == "unknown"
