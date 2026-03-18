from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import os


@dataclass(frozen=True)
class Settings:
    app_env: str
    database_url: str
    source_name: str
    edmonton_311_api_url: str
    edmonton_311_api_token: str | None
    jwt_secret: str
    jwt_audience: str
    jwt_issuer: str
    scheduler_enabled: bool
    scheduler_cron: str
    edmonton_311_first_run_lookback_days: int
    edmonton_311_retry_attempts: int
    edmonton_311_retry_backoff_seconds: float


def _to_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL must be set for application runtime")
    return Settings(
        app_env=os.getenv("APP_ENV", "development"),
        database_url=database_url,
        source_name=os.getenv("EDMONTON_311_SOURCE_NAME", "edmonton_311"),
        edmonton_311_api_url=os.getenv(
            "EDMONTON_311_API_URL",
            "https://data.edmonton.ca/resource/q7ua-agfg.json",
        ),
        edmonton_311_api_token=os.getenv("EDMONTON_311_API_TOKEN") or None,
        jwt_secret=os.getenv("JWT_SECRET", "test-secret"),
        jwt_audience=os.getenv("JWT_AUDIENCE", "311-forecast-system"),
        jwt_issuer=os.getenv("JWT_ISSUER", "311-forecast-system"),
        scheduler_enabled=_to_bool(os.getenv("SCHEDULER_ENABLED"), False),
        scheduler_cron=os.getenv("SCHEDULER_CRON", "0 0 * * 0"),
        edmonton_311_first_run_lookback_days=int(os.getenv("EDMONTON_311_FIRST_RUN_LOOKBACK_DAYS", "700")),
        edmonton_311_retry_attempts=int(os.getenv("EDMONTON_311_RETRY_ATTEMPTS", "3")),
        edmonton_311_retry_backoff_seconds=float(os.getenv("EDMONTON_311_RETRY_BACKOFF_SECONDS", "0.5")),
    )
