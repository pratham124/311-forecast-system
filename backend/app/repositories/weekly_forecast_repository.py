from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CurrentWeeklyForecastMarker, WeeklyForecastBucket, WeeklyForecastVersion


class WeeklyForecastRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_forecast_version(
        self,
        *,
        weekly_forecast_run_id: str,
        source_cleaned_dataset_version_id: str,
        week_start_local: datetime,
        week_end_local: datetime,
        geography_scope: str,
        baseline_method: str,
        summary: str,
    ) -> WeeklyForecastVersion:
        version = WeeklyForecastVersion(
            weekly_forecast_run_id=weekly_forecast_run_id,
            source_cleaned_dataset_version_id=source_cleaned_dataset_version_id,
            week_start_local=week_start_local,
            week_end_local=week_end_local,
            geography_scope=geography_scope,
            baseline_method=baseline_method,
            storage_status="pending",
            summary=summary,
        )
        self.session.add(version)
        self.session.flush()
        return version

    def store_buckets(self, weekly_forecast_version_id: str, buckets: list[dict[str, object]]) -> None:
        rows = [
            WeeklyForecastBucket(
                weekly_forecast_version_id=weekly_forecast_version_id,
                forecast_date_local=bucket["forecast_date_local"],
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

    def mark_version_stored(self, weekly_forecast_version_id: str) -> WeeklyForecastVersion:
        version = self._require_version(weekly_forecast_version_id)
        version.storage_status = "stored"
        version.stored_at = datetime.utcnow()
        self.session.flush()
        return version

    def activate_forecast(
        self,
        *,
        forecast_product_name: str,
        weekly_forecast_version_id: str,
        source_cleaned_dataset_version_id: str,
        week_start_local: datetime,
        week_end_local: datetime,
        updated_by_run_id: str,
        geography_scope: str,
    ) -> CurrentWeeklyForecastMarker:
        prior_versions = self.session.scalars(
            select(WeeklyForecastVersion).where(WeeklyForecastVersion.is_current.is_(True))
        ).all()
        for version in prior_versions:
            version.is_current = False

        version = self._require_version(weekly_forecast_version_id)
        version.is_current = True
        version.activated_at = datetime.utcnow()

        marker = self.session.get(CurrentWeeklyForecastMarker, forecast_product_name)
        if marker is None:
            marker = CurrentWeeklyForecastMarker(
                forecast_product_name=forecast_product_name,
                weekly_forecast_version_id=weekly_forecast_version_id,
                source_cleaned_dataset_version_id=source_cleaned_dataset_version_id,
                week_start_local=week_start_local,
                week_end_local=week_end_local,
                geography_scope=geography_scope,
                updated_by_run_id=updated_by_run_id,
            )
            self.session.add(marker)
        else:
            marker.weekly_forecast_version_id = weekly_forecast_version_id
            marker.source_cleaned_dataset_version_id = source_cleaned_dataset_version_id
            marker.week_start_local = week_start_local
            marker.week_end_local = week_end_local
            marker.geography_scope = geography_scope
            marker.updated_at = datetime.utcnow()
            marker.updated_by_run_id = updated_by_run_id
        self.session.flush()
        return marker

    def get_current_marker(self, forecast_product_name: str) -> CurrentWeeklyForecastMarker | None:
        return self.session.get(CurrentWeeklyForecastMarker, forecast_product_name)

    def get_forecast_version(self, weekly_forecast_version_id: str) -> WeeklyForecastVersion | None:
        return self.session.get(WeeklyForecastVersion, weekly_forecast_version_id)

    def list_buckets(self, weekly_forecast_version_id: str) -> list[WeeklyForecastBucket]:
        statement = (
            select(WeeklyForecastBucket)
            .where(WeeklyForecastBucket.weekly_forecast_version_id == weekly_forecast_version_id)
            .order_by(
                WeeklyForecastBucket.forecast_date_local.asc(),
                WeeklyForecastBucket.service_category.asc(),
                WeeklyForecastBucket.geography_key.asc(),
            )
        )
        return list(self.session.scalars(statement))

    def list_buckets_filtered(
        self,
        version_ids: list[str],
        *,
        service_categories: list[str] | None = None,
        date_start: date | None = None,
        date_end: date | None = None,
        geography_keys: list[str] | None = None,
    ) -> list[WeeklyForecastBucket]:
        """Fetch buckets for multiple weekly versions in one query, with all filters in SQL."""
        if not version_ids:
            return []
        statement = (
            select(WeeklyForecastBucket)
            .where(WeeklyForecastBucket.weekly_forecast_version_id.in_(version_ids))
        )
        if service_categories:
            statement = statement.where(WeeklyForecastBucket.service_category.in_(service_categories))
        if date_start is not None:
            statement = statement.where(WeeklyForecastBucket.forecast_date_local >= date_start)
        if date_end is not None:
            statement = statement.where(WeeklyForecastBucket.forecast_date_local < date_end)
        if geography_keys is not None:
            statement = statement.where(WeeklyForecastBucket.geography_key.in_(geography_keys))
        statement = statement.order_by(
            WeeklyForecastBucket.forecast_date_local.asc(),
            WeeklyForecastBucket.service_category.asc(),
            WeeklyForecastBucket.geography_key.asc(),
        )
        return list(self.session.scalars(statement))


    def list_service_categories(self, weekly_forecast_version_id: str) -> list[str]:
        return sorted({bucket.service_category for bucket in self.list_buckets(weekly_forecast_version_id) if bucket.service_category})

    def list_current_service_categories(self, forecast_product_name: str) -> list[str]:
        marker = self.get_current_marker(forecast_product_name)
        if marker is None:
            return []
        version = self.get_forecast_version(marker.weekly_forecast_version_id)
        if version is None or version.storage_status != "stored":
            return []
        return self.list_service_categories(version.weekly_forecast_version_id)

    def find_latest_stored_version(self) -> WeeklyForecastVersion | None:
        statement = (
            select(WeeklyForecastVersion)
            .where(WeeklyForecastVersion.storage_status == 'stored')
            .order_by(WeeklyForecastVersion.week_end_local.desc(), WeeklyForecastVersion.stored_at.desc().nullslast(), WeeklyForecastVersion.weekly_forecast_version_id.desc())
            .limit(1)
        )
        return self.session.scalar(statement)

    def find_latest_stored_version_ending_by(self, cutoff: datetime) -> WeeklyForecastVersion | None:
        statement = (
            select(WeeklyForecastVersion)
            .where(WeeklyForecastVersion.storage_status == 'stored', WeeklyForecastVersion.week_end_local <= cutoff)
            .order_by(WeeklyForecastVersion.week_end_local.desc(), WeeklyForecastVersion.stored_at.desc().nullslast(), WeeklyForecastVersion.weekly_forecast_version_id.desc())
            .limit(1)
        )
        return self.session.scalar(statement)

    def find_current_for_week(
        self,
        *,
        forecast_product_name: str,
        week_start_local: datetime,
        week_end_local: datetime,
    ) -> WeeklyForecastVersion | None:
        marker = self.get_current_marker(forecast_product_name)
        if marker is None:
            return None
        if marker.week_start_local != week_start_local or marker.week_end_local != week_end_local:
            return None
        version = self.get_forecast_version(marker.weekly_forecast_version_id)
        if version is None or version.storage_status != "stored":
            return None
        return version

    def list_stored_versions_overlapping_range(
        self,
        *,
        range_start: datetime,
        range_end: datetime,
    ) -> list[WeeklyForecastVersion]:
        statement = (
            select(WeeklyForecastVersion)
            .where(
                WeeklyForecastVersion.storage_status == "stored",
                WeeklyForecastVersion.week_end_local >= range_start,
                WeeklyForecastVersion.week_start_local <= range_end,
            )
            .order_by(
                WeeklyForecastVersion.stored_at.desc().nullslast(),
                WeeklyForecastVersion.activated_at.desc().nullslast(),
                WeeklyForecastVersion.weekly_forecast_version_id.desc(),
            )
        )
        return list(self.session.scalars(statement))

    def _require_version(self, weekly_forecast_version_id: str) -> WeeklyForecastVersion:
        version = self.get_forecast_version(weekly_forecast_version_id)
        if version is None:
            raise ValueError("Weekly forecast version not found")
        return version
