from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import os


@dataclass(frozen=True)
class Settings:
    app_env: str
    database_url: str
    source_name: str
    forecast_product_name: str
    weekly_forecast_product_name: str
    edmonton_311_api_url: str
    edmonton_311_api_token: str | None
    jwt_secret: str
    jwt_audience: str
    jwt_issuer: str
    jwt_access_token_expires_minutes: int
    jwt_refresh_token_expires_days: int
    auth_signup_allowlist: str
    auth_refresh_cookie_name: str
    auth_cookie_secure: bool
    auth_cookie_samesite: str
    frontend_origin: str
    scheduler_enabled: bool
    scheduler_cron: str
    forecast_scheduler_enabled: bool
    forecast_scheduler_cron: str
    weekly_forecast_scheduler_enabled: bool
    weekly_forecast_scheduler_cron: str
    weekly_forecast_daily_regeneration_enabled: bool
    weekly_forecast_daily_regeneration_cron: str
    forecast_model_scheduler_enabled: bool
    forecast_model_scheduler_cron: str
    forecast_model_artifact_dir: str
    weekly_forecast_model_scheduler_enabled: bool
    weekly_forecast_model_scheduler_cron: str
    weekly_forecast_model_artifact_dir: str
    edmonton_311_first_run_lookback_days: int
    edmonton_311_retry_attempts: int
    edmonton_311_retry_backoff_seconds: float
    duplicate_review_threshold_percentage: float
    geomet_base_url: str
    geomet_climate_identifier: str | None
    geomet_station_selector: str
    geomet_timeout_seconds: float
    nager_date_base_url: str
    forecast_model_family: str
    forecast_training_lookback_days: int
    weekly_forecast_timezone: str
    weekly_forecast_history_days: int
    visualization_fallback_age_hours: int


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
        forecast_product_name=os.getenv("FORECAST_PRODUCT_NAME", "daily_1_day_demand"),
        weekly_forecast_product_name=os.getenv("WEEKLY_FORECAST_PRODUCT_NAME", "weekly_7_day_demand"),
        edmonton_311_api_url=os.getenv(
            "EDMONTON_311_API_URL",
            "https://data.edmonton.ca/resource/q7ua-agfg.json",
        ),
        edmonton_311_api_token=os.getenv("EDMONTON_311_API_TOKEN") or None,
        jwt_secret=os.getenv("JWT_SECRET", "test-secret-key-311-forecast-system-32b"),
        jwt_audience=os.getenv("JWT_AUDIENCE", "311-forecast-system"),
        jwt_issuer=os.getenv("JWT_ISSUER", "311-forecast-system"),
        jwt_access_token_expires_minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", "60")),
        jwt_refresh_token_expires_days=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES_DAYS", "14")),
        auth_signup_allowlist=os.getenv("AUTH_SIGNUP_ALLOWLIST", "planner@example.com:CityPlanner,manager@example.com:OperationalManager"),
        auth_refresh_cookie_name=os.getenv("AUTH_REFRESH_COOKIE_NAME", "forecast_refresh_token"),
        auth_cookie_secure=_to_bool(os.getenv("AUTH_COOKIE_SECURE"), False),
        auth_cookie_samesite=os.getenv("AUTH_COOKIE_SAMESITE", "lax"),
        frontend_origin=os.getenv("FRONTEND_ORIGIN", "http://localhost:5173"),
        scheduler_enabled=_to_bool(os.getenv("SCHEDULER_ENABLED"), False),
        scheduler_cron=os.getenv("SCHEDULER_CRON", "0 0 * * 0"),
        forecast_scheduler_enabled=_to_bool(os.getenv("FORECAST_SCHEDULER_ENABLED"), False),
        forecast_scheduler_cron=os.getenv("FORECAST_SCHEDULER_CRON", "0 * * * *"),
        weekly_forecast_scheduler_enabled=_to_bool(os.getenv("WEEKLY_FORECAST_SCHEDULER_ENABLED"), False),
        weekly_forecast_scheduler_cron=os.getenv("WEEKLY_FORECAST_SCHEDULER_CRON", "0 1 * * 1"),
        weekly_forecast_daily_regeneration_enabled=_to_bool(os.getenv("WEEKLY_FORECAST_DAILY_REGENERATION_ENABLED"), False),
        weekly_forecast_daily_regeneration_cron=os.getenv("WEEKLY_FORECAST_DAILY_REGENERATION_CRON", "0 2 * * *"),
        forecast_model_scheduler_enabled=_to_bool(os.getenv("FORECAST_MODEL_SCHEDULER_ENABLED"), False),
        forecast_model_scheduler_cron=os.getenv("FORECAST_MODEL_SCHEDULER_CRON", "15 0 * * 0"),
        forecast_model_artifact_dir=os.getenv("FORECAST_MODEL_ARTIFACT_DIR", "backend/.artifacts/forecast_models"),
        weekly_forecast_model_scheduler_enabled=_to_bool(os.getenv("WEEKLY_FORECAST_MODEL_SCHEDULER_ENABLED"), False),
        weekly_forecast_model_scheduler_cron=os.getenv("WEEKLY_FORECAST_MODEL_SCHEDULER_CRON", "30 0 * * 0"),
        weekly_forecast_model_artifact_dir=os.getenv("WEEKLY_FORECAST_MODEL_ARTIFACT_DIR", "backend/.artifacts/weekly_forecast_models"),
        edmonton_311_first_run_lookback_days=int(os.getenv("EDMONTON_311_FIRST_RUN_LOOKBACK_DAYS", "365")),
        edmonton_311_retry_attempts=int(os.getenv("EDMONTON_311_RETRY_ATTEMPTS", "3")),
        edmonton_311_retry_backoff_seconds=float(os.getenv("EDMONTON_311_RETRY_BACKOFF_SECONDS", "0.5")),
        duplicate_review_threshold_percentage=float(os.getenv("DUPLICATE_REVIEW_THRESHOLD_PERCENTAGE", "20")),
        geomet_base_url=os.getenv("GEOMET_BASE_URL", "https://api.weather.gc.ca"),
        geomet_climate_identifier=os.getenv("GEOMET_CLIMATE_IDENTIFIER") or None,
        geomet_station_selector=os.getenv("GEOMET_STATION_SELECTOR", "edmonton_hourly_station"),
        geomet_timeout_seconds=float(os.getenv("GEOMET_TIMEOUT_SECONDS", "30.0")),
        nager_date_base_url=os.getenv("NAGER_DATE_BASE_URL", "https://date.nager.at"),
        forecast_model_family=os.getenv("FORECAST_MODEL_FAMILY", "lightgbm_global"),
        forecast_training_lookback_days=int(os.getenv("FORECAST_TRAINING_LOOKBACK_DAYS", "112")),
        weekly_forecast_timezone=os.getenv("WEEKLY_FORECAST_TIMEZONE", "America/Edmonton"),
        weekly_forecast_history_days=int(os.getenv("WEEKLY_FORECAST_HISTORY_DAYS", "112")),
        visualization_fallback_age_hours=int(os.getenv("VISUALIZATION_FALLBACK_AGE_HOURS", "24")),
    )
