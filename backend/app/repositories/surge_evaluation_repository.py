from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import SurgeCandidate, SurgeConfirmationOutcome, SurgeEvaluationRun


@dataclass
class SurgeCandidateBundle:
    candidate: SurgeCandidate
    confirmation: SurgeConfirmationOutcome | None


@dataclass
class SurgeEvaluationDetailBundle:
    run: SurgeEvaluationRun
    candidates: list[SurgeCandidateBundle]


class SurgeEvaluationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_run(self, surge_evaluation_run_id: str) -> SurgeEvaluationRun | None:
        return self.session.get(SurgeEvaluationRun, surge_evaluation_run_id)

    def create_run(self, *, ingestion_run_id: str, trigger_source: str) -> SurgeEvaluationRun:
        run = SurgeEvaluationRun(
            ingestion_run_id=ingestion_run_id,
            trigger_source=trigger_source,
            status="running",
        )
        self.session.add(run)
        self.session.flush()
        return run

    def create_candidate(self, **kwargs) -> SurgeCandidate:
        candidate = SurgeCandidate(**kwargs)
        self.session.add(candidate)
        self.session.flush()
        return candidate

    def create_confirmation_outcome(self, **kwargs) -> SurgeConfirmationOutcome:
        outcome = SurgeConfirmationOutcome(**kwargs)
        self.session.add(outcome)
        self.session.flush()
        return outcome

    def finalize_run(
        self,
        surge_evaluation_run_id: str,
        *,
        status: str,
        evaluated_scope_count: int,
        candidate_count: int,
        confirmed_count: int,
        notification_created_count: int,
        failure_summary: str | None = None,
    ) -> SurgeEvaluationRun:
        run = self.session.get(SurgeEvaluationRun, surge_evaluation_run_id)
        if run is None:
            raise ValueError("Surge evaluation run not found")
        run.status = status
        run.evaluated_scope_count = evaluated_scope_count
        run.candidate_count = candidate_count
        run.confirmed_count = confirmed_count
        run.notification_created_count = notification_created_count
        run.failure_summary = failure_summary
        run.completed_at = datetime.utcnow()
        self.session.flush()
        return run

    def list_runs(
        self,
        *,
        ingestion_run_id: str | None = None,
        status: str | None = None,
    ) -> list[SurgeEvaluationRun]:
        statement = select(SurgeEvaluationRun).order_by(SurgeEvaluationRun.started_at.desc())
        if ingestion_run_id:
            statement = statement.where(SurgeEvaluationRun.ingestion_run_id == ingestion_run_id)
        if status:
            statement = statement.where(SurgeEvaluationRun.status == status)
        return list(self.session.scalars(statement))

    def get_run_detail(self, surge_evaluation_run_id: str) -> SurgeEvaluationDetailBundle | None:
        run = self.session.get(SurgeEvaluationRun, surge_evaluation_run_id)
        if run is None:
            return None
        candidates = self._list_candidates_for_statement(
            select(SurgeCandidate)
            .where(SurgeCandidate.surge_evaluation_run_id == surge_evaluation_run_id)
            .order_by(SurgeCandidate.detected_at.asc(), SurgeCandidate.service_category.asc())
        )
        return SurgeEvaluationDetailBundle(
            run=run,
            candidates=candidates,
        )

    def get_candidate_bundle(self, surge_candidate_id: str) -> SurgeCandidateBundle | None:
        candidate = self.session.get(SurgeCandidate, surge_candidate_id)
        if candidate is None:
            return None
        confirmation = self.session.scalar(
            select(SurgeConfirmationOutcome).where(SurgeConfirmationOutcome.surge_candidate_id == surge_candidate_id)
        )
        return SurgeCandidateBundle(candidate=candidate, confirmation=confirmation)

    def list_candidate_bundles_for_window(
        self,
        *,
        service_category: str,
        detected_at_start: datetime,
        detected_at_end: datetime,
    ) -> list[SurgeCandidateBundle]:
        return self._list_candidates_for_statement(
            select(SurgeCandidate)
            .where(
                SurgeCandidate.service_category == service_category,
                SurgeCandidate.detected_at >= detected_at_start,
                SurgeCandidate.detected_at <= detected_at_end,
            )
            .order_by(SurgeCandidate.detected_at.asc(), SurgeCandidate.service_category.asc())
        )

    def _list_candidates_for_statement(self, statement) -> list[SurgeCandidateBundle]:
        candidates = list(self.session.scalars(statement))
        if not candidates:
            return []
        confirmations = list(
            self.session.scalars(
                select(SurgeConfirmationOutcome).where(
                    SurgeConfirmationOutcome.surge_candidate_id.in_(
                        [item.surge_candidate_id for item in candidates]
                    )
                )
            )
        )
        confirmation_by_candidate = {item.surge_candidate_id: item for item in confirmations}
        return [
            SurgeCandidateBundle(candidate=item, confirmation=confirmation_by_candidate.get(item.surge_candidate_id))
            for item in candidates
        ]
