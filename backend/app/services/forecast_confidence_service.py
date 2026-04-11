from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import logging

from app.core.config import Settings
from app.core.logging import (
    summarize_forecast_confidence_failure,
    summarize_forecast_confidence_success,
    summarize_forecast_confidence_warning,
)
from app.repositories.surge_evaluation_repository import SurgeEvaluationRepository
from app.repositories.surge_state_repository import SurgeStateRepository
from app.schemas.forecast_visualization import ForecastConfidenceRead

_CONFIRMED_SURGE_OUTCOME_SIGNALS = {
    "confirmed": "recent_confirmed_surge",
    "suppressed_active_surge": "recent_suppressed_active_surge",
}
_DEFAULT_LOOKBACK_HOURS = 48
_DEFAULT_NORMAL_MESSAGE = "Forecast confidence is normal for the current selection."
_DEFAULT_SIGNALS_MISSING_MESSAGE = "Forecast confidence could not be fully assessed with the currently available signals."
_DEFAULT_DISMISSED_MESSAGE = "Recent confidence warnings were reviewed and dismissed for the current selection."
_DEFAULT_MISSING_INPUTS_MESSAGE = "Forecast confidence is reduced because some visualization inputs are missing."
_DEFAULT_ANOMALY_MESSAGE = "Forecast confidence is reduced because recent surge conditions were confirmed for the selected service areas."
_DEFAULT_COMBINED_MESSAGE = "Forecast confidence is reduced because some visualization inputs are missing and recent surge conditions were confirmed for the selected service areas."


@dataclass(frozen=True)
class ForecastConfidenceAssessment:
    assessment_status: str
    indicator_state: str
    reason_categories: tuple[str, ...]
    supporting_signals: tuple[str, ...]
    message: str
    signal_resolution_status: str

    def to_schema(self) -> ForecastConfidenceRead:
        return ForecastConfidenceRead(
            assessmentStatus=self.assessment_status,
            indicatorState=self.indicator_state,
            reasonCategories=list(self.reason_categories),
            supportingSignals=list(self.supporting_signals),
            message=self.message,
        )


@dataclass(frozen=True)
class _AnomalySignalAssessment:
    confirmed_signals: tuple[str, ...] = ()
    dismissed_signals: tuple[str, ...] = ()
    missing_signals: tuple[str, ...] = ()


class ForecastConfidenceService:
    def __init__(
        self,
        *,
        surge_state_repository: SurgeStateRepository | None,
        surge_evaluation_repository: SurgeEvaluationRepository | None,
        settings: Settings,
        logger: logging.Logger,
    ) -> None:
        self.surge_state_repository = surge_state_repository
        self.surge_evaluation_repository = surge_evaluation_repository
        self.settings = settings
        self.logger = logger

    def assess_confidence(
        self,
        *,
        visualization_load_id: str,
        forecast_product: str,
        service_categories: list[str] | None,
        degradation_type: str | None,
        now: datetime,
    ) -> ForecastConfidenceAssessment:
        normalized_categories = _normalize_categories(service_categories)
        confirmed_signals: list[str] = []
        reason_categories: list[str] = []
        dismissed_signals: list[str] = []
        missing_signals: list[str] = []

        if degradation_type in {"history_missing", "uncertainty_missing"}:
            confirmed_signals.append(degradation_type)
            reason_categories.append("missing_inputs")

        anomaly_signals = self._evaluate_anomaly_signals(
            visualization_load_id=visualization_load_id,
            forecast_product=forecast_product,
            service_categories=normalized_categories,
            now=now,
        )
        if anomaly_signals.confirmed_signals:
            confirmed_signals.extend(anomaly_signals.confirmed_signals)
            reason_categories.append("anomaly")
        if anomaly_signals.dismissed_signals:
            dismissed_signals.extend(anomaly_signals.dismissed_signals)
        if anomaly_signals.missing_signals:
            missing_signals.extend(anomaly_signals.missing_signals)

        if confirmed_signals:
            assessment = ForecastConfidenceAssessment(
                assessment_status="degraded_confirmed",
                indicator_state="display_required",
                reason_categories=tuple(_dedupe(reason_categories)),
                supporting_signals=tuple(_dedupe(confirmed_signals)),
                message=self._build_degraded_message(reason_categories),
                signal_resolution_status="resolved",
            )
            self.logger.warning(
                "%s",
                summarize_forecast_confidence_warning(
                    "forecast_confidence.assessed",
                    visualization_load_id=visualization_load_id,
                    assessment_status=assessment.assessment_status,
                    reason_categories=list(assessment.reason_categories),
                    supporting_signals=list(assessment.supporting_signals),
                ),
            )
            return assessment

        if missing_signals:
            assessment = build_signals_missing_confidence(
                message=self._signals_missing_message(),
                supporting_signals=_dedupe(missing_signals),
            )
            self.logger.warning(
                "%s",
                summarize_forecast_confidence_warning(
                    "forecast_confidence.signals_missing",
                    visualization_load_id=visualization_load_id,
                    assessment_status=assessment.assessment_status,
                    supporting_signals=list(assessment.supporting_signals),
                ),
            )
            return assessment

        if dismissed_signals:
            assessment = ForecastConfidenceAssessment(
                assessment_status="dismissed",
                indicator_state="not_required",
                reason_categories=("anomaly",),
                supporting_signals=tuple(_dedupe(dismissed_signals)),
                message=self._dismissed_message(),
                signal_resolution_status="dismissed",
            )
            self.logger.info(
                "%s",
                summarize_forecast_confidence_success(
                    "forecast_confidence.dismissed",
                    visualization_load_id=visualization_load_id,
                    assessment_status=assessment.assessment_status,
                    supporting_signals=list(assessment.supporting_signals),
                ),
            )
            return assessment

        assessment = ForecastConfidenceAssessment(
            assessment_status="normal",
            indicator_state="not_required",
            reason_categories=(),
            supporting_signals=(),
            message=self._normal_message(),
            signal_resolution_status="resolved",
        )
        self.logger.info(
            "%s",
            summarize_forecast_confidence_success(
                "forecast_confidence.normal",
                visualization_load_id=visualization_load_id,
                assessment_status=assessment.assessment_status,
            ),
        )
        return assessment

    def _build_degraded_message(self, reason_categories: list[str]) -> str:
        reason_set = set(reason_categories)
        if {"missing_inputs", "anomaly"}.issubset(reason_set):
            return self._combined_message()
        if "missing_inputs" in reason_set:
            return self._missing_inputs_message()
        return self._anomaly_message()

    def _evaluate_anomaly_signals(
        self,
        *,
        visualization_load_id: str,
        forecast_product: str,
        service_categories: list[str],
        now: datetime,
    ) -> _AnomalySignalAssessment:
        if forecast_product != "daily_1_day" or not service_categories:
            return _AnomalySignalAssessment()
        if self.surge_state_repository is None or self.surge_evaluation_repository is None:
            return _AnomalySignalAssessment()

        confirmed_signals: list[str] = []
        dismissed_signals: list[str] = []
        missing_signals: list[str] = []
        window_end = now if now.tzinfo is not None else now.replace(tzinfo=timezone.utc)
        window_start = window_end - timedelta(hours=self._lookback_hours())

        for category in service_categories:
            try:
                state = self.surge_state_repository.get_state(service_category=category, forecast_product="daily")
                if state is not None and state.current_state == "active_surge":
                    confirmed_signals.append("active_surge_state")
                bundles = self.surge_evaluation_repository.list_candidate_bundles_for_window(
                    service_category=category,
                    detected_at_start=window_start,
                    detected_at_end=window_end,
                )
            except Exception as exc:
                self.logger.exception(
                    "%s",
                    summarize_forecast_confidence_failure(
                        "forecast_confidence.signal_resolution_failed",
                        visualization_load_id=visualization_load_id,
                        service_category=category,
                        failure_reason=str(exc),
                    ),
                )
                missing_signals.append("surge_signal_unavailable")
                continue

            for bundle in bundles:
                confirmation = bundle.confirmation
                outcome = confirmation.outcome if confirmation is not None else None
                if outcome in _CONFIRMED_SURGE_OUTCOME_SIGNALS:
                    confirmed_signals.append(_CONFIRMED_SURGE_OUTCOME_SIGNALS[outcome])
                    continue
                if outcome == "filtered":
                    dismissed_signals.append("filtered_surge_candidate")
                    continue
                if _candidate_signal_failed(bundle.candidate.candidate_status) or outcome == "failed":
                    missing_signals.append("surge_signal_unavailable")
                    continue
                if confirmation is not None and confirmation.failure_reason:
                    missing_signals.append("surge_signal_unavailable")

        return _AnomalySignalAssessment(
            confirmed_signals=tuple(_dedupe(confirmed_signals)),
            dismissed_signals=tuple(_dedupe(dismissed_signals)),
            missing_signals=tuple(_dedupe(missing_signals)),
        )

    def _lookback_hours(self) -> int:
        return int(getattr(self.settings, "forecast_confidence_signal_lookback_hours", _DEFAULT_LOOKBACK_HOURS))

    def _normal_message(self) -> str:
        return str(getattr(self.settings, "forecast_confidence_normal_message", _DEFAULT_NORMAL_MESSAGE))

    def _signals_missing_message(self) -> str:
        return str(getattr(self.settings, "forecast_confidence_signals_missing_message", _DEFAULT_SIGNALS_MISSING_MESSAGE))

    def _dismissed_message(self) -> str:
        return str(getattr(self.settings, "forecast_confidence_dismissed_message", _DEFAULT_DISMISSED_MESSAGE))

    def _missing_inputs_message(self) -> str:
        return str(getattr(self.settings, "forecast_confidence_missing_inputs_message", _DEFAULT_MISSING_INPUTS_MESSAGE))

    def _anomaly_message(self) -> str:
        return str(getattr(self.settings, "forecast_confidence_anomaly_message", _DEFAULT_ANOMALY_MESSAGE))

    def _combined_message(self) -> str:
        return str(getattr(self.settings, "forecast_confidence_combined_message", _DEFAULT_COMBINED_MESSAGE))


def build_signals_missing_confidence(
    *,
    message: str,
    supporting_signals: list[str] | None = None,
) -> ForecastConfidenceAssessment:
    return ForecastConfidenceAssessment(
        assessment_status="signals_missing",
        indicator_state="not_required",
        reason_categories=(),
        supporting_signals=tuple(_dedupe(supporting_signals or ["confidence_signal_unavailable"])),
        message=message,
        signal_resolution_status="missing",
    )


def build_fallback_confidence_read() -> ForecastConfidenceRead:
    return build_signals_missing_confidence(
        message="Current forecast confidence could not be refreshed while a fallback snapshot is shown.",
        supporting_signals=["fallback_confidence_unresolved"],
    ).to_schema()


def build_unavailable_confidence_read() -> ForecastConfidenceRead:
    return build_signals_missing_confidence(
        message="Current forecast confidence could not be assessed because forecast data is unavailable.",
        supporting_signals=["forecast_data_unavailable"],
    ).to_schema()


def confidence_signal_resolution_status(assessment_status: str) -> str:
    if assessment_status == "signals_missing":
        return "missing"
    if assessment_status == "dismissed":
        return "dismissed"
    return "resolved"


def _dedupe(values: list[str]) -> list[str]:
    seen: dict[str, None] = {}
    for value in values:
        if value:
            seen[value] = None
    return list(seen.keys())


def _normalize_categories(service_categories: list[str] | None) -> list[str]:
    seen: dict[str, None] = {}
    for category in service_categories or []:
        token = category.strip()
        if token:
            seen[token] = None
    return list(seen.keys())


def _candidate_signal_failed(candidate_status: str | None) -> bool:
    if not candidate_status:
        return False
    return candidate_status.endswith("failed")
