from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clients.weather_client import get_weather_enrichment_source
from app.models import CurrentForecastMarker, ForecastBucket, ForecastVersion




def _normalize_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)

class ForecastRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_forecast_version(
        self,
        *,
        forecast_run_id: str,
        source_cleaned_dataset_version_id: str,
        horizon_start: datetime,
        horizon_end: datetime,
        geography_scope: str,
        baseline_method: str,
        summary: str,
    ) -> ForecastVersion:
        version = ForecastVersion(
            forecast_run_id=forecast_run_id,
            source_cleaned_dataset_version_id=source_cleaned_dataset_version_id,
            weather_enrichment_source=get_weather_enrichment_source(),
            holiday_enrichment_source="nager_date_canada",
            horizon_start=horizon_start,
            horizon_end=horizon_end,
            geography_scope=geography_scope,
            baseline_method=baseline_method,
            storage_status="pending",
            summary=summary,
        )
        self.session.add(version)
        self.session.flush()
        return version

    def store_buckets(self, forecast_version_id: str, buckets: list[dict[str, object]]) -> None:
        rows = [
            ForecastBucket(
                forecast_version_id=forecast_version_id,
                bucket_start=bucket["bucket_start"],
                bucket_end=bucket["bucket_end"],
                service_category=str(bucket["service_category"]),
                geography_key=bucket.get("geography_key"),
                point_forecast=float(bucket["point_forecast"]),
                quantile_p10=float(bucket["quantile_p10"]),
                quantile_p50=float(bucket["quantile_p50"]),
                quantile_p90=float(bucket["quantile_p90"]),
                baseline_value=float(bucket["baseline_value"]),
            )
            for bucket in buckets
        ]
        self.session.add_all(rows)
        self.session.flush()

    def mark_version_stored(self, forecast_version_id: str, bucket_count: int) -> ForecastVersion:
        version = self._require_version(forecast_version_id)
        version.storage_status = "stored"
        version.bucket_count = bucket_count
        version.stored_at = datetime.utcnow()
        self.session.flush()
        return version

    def activate_forecast(
        self,
        *,
        forecast_product_name: str,
        forecast_version_id: str,
        source_cleaned_dataset_version_id: str,
        horizon_start: datetime,
        horizon_end: datetime,
        updated_by_run_id: str,
        geography_scope: str,
    ) -> CurrentForecastMarker:
        prior_versions = self.session.scalars(
            select(ForecastVersion).where(ForecastVersion.is_current.is_(True))
        ).all()
        for version in prior_versions:
            version.is_current = False

        version = self._require_version(forecast_version_id)
        version.is_current = True
        version.activated_at = datetime.utcnow()

        marker = self.session.get(CurrentForecastMarker, forecast_product_name)
        if marker is None:
            marker = CurrentForecastMarker(
                forecast_product_name=forecast_product_name,
                forecast_version_id=forecast_version_id,
                source_cleaned_dataset_version_id=source_cleaned_dataset_version_id,
                horizon_start=horizon_start,
                horizon_end=horizon_end,
                updated_by_run_id=updated_by_run_id,
                geography_scope=geography_scope,
            )
            self.session.add(marker)
        else:
            marker.forecast_version_id = forecast_version_id
            marker.source_cleaned_dataset_version_id = source_cleaned_dataset_version_id
            marker.horizon_start = horizon_start
            marker.horizon_end = horizon_end
            marker.updated_at = datetime.utcnow()
            marker.updated_by_run_id = updated_by_run_id
            marker.geography_scope = geography_scope
        self.session.flush()
        return marker

    def get_current_marker(self, forecast_product_name: str) -> CurrentForecastMarker | None:
        return self.session.get(CurrentForecastMarker, forecast_product_name)

    def get_forecast_version(self, forecast_version_id: str) -> ForecastVersion | None:
        return self.session.get(ForecastVersion, forecast_version_id)

    def list_buckets(self, forecast_version_id: str) -> list[ForecastBucket]:
        statement = (
            select(ForecastBucket)
            .where(ForecastBucket.forecast_version_id == forecast_version_id)
            .order_by(
                ForecastBucket.bucket_start.asc(),
                ForecastBucket.service_category.asc(),
                ForecastBucket.geography_key.asc(),
            )
        )
        return list(self.session.scalars(statement))

    def list_buckets_filtered(
        self,
        version_ids: list[str],
        *,
        service_categories: list[str] | None = None,
        time_start: datetime | None = None,
        time_end: datetime | None = None,
        geography_keys: list[str] | None = None,
    ) -> list[ForecastBucket]:
        """Fetch buckets for multiple versions in one query, with all filters in SQL."""
        if not version_ids:
            return []
        statement = (
            select(ForecastBucket)
            .where(ForecastBucket.forecast_version_id.in_(version_ids))
        )
        if service_categories:
            statement = statement.where(ForecastBucket.service_category.in_(service_categories))
        if time_start is not None:
            statement = statement.where(ForecastBucket.bucket_start >= time_start)
        if time_end is not None:
            statement = statement.where(ForecastBucket.bucket_start < time_end)
        if geography_keys is not None:
            statement = statement.where(ForecastBucket.geography_key.in_(geography_keys))
        statement = statement.order_by(
            ForecastBucket.bucket_start.asc(),
            ForecastBucket.service_category.asc(),
            ForecastBucket.geography_key.asc(),
        )
        return list(self.session.scalars(statement))


    def list_service_categories(self, forecast_version_id: str) -> list[str]:
        return sorted({bucket.service_category for bucket in self.list_buckets(forecast_version_id) if bucket.service_category})

    def list_current_service_categories(self, forecast_product_name: str) -> list[str]:
        marker = self.get_current_marker(forecast_product_name)
        if marker is None:
            return []
        version = self.get_forecast_version(marker.forecast_version_id)
        if version is None or version.storage_status != "stored":
            return []
        return self.list_service_categories(version.forecast_version_id)

    def find_latest_stored_version(self) -> ForecastVersion | None:
        statement = (
            select(ForecastVersion)
            .where(ForecastVersion.storage_status == 'stored')
            .order_by(ForecastVersion.horizon_end.desc(), ForecastVersion.stored_at.desc().nullslast(), ForecastVersion.forecast_version_id.desc())
            .limit(1)
        )
        return self.session.scalar(statement)

    def find_latest_stored_version_ending_by(self, cutoff: datetime) -> ForecastVersion | None:
        statement = (
            select(ForecastVersion)
            .where(ForecastVersion.storage_status == 'stored', ForecastVersion.horizon_end <= cutoff)
            .order_by(ForecastVersion.horizon_end.desc(), ForecastVersion.stored_at.desc().nullslast(), ForecastVersion.forecast_version_id.desc())
            .limit(1)
        )
        return self.session.scalar(statement)

    def find_current_for_horizon(
        self,
        *,
        forecast_product_name: str,
        horizon_start: datetime,
        horizon_end: datetime,
    ) -> ForecastVersion | None:
        marker = self.get_current_marker(forecast_product_name)
        if marker is None:
            return None
        if _normalize_utc(marker.horizon_start) != _normalize_utc(horizon_start) or _normalize_utc(marker.horizon_end) != _normalize_utc(horizon_end):
            return None
        version = self.get_forecast_version(marker.forecast_version_id)
        if version is None:
            return None
        return version if version.storage_status == "stored" else None

    def list_stored_versions_overlapping_range(
        self,
        *,
        range_start: datetime,
        range_end: datetime,
    ) -> list[ForecastVersion]:
        statement = (
            select(ForecastVersion)
            .where(
                ForecastVersion.storage_status == "stored",
                ForecastVersion.horizon_end >= range_start,
                ForecastVersion.horizon_start <= range_end,
            )
            .order_by(
                ForecastVersion.stored_at.desc().nullslast(),
                ForecastVersion.activated_at.desc().nullslast(),
                ForecastVersion.forecast_version_id.desc(),
            )
        )
        return list(self.session.scalars(statement))

    def _require_version(self, forecast_version_id: str) -> ForecastVersion:
        version = self.get_forecast_version(forecast_version_id)
        if version is None:
            raise ValueError("Forecast version not found")
        return version
