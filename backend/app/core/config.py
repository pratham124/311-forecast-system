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
    weather_provider: str
    geomet_base_url: str
    geomet_climate_identifier: str | None
    geomet_station_selector: str
    geomet_timeout_seconds: float
    open_meteo_base_url: str
    open_meteo_latitude: float
    open_meteo_longitude: float
    open_meteo_timeout_seconds: float
    nager_date_base_url: str
    forecast_model_family: str
    forecast_training_lookback_days: int
    weekly_forecast_timezone: str
    weekly_forecast_history_days: int
    visualization_fallback_age_hours: int
    forecast_confidence_signal_lookback_hours: int
    forecast_confidence_normal_message: str
    forecast_confidence_signals_missing_message: str
    forecast_confidence_dismissed_message: str
    forecast_confidence_missing_inputs_message: str
    forecast_confidence_anomaly_message: str
    forecast_confidence_combined_message: str
    evaluation_forecast_products: str
    evaluation_baseline_methods: str
    evaluation_scheduler_enabled: bool
    evaluation_scheduler_cron: str


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
        edmonton_311_first_run_lookback_days=int(os.getenv("EDMONTON_311_FIRST_RUN_LOOKBACK_DAYS", "112")),
        edmonton_311_retry_attempts=int(os.getenv("EDMONTON_311_RETRY_ATTEMPTS", "3")),
        edmonton_311_retry_backoff_seconds=float(os.getenv("EDMONTON_311_RETRY_BACKOFF_SECONDS", "0.5")),
        duplicate_review_threshold_percentage=float(os.getenv("DUPLICATE_REVIEW_THRESHOLD_PERCENTAGE", "20")),
        weather_provider=os.getenv("WEATHER_PROVIDER", "open_meteo"),
        geomet_base_url=os.getenv("GEOMET_BASE_URL", "https://api.weather.gc.ca"),
        geomet_climate_identifier=os.getenv("GEOMET_CLIMATE_IDENTIFIER") or None,
        geomet_station_selector=os.getenv("GEOMET_STATION_SELECTOR", "edmonton_hourly_station"),
        geomet_timeout_seconds=float(os.getenv("GEOMET_TIMEOUT_SECONDS", "30.0")),
        open_meteo_base_url=os.getenv("OPEN_METEO_BASE_URL", "https://api.open-meteo.com/v1"),
        open_meteo_latitude=float(os.getenv("OPEN_METEO_LATITUDE", "53.5461")),
        open_meteo_longitude=float(os.getenv("OPEN_METEO_LONGITUDE", "-113.4938")),
        open_meteo_timeout_seconds=float(os.getenv("OPEN_METEO_TIMEOUT_SECONDS", "30.0")),
        nager_date_base_url=os.getenv("NAGER_DATE_BASE_URL", "https://date.nager.at"),
        forecast_model_family=os.getenv("FORECAST_MODEL_FAMILY", "lightgbm_global"),
        forecast_training_lookback_days=int(os.getenv("FORECAST_TRAINING_LOOKBACK_DAYS", "112")),
        weekly_forecast_timezone=os.getenv("WEEKLY_FORECAST_TIMEZONE", "America/Edmonton"),
        weekly_forecast_history_days=int(os.getenv("WEEKLY_FORECAST_HISTORY_DAYS", "112")),
        visualization_fallback_age_hours=int(os.getenv("VISUALIZATION_FALLBACK_AGE_HOURS", "24")),
        forecast_confidence_signal_lookback_hours=int(os.getenv("FORECAST_CONFIDENCE_SIGNAL_LOOKBACK_HOURS", "48")),
        forecast_confidence_normal_message=os.getenv(
            "FORECAST_CONFIDENCE_NORMAL_MESSAGE",
            "Forecast confidence is normal for the current selection.",
        ),
        forecast_confidence_signals_missing_message=os.getenv(
            "FORECAST_CONFIDENCE_SIGNALS_MISSING_MESSAGE",
            "Forecast confidence could not be fully assessed with the currently available signals.",
        ),
        forecast_confidence_dismissed_message=os.getenv(
            "FORECAST_CONFIDENCE_DISMISSED_MESSAGE",
            "Recent confidence warnings were reviewed and dismissed for the current selection.",
        ),
        forecast_confidence_missing_inputs_message=os.getenv(
            "FORECAST_CONFIDENCE_MISSING_INPUTS_MESSAGE",
            "Forecast confidence is reduced because some visualization inputs are missing.",
        ),
        forecast_confidence_anomaly_message=os.getenv(
            "FORECAST_CONFIDENCE_ANOMALY_MESSAGE",
            "Forecast confidence is reduced because recent surge conditions were confirmed for the selected service areas.",
        ),
        forecast_confidence_combined_message=os.getenv(
            "FORECAST_CONFIDENCE_COMBINED_MESSAGE",
            "Forecast confidence is reduced because some visualization inputs are missing and recent surge conditions were confirmed for the selected service areas.",
        ),
        evaluation_forecast_products=os.getenv("EVALUATION_FORECAST_PRODUCTS", "daily_1_day,weekly_7_day"),
        evaluation_baseline_methods=os.getenv("EVALUATION_BASELINE_METHODS", "seasonal_naive,moving_average"),
        evaluation_scheduler_enabled=_to_bool(os.getenv("EVALUATION_SCHEDULER_ENABLED"), False),
        evaluation_scheduler_cron=os.getenv("EVALUATION_SCHEDULER_CRON", "0 3 * * *"),
    )
