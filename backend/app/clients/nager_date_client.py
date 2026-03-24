from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Protocol

import httpx

from app.core.config import get_settings


class NagerDateClientError(RuntimeError):
    pass


class NagerDateTransport(Protocol):
    def fetch_holidays(self, year: int, country_code: str = "CA") -> list[dict[str, object]]: ...


ALBERTA_SUBDIVISION_CODE = "CA-AB"


class NagerDateHttpTransport:
    def __init__(self, *, base_url: str, timeout: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def fetch_holidays(self, year: int, country_code: str = "CA") -> list[dict[str, object]]:
        url = f"{self.base_url}/api/v3/PublicHolidays/{year}/{country_code}"
        print(f"[debug][forecast] nager request start endpoint={url} year={year} country={country_code}")
        try:
            response = httpx.get(url, headers={"Accept": "application/json"}, timeout=self.timeout)
        except httpx.TimeoutException as exc:
            print(f"[debug][forecast] nager request fail endpoint={url} year={year} country={country_code} error=timeout")
            raise NagerDateClientError("Nager.Date request timed out") from exc
        except httpx.HTTPError as exc:
            print(f"[debug][forecast] nager request fail endpoint={url} year={year} country={country_code} error=http")
            raise NagerDateClientError("Nager.Date request failed") from exc

        if response.status_code >= 400:
            print(f"[debug][forecast] nager request fail endpoint={url} year={year} country={country_code} status={response.status_code}")
            raise NagerDateClientError(f"Nager.Date request failed: {response.status_code}")

        payload = response.json()
        if not isinstance(payload, list):
            print(f"[debug][forecast] nager request fail endpoint={url} year={year} country={country_code} error=unexpected_payload")
            raise NagerDateClientError("Unexpected Nager.Date response payload")

        normalized: list[dict[str, object]] = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            if not _is_alberta_holiday(item):
                continue
            holiday_date = item.get("date")
            name = item.get("name") or item.get("localName")
            if not isinstance(holiday_date, str) or not holiday_date:
                continue
            normalized.append(
                {
                    "date": holiday_date,
                    "name": str(name or "Holiday"),
                    "countryCode": str(item.get("countryCode") or country_code),
                }
            )
        print(f"[debug][forecast] nager request end endpoint={url} year={year} country={country_code} rows={len(payload)} filtered={len(normalized)}")
        return normalized


@dataclass
class NagerDateClient:
    transport: NagerDateTransport | None = None

    def __post_init__(self) -> None:
        if self.transport is None:
            settings = get_settings()
            self.transport = NagerDateHttpTransport(base_url=settings.nager_date_base_url)

    def fetch_holidays(self, year: int, country_code: str = "CA") -> list[dict[str, object]]:
        if self.transport is not None:
            if hasattr(self.transport, "fetch_holidays"):
                print(f"[debug][forecast] nager client path=transport.fetch_holidays year={year} country={country_code}")
                return list(self.transport.fetch_holidays(year, country_code))
            if hasattr(self.transport, "fetch"):
                print(f"[debug][forecast] nager client path=transport.fetch year={year} country={country_code}")
                return list(self.transport.fetch(year, country_code))
        print(f"[debug][forecast] nager client fallback=default year={year} country={country_code}")
        return [
            {
                "date": date(year, 1, 1).isoformat(),
                "name": "New Year's Day",
                "countryCode": country_code,
            }
        ]



def _is_alberta_holiday(item: dict[str, object]) -> bool:
    if item.get("global") is True:
        return True
    counties = item.get("counties")
    if not isinstance(counties, list):
        return False
    return ALBERTA_SUBDIVISION_CODE in {str(value) for value in counties}
