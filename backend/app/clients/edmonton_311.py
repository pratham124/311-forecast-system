from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import time
from typing import Any, Protocol

import httpx

from app.core.config import get_settings


class Edmonton311AuthError(Exception):
    pass


class Edmonton311UnavailableError(Exception):
    pass


class Edmonton311Transport(Protocol):
    def fetch(self, cursor: str | None) -> list[dict[str, Any]]: ...


@dataclass
class Edmonton311FetchResult:
    result_type: str
    records: list[dict[str, Any]]
    cursor_value: str | None


TIMESTAMP_FIELDS = (
    "requested_at",
    "submitted_date",
    "created_at",
    "creation_date",
    "opened_date",
    "date_created",
    "last_modified_date",
    "service_request_date",
    "request_date",
    "timestamp",
)
IDENTIFIER_FIELDS = (
    "service_request_id",
    "service_request_number",
    "request_id",
    "case_id",
    "sr_number",
    "row_id",
    "id",
    ":id",
)
CATEGORY_FIELDS = (
    "category",
    "service_name",
    "service_category",
    "service_description",
    "service_type",
    "problem_type",
    "issue_type",
    "description",
)


class SocrataEdmonton311Transport:
    def __init__(
        self,
        base_url: str,
        api_token: str | None = None,
        timeout: float = 30.0,
        first_run_lookback_days: int = 30,
        retry_attempts: int = 3,
        retry_backoff_seconds: float = 0.5,
    ) -> None:
        self.base_url = base_url
        self.api_token = api_token
        self.timeout = timeout
        self.first_run_lookback_days = first_run_lookback_days
        self.retry_attempts = max(1, retry_attempts)
        self.retry_backoff_seconds = max(0.0, retry_backoff_seconds)

    def _build_first_run_where(self, timestamp_field: str) -> str | None:
        if self.first_run_lookback_days <= 0:
            return None
        lookback_start = datetime.now(timezone.utc) - timedelta(days=self.first_run_lookback_days)
        return f"{timestamp_field} >= '{lookback_start.strftime('%Y-%m-%dT%H:%M:%S')}'"

    def fetch(self, cursor: str | None) -> list[dict[str, Any]]:
        print(f"[debug] transport.fetch sample request cursor={cursor}")
        sample_rows = self._request_json({"$limit": 1})
        print(f"[debug] transport.fetch sample rows count={len(sample_rows)}")
        if not sample_rows:
            return []

        timestamp_field = self._pick_field(sample_rows[0], TIMESTAMP_FIELDS)
        identifier_field = self._pick_field(sample_rows[0], IDENTIFIER_FIELDS)
        print(f"[debug] transport.fetch timestamp_field={timestamp_field}")
        print(f"[debug] transport.fetch identifier_field={identifier_field}")
        if timestamp_field:
            return self._fetch_with_keyset_pagination(
                cursor=cursor,
                timestamp_field=timestamp_field,
                identifier_field=identifier_field,
            )

        return self._fetch_with_offset_pagination()

    def _fetch_with_keyset_pagination(
        self,
        cursor: str | None,
        timestamp_field: str,
        identifier_field: str | None,
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        limit = 1000
        base_where = self._build_initial_where(cursor, timestamp_field)
        last_timestamp: Any | None = None
        last_identifier: Any | None = None

        while True:
            params: dict[str, str | int] = {
                "$limit": limit,
                "$order": self._build_order_clause(timestamp_field, identifier_field),
            }
            page_where = self._build_page_where(
                base_where=base_where,
                timestamp_field=timestamp_field,
                identifier_field=identifier_field,
                last_timestamp=last_timestamp,
                last_identifier=last_identifier,
            )
            if page_where:
                params["$where"] = page_where
            print(f"[debug] transport.fetch batch request params={params}")
            batch = self._request_json(params)
            print(f"[debug] transport.fetch batch rows count={len(batch)} keyset_cursor={last_timestamp}/{last_identifier}")
            if not batch:
                break
            rows.extend(batch)
            if len(batch) < limit:
                break
            last_row = batch[-1]
            last_timestamp = last_row.get(timestamp_field)
            last_identifier = last_row.get(identifier_field) if identifier_field else None
            if last_timestamp is None:
                break

        return rows

    def _fetch_with_offset_pagination(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        offset = 0
        limit = 1000

        while True:
            params: dict[str, str | int] = {"$limit": limit, "$offset": offset}
            print(f"[debug] transport.fetch batch request params={params}")
            batch = self._request_json(params)
            print(f"[debug] transport.fetch batch rows count={len(batch)} offset={offset}")
            if not batch:
                break
            rows.extend(batch)
            if len(batch) < limit:
                break
            offset += limit

        return rows

    def _request_json(self, params: dict[str, str | int]) -> list[dict[str, Any]]:
        headers = {"Accept": "application/json"}
        if self.api_token:
            headers["X-App-Token"] = self.api_token
        last_error: Exception | None = None

        for attempt in range(1, self.retry_attempts + 1):
            try:
                print(
                    f"[debug] httpx.get start url={self.base_url} params={params} "
                    f"attempt={attempt}/{self.retry_attempts}"
                )
                response = httpx.get(self.base_url, params=params, headers=headers, timeout=self.timeout)
                print(
                    f"[debug] httpx.get complete status={response.status_code} params={params} "
                    f"attempt={attempt}/{self.retry_attempts}"
                )
            except httpx.TimeoutException as exc:
                print(f"[debug] httpx.get timeout params={params} error={exc} attempt={attempt}/{self.retry_attempts}")
                last_error = Edmonton311UnavailableError("Timeout from Edmonton 311 source")
                if attempt == self.retry_attempts:
                    raise last_error from exc
                self._sleep_before_retry(attempt)
                continue
            except httpx.HTTPError as exc:
                print(f"[debug] httpx.get http error params={params} error={exc} attempt={attempt}/{self.retry_attempts}")
                last_error = Edmonton311UnavailableError("Edmonton 311 source unavailable")
                if attempt == self.retry_attempts:
                    raise last_error from exc
                self._sleep_before_retry(attempt)
                continue

            if response.status_code in {401, 403}:
                raise Edmonton311AuthError("Edmonton 311 authentication failed")
            if response.status_code >= 500:
                last_error = Edmonton311UnavailableError(f"Edmonton 311 source error: {response.status_code}")
                if attempt == self.retry_attempts:
                    raise last_error
                self._sleep_before_retry(attempt)
                continue
            if response.status_code >= 400:
                raise Edmonton311UnavailableError(f"Edmonton 311 request failed: {response.status_code}")

            payload = response.json()
            if not isinstance(payload, list):
                raise Edmonton311UnavailableError("Unexpected Edmonton 311 response payload")
            return payload

        raise last_error or Edmonton311UnavailableError("Edmonton 311 source unavailable")

    def _sleep_before_retry(self, attempt: int) -> None:
        if self.retry_backoff_seconds <= 0:
            return
        time.sleep(self.retry_backoff_seconds * attempt)

    def _build_initial_where(self, cursor: str | None, timestamp_field: str) -> str | None:
        if cursor:
            return f"{timestamp_field} > {self._format_soql_literal(cursor)}"
        return self._build_first_run_where(timestamp_field)

    @staticmethod
    def _build_order_clause(timestamp_field: str, identifier_field: str | None) -> str:
        if identifier_field:
            return f"{timestamp_field} ASC, {identifier_field} ASC"
        return f"{timestamp_field} ASC"

    def _build_page_where(
        self,
        base_where: str | None,
        timestamp_field: str,
        identifier_field: str | None,
        last_timestamp: Any | None,
        last_identifier: Any | None,
    ) -> str | None:
        if last_timestamp is None:
            return base_where

        if identifier_field and last_identifier is not None:
            progression_where = (
                f"({timestamp_field} > {self._format_soql_literal(last_timestamp)} "
                f"OR ({timestamp_field} = {self._format_soql_literal(last_timestamp)} "
                f"AND {identifier_field} > {self._format_soql_literal(last_identifier)}))"
            )
        else:
            progression_where = f"{timestamp_field} > {self._format_soql_literal(last_timestamp)}"

        if base_where:
            return f"({base_where}) AND {progression_where}"
        return progression_where

    @staticmethod
    def _format_soql_literal(value: Any) -> str:
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (int, float)):
            return str(value)
        escaped = str(value).replace("'", "''")
        return f"'{escaped}'"

    @staticmethod
    def _pick_field(record: dict[str, Any], candidates: tuple[str, ...]) -> str | None:
        for candidate in candidates:
            if candidate in record:
                return candidate
        return None


class Edmonton311Client:
    def __init__(self, transport: Edmonton311Transport | None = None) -> None:
        self.settings = get_settings()
        self.transport = transport or SocrataEdmonton311Transport(
            base_url=self.settings.edmonton_311_api_url,
            api_token=self.settings.edmonton_311_api_token,
            first_run_lookback_days=self.settings.edmonton_311_first_run_lookback_days,
            retry_attempts=self.settings.edmonton_311_retry_attempts,
            retry_backoff_seconds=self.settings.edmonton_311_retry_backoff_seconds,
        )

    def _compute_cursor(self, records: list[dict[str, Any]]) -> str | None:
        if not records:
            return None
        latest = max(record["requested_at"] for record in records)
        if isinstance(latest, datetime):
            return latest.isoformat()
        return str(latest)

    def _normalize_row(self, record: dict[str, Any]) -> dict[str, Any]:
        timestamp_field = next((field for field in TIMESTAMP_FIELDS if field in record), None)
        identifier_field = next((field for field in IDENTIFIER_FIELDS if field in record), None)
        category_field = next((field for field in CATEGORY_FIELDS if field in record), None)
        normalized = dict(record)
        normalized["service_request_id"] = str(record.get(identifier_field or ":id", record.get(":id", "")))
        normalized["requested_at"] = record.get(timestamp_field) or ""
        normalized["category"] = record.get(category_field) or "unknown"
        return normalized

    def fetch_records(self, cursor: str | None) -> Edmonton311FetchResult:
        raw_records = self.transport.fetch(cursor)
        if not raw_records:
            return Edmonton311FetchResult(
                result_type="no_new_records",
                records=[],
                cursor_value=cursor,
            )
        records = [self._normalize_row(record) for record in raw_records]
        return Edmonton311FetchResult(
            result_type="new_data",
            records=records,
            cursor_value=self._compute_cursor(records),
        )
