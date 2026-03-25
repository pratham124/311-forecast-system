from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CurrentForecastModelMarker, ForecastModelArtifact, ForecastModelRun


class ForecastModelRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_run(
        self,
        *,
        forecast_product_name: str,
        trigger_type: str,
        source_cleaned_dataset_version_id: str | None,
        training_window_start: datetime,
        training_window_end: datetime,
    ) -> ForecastModelRun:
        run = ForecastModelRun(
            forecast_product_name=forecast_product_name,
            trigger_type=trigger_type,
            source_cleaned_dataset_version_id=source_cleaned_dataset_version_id,
            training_window_start=training_window_start,
            training_window_end=training_window_end,
            status="running",
        )
        self.session.add(run)
        self.session.flush()
        return run

    def get_run(self, forecast_model_run_id: str) -> ForecastModelRun | None:
        return self.session.get(ForecastModelRun, forecast_model_run_id)

    def create_artifact(
        self,
        *,
        forecast_product_name: str,
        forecast_model_run_id: str,
        source_cleaned_dataset_version_id: str,
        geography_scope: str,
        model_family: str,
        baseline_method: str,
        feature_schema_version: str,
        artifact_path: str,
        summary: str,
    ) -> ForecastModelArtifact:
        artifact = ForecastModelArtifact(
            forecast_product_name=forecast_product_name,
            forecast_model_run_id=forecast_model_run_id,
            source_cleaned_dataset_version_id=source_cleaned_dataset_version_id,
            geography_scope=geography_scope,
            model_family=model_family,
            baseline_method=baseline_method,
            feature_schema_version=feature_schema_version,
            artifact_path=artifact_path,
            storage_status="stored",
            trained_at=datetime.utcnow(),
            summary=summary,
        )
        self.session.add(artifact)
        self.session.flush()
        return artifact

    def activate_artifact(
        self,
        *,
        forecast_product_name: str,
        forecast_model_artifact_id: str,
        source_cleaned_dataset_version_id: str,
        training_window_start: datetime,
        training_window_end: datetime,
        updated_by_run_id: str,
        geography_scope: str,
    ) -> CurrentForecastModelMarker:
        prior_artifacts = self.session.scalars(
            select(ForecastModelArtifact).where(
                ForecastModelArtifact.is_current.is_(True),
                ForecastModelArtifact.forecast_product_name == forecast_product_name,
            )
        ).all()
        for artifact in prior_artifacts:
            artifact.is_current = False

        artifact = self._require_artifact(forecast_model_artifact_id)
        artifact.is_current = True
        artifact.activated_at = datetime.utcnow()

        marker = self.session.get(CurrentForecastModelMarker, forecast_product_name)
        if marker is None:
            marker = CurrentForecastModelMarker(
                forecast_product_name=forecast_product_name,
                forecast_model_artifact_id=forecast_model_artifact_id,
                source_cleaned_dataset_version_id=source_cleaned_dataset_version_id,
                training_window_start=training_window_start,
                training_window_end=training_window_end,
                updated_by_run_id=updated_by_run_id,
                geography_scope=geography_scope,
            )
            self.session.add(marker)
        else:
            marker.forecast_model_artifact_id = forecast_model_artifact_id
            marker.source_cleaned_dataset_version_id = source_cleaned_dataset_version_id
            marker.training_window_start = training_window_start
            marker.training_window_end = training_window_end
            marker.updated_at = datetime.utcnow()
            marker.updated_by_run_id = updated_by_run_id
            marker.geography_scope = geography_scope
        self.session.flush()
        return marker

    def finalize_trained(
        self,
        forecast_model_run_id: str,
        *,
        forecast_model_artifact_id: str,
        geography_scope: str,
        summary: str,
    ) -> ForecastModelRun:
        run = self._require_run(forecast_model_run_id)
        run.status = "success"
        run.result_type = "trained_new"
        run.forecast_model_artifact_id = forecast_model_artifact_id
        run.geography_scope = geography_scope
        run.summary = summary
        run.completed_at = datetime.utcnow()
        self.session.flush()
        return run

    def finalize_failed(
        self,
        forecast_model_run_id: str,
        *,
        result_type: str,
        failure_reason: str,
        summary: str,
    ) -> ForecastModelRun:
        run = self._require_run(forecast_model_run_id)
        run.status = "failed"
        run.result_type = result_type
        run.failure_reason = failure_reason
        run.summary = summary
        run.completed_at = datetime.utcnow()
        self.session.flush()
        return run

    def get_current_marker(self, forecast_product_name: str) -> CurrentForecastModelMarker | None:
        return self.session.get(CurrentForecastModelMarker, forecast_product_name)

    def get_artifact(self, forecast_model_artifact_id: str) -> ForecastModelArtifact | None:
        return self.session.get(ForecastModelArtifact, forecast_model_artifact_id)

    def find_current_model(self, forecast_product_name: str) -> ForecastModelArtifact | None:
        marker = self.get_current_marker(forecast_product_name)
        if marker is None:
            return None
        artifact = self.get_artifact(marker.forecast_model_artifact_id)
        if artifact is None:
            return None
        if artifact.forecast_product_name != forecast_product_name:
            return None
        return artifact if artifact.storage_status == "stored" else None

    def _require_run(self, forecast_model_run_id: str) -> ForecastModelRun:
        run = self.get_run(forecast_model_run_id)
        if run is None:
            raise ValueError("Forecast model run not found")
        return run

    def _require_artifact(self, forecast_model_artifact_id: str) -> ForecastModelArtifact:
        artifact = self.get_artifact(forecast_model_artifact_id)
        if artifact is None:
            raise ValueError("Forecast model artifact not found")
        return artifact
