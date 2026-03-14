# Implementation Plan: Submit Feedback or Bug Report

**Branch**: `019-feedback-bug-reporting` | **Date**: 2026-03-14 | **Spec**: [spec.md](/home/asiad/ece493/311-forecast-system/specs/019-feedback-bug-reporting/spec.md)
**Input**: Feature specification from `/specs/019-feedback-bug-reporting/spec.md`

## Summary

Implement UC-19 as a reliable feedback-intake capability that accepts both anonymous and authenticated submissions, requires explicit report typing (`Feedback` or `Bug Report`), validates inputs before acceptance, preserves accepted reports for authorized review, and maintains failure-safe behavior when external issue-tracking integrations are unavailable.

## Technical Context

**Language/Version**: Python 3.11 backend services and TypeScript React frontend  
**Primary Dependencies**: FastAPI, Pydantic-style typed schemas, SQLAlchemy-compatible PostgreSQL access layer, structured logging, React, TypeScript, Tailwind CSS, JWT authentication, role-based authorization dependencies  
**Storage**: PostgreSQL for feedback-submission records, submission status events, and reviewer-facing queue records  
**Testing**: pytest for backend unit/integration/contract coverage plus frontend interaction tests for submission validation and status messaging  
**Target Platform**: Linux-hosted web application with FastAPI backend and React frontend
**Project Type**: Web application (backend API + typed frontend)  
**Performance Goals**: Meet UC-19 measurable outcomes, including outcome-message visibility for at least 95% of valid submissions within 10 seconds  
**Constraints**: Must allow anonymous and authenticated submission, require one report type per submission, avoid silent failure, preserve accepted reports during downstream integration outages, and keep review access restricted to authorized team members  
**Scale/Scope**: Operational-feedback intake for Edmonton 311 forecasting system users with as-needed submission frequency and reviewer-oriented triage access

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- `PASS`: Use-case traceability is explicit to [UC-19.md](/home/asiad/ece493/311-forecast-system/docs/UC-19.md) and [UC-19-AT.md](/home/asiad/ece493/311-forecast-system/docs/UC-19-AT.md), and the feature spec clarifications are incorporated.
- `PASS`: Layered backend architecture is preserved: intake and validation in service modules, persistence in repository modules, and external issue-tracker integration isolated in client modules.
- `PASS`: Typed contracts are preserved through explicit request/response schemas for submission and reviewer retrieval flows.
- `PASS`: Security model is preserved: anonymous intake is allowed, reviewer access is authenticated and role-gated, and sensitive review data is not publicly exposed.
- `PASS`: Operational safety is preserved: accepted reports remain locally retained when external integrations fail; status events and structured logs make failures diagnosable.
- `PASS`: No constitution waiver is required for this feature.

## Phase 0 Research Decisions

- Require explicit report classification (`Feedback` or `Bug Report`) at submission time to improve downstream triage and reporting consistency.
- Permit both anonymous and authenticated submissions, with optional contact details, to maximize report capture while preserving optional follow-up.
- Treat local persistence as the system-of-record for accepted submissions; integration with external issue-tracking is downstream and failure-tolerant.
- Use explicit lifecycle statuses (`accepted`, `deferred_for_retry`, `forwarded`, `forward_failed`) so reviewers can distinguish processing outcomes.
- Keep duplicate-submission handling non-blocking in UC-19 scope (capture duplicates as separate reports) to avoid losing potentially distinct incidents.

## Project Structure

### Documentation (this feature)

```text
specs/019-feedback-bug-reporting/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── feedback-reporting-api.yaml
└── spec.md
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   ├── services/
│   ├── repositories/
│   ├── clients/
│   └── models/
└── tests/

frontend/
├── src/
│   ├── pages/
│   ├── features/
│   ├── components/
│   ├── api/
│   ├── hooks/
│   └── types/
└── tests/

tests/
├── contract/
├── integration/
└── unit/
```

**Structure Decision**: Use the existing web-application split with backend and frontend boundaries. Submission handling, retry/defer semantics, and reviewer retrieval belong to backend services and repositories; frontend consumes typed API contracts for intake and reviewer views.

## Phase 1 Design

### Data Model Direction

- `FeedbackSubmission` is the canonical accepted-report entity with required report type, required description, optional contact details, submitter context (`anonymous` or `authenticated`), and current processing status.
- `SubmissionStatusEvent` records each processing transition (`accepted`, `deferred_for_retry`, `forwarded`, `forward_failed`) with timestamp and reason metadata.
- `ReviewQueueRecord` materializes reviewer-facing triage state for authorized team members, including visibility status and handling progress.
- Accepted submissions are never dropped due to downstream integration failure; they transition to `deferred_for_retry` instead.

### Service Direction

- `FeedbackIntakeService` validates payloads, enforces report-type requirement, creates accepted submissions, and emits immediate user outcome.
- `FeedbackForwardingService` attempts forwarding accepted submissions to the configured issue-tracking destination and records status events.
- `FeedbackRetryService` retries deferred submissions using bounded retry policy and maintains status history.
- `FeedbackReviewService` provides authorized retrieval and filtering capabilities for reviewer workflows.

### API Contract Direction

- `POST /api/v1/feedback-submissions` accepts anonymous or authenticated submission payloads and returns explicit submission outcome.
- `GET /api/v1/feedback-submissions` and `GET /api/v1/feedback-submissions/{feedbackSubmissionId}` are reviewer-only endpoints for list/detail inspection.
- Contracts expose stable vocabularies for `reportType` and `processingStatus` so frontend and acceptance tests share one canonical set.

### Implementation Notes

- Validation failures do not create accepted submissions.
- Every accepted submission receives at least one persisted status event.
- External forwarding failures do not change acceptance status retroactively; they append forwarding-failure state and keep item reviewable.
- Anonymous submissions are allowed and must not require authentication cookies or tokens to be accepted.

## Post-Design Constitution Check

- `PASS`: Design stays traceable to UC-19 and UC-19-AT and maintains explicit acceptance-aligned outcomes.
- `PASS`: Backend layering is preserved with thin routes and service/repository/client isolation.
- `PASS`: Typed API contracts and role-based reviewer access are explicit.
- `PASS`: Operational safety is preserved through retained accepted submissions, explicit status events, and non-silent failure behavior.
- `PASS`: No constitution violations detected after Phase 1 design.

## Complexity Tracking

No constitution violations or complexity exemptions are required.
