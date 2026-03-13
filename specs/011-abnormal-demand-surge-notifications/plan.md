# Implementation Plan: Abnormal Demand Surge Notifications

**Branch**: `011-abnormal-demand-surge-notifications` | **Date**: 2026-03-13 | **Spec**: [spec.md](/Users/sahmed/Documents/311-forecast-system/specs/011-abnormal-demand-surge-notifications/spec.md)
**Input**: Feature specification from `/specs/011-abnormal-demand-surge-notifications/spec.md`

## Summary

Implement UC-11 as an ingestion-triggered surge-detection flow that compares newly ingested actual demand against the active LightGBM P50 forecast on the canonical service-category and optional-geography scope, computes a rolling residual z-score plus percent-above-forecast confirmation check, creates one surge notification only when a scope newly enters confirmed surge state, suppresses duplicate notifications while that scope remains in surge state, and preserves reviewable records for filtered candidates, detector failures, delivered alerts, and retry-or-manual-review follow-up outcomes.

## Technical Context

**Language/Version**: Python 3.11 backend services and TypeScript React frontend  
**Primary Dependencies**: FastAPI, Pydantic-style typed schemas, SQLAlchemy-compatible PostgreSQL access layer, APScheduler-compatible scheduling for existing platform jobs, structured logging, JWT authentication, role-based authorization dependencies  
**Storage**: PostgreSQL for reused UC-01 through UC-10 lineage plus surge-detection configuration, evaluation runs, surge candidates, confirmation outcomes, surge state, surge notification events, and surge channel-attempt records  
**Testing**: pytest for backend unit/integration/contract coverage, frontend interaction tests for surge-evaluation and surge-event review visibility, and acceptance tests aligned to [UC-11-AT.md](/Users/sahmed/Documents/311-forecast-system/docs/UC-11-AT.md)  
**Target Platform**: Linux-hosted web application with FastAPI backend and React frontend  
**Project Type**: Web application with backend API plus typed frontend  
**Performance Goals**: Confirm and persist surge outcomes within 5 minutes of a successful UC-01 ingestion completion while keeping per-run evaluation bounded to the affected service-category and optional-geography scopes  
**Constraints**: Automatic execution starts only after a successful UC-01 ingestion run; no cron-only or streaming-only trigger path; confirmation requires both z-score and percent-above-forecast thresholds; duplicate surge notifications remain suppressed until the same scope returns to normal; surge persistence stays separate from UC-10 threshold-alert tables; and delivery failures must remain reviewable for retry or manual follow-up  
**Scale/Scope**: Edmonton 311 service categories with optional supported geography scopes, using active LightGBM daily forecast lineage produced by UC-03 for surge evaluation while excluding UC-04 weekly forecast products, plus the notification semantics established in UC-10

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- `PASS`: Use-case traceability is preserved. The plan remains bounded to [UC-11.md](/Users/sahmed/Documents/311-forecast-system/docs/UC-11.md), [UC-11-AT.md](/Users/sahmed/Documents/311-forecast-system/docs/UC-11-AT.md), and the accepted clarifications captured in the feature spec.
- `PASS`: Canonical Edmonton lineage is preserved. Surge detection reuses successful UC-01 ingestion outputs plus active LightGBM forecast lineage from UC-03 and UC-04 instead of introducing a second demand-monitoring or forecasting source.
- `PASS`: Layered backend architecture is preserved. Route handlers remain thin; ingestion-triggered orchestration lives in a dedicated surge-evaluation pipeline; residual calculation, rolling-baseline lookup, confirmation, state transitions, and delivery aggregation remain isolated in services and repositories.
- `PASS`: Typed contract coverage is preserved. The API contract uses one canonical trigger-source vocabulary, one confirmation-outcome vocabulary, and one delivery-status vocabulary across replay and review endpoints.
- `PASS`: Security coverage is preserved. Replay and review endpoints remain authenticated and role-aware, consistent with the constitution and UC-10 patterns.
- `PASS`: Operational safety is preserved. Detector failures, filtered candidates, suppressed duplicates, and delivery failures are first-class persisted outcomes rather than log-only side effects.
- `PASS`: No constitution waiver is required. The design stays within the required Python/FastAPI/PostgreSQL architecture and reuses established lineage entities instead of redefining them.

## Phase 0 Research Decisions

- Reuse successful UC-01 ingestion completion as the only automatic trigger for surge detection.
- Compare newly ingested actual demand against the active LightGBM P50 forecast residual instead of training or serving a second anomaly model.
- Confirm surges with one dual-threshold rule: residual z-score above threshold and percent-above-forecast above floor for the same scope and evaluation.
- Evaluate one canonical scope at a time: service category plus optional geography, aligned to the same scope vocabulary used by UC-03, UC-04, and UC-10.
- Persist one surge-state record per scope so notifications fire only on state entry and re-arm only after return-to-normal.
- Keep UC-11 persistence separate from UC-10 threshold-alert tables while reusing the same delivery-status semantics and notification-review expectations.
- Expose a minimal API surface limited to protected manual replay triggering, surge-evaluation review, and confirmed surge-event retrieval; threshold or detector authoring is outside this feature.

## Project Structure

### Documentation (this feature)

```text
specs/011-abnormal-demand-surge-notifications/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── surge-alerts-api.yaml
└── spec.md
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   ├── pipelines/
│   ├── services/
│   ├── repositories/
│   ├── clients/
│   ├── models/
│   └── core/
└── tests/

frontend/
├── src/
│   ├── api/
│   ├── components/
│   ├── features/
│   ├── hooks/
│   ├── pages/
│   ├── types/
│   └── utils/
└── tests/

tests/
├── contract/
├── integration/
└── unit/
```

**Structure Decision**: Use the existing FastAPI backend and React frontend split. Ingestion-triggered surge orchestration belongs in `backend/src/pipelines/`; residual-baseline lookup, candidate creation, confirmation, surge-state reconciliation, and delivery aggregation belong in backend services and repositories; frontend usage is limited to authenticated surge-evaluation and surge-event review through typed backend APIs.

## Phase 1 Design

### Data Model Direction

- Reuse UC-01 ingestion lineage, UC-03 daily forecast lineage, UC-04 weekly lineage context where needed for cross-feature documentation only, and UC-10 delivery vocabulary without redefining those shared entities in UC-11.
- `SurgeDetectionConfiguration` stores the dual-threshold rule and rolling-baseline parameters for one service category and optional geography scope, with evaluation bound to the UC-03 daily forecast product.
- `SurgeEvaluationRun` captures one ingestion-triggered or manual-replay evaluation pass tied to one successful `IngestionRun`.
- `SurgeCandidate` records the residual-based detector output for one evaluated scope, including actual value, forecast value, residual, rolling-baseline context, and candidate status.
- `SurgeConfirmationOutcome` records whether the candidate became `confirmed`, `filtered`, `suppressed_active_surge`, or `failed`.
- `SurgeState` tracks whether a scope is currently in confirmed surge state and whether notification eligibility is armed.
- `SurgeNotificationEvent` represents one confirmed-surge alert event with surge metrics, delivery status, and follow-up metadata.
- `SurgeNotificationChannelAttempt` records every configured channel attempt so complete success, partial delivery, and total failure remain reviewable.

### Pipeline Direction

- `AbnormalDemandSurgeEvaluationPipeline` owns one full evaluation pass after successful ingestion and coordinates demand aggregation, active-forecast lookup, residual calculation, rolling-baseline retrieval, candidate creation, confirmation, state transitions, alert creation, and delivery dispatch.
- The pipeline invokes services and repositories but is the only module responsible for end-to-end surge-evaluation orchestration.

### API Contract Direction

- `POST /api/v1/surge-alerts/evaluations` triggers a protected manual replay for one successful ingestion run, records `trigger_source = manual_replay` server-side, and returns the accepted surge-evaluation-run identifier.
- `GET /api/v1/surge-alerts/evaluations` returns surge evaluation runs for operational review so detector failures and runs with zero notifications remain inspectable.
- `GET /api/v1/surge-alerts/evaluations/{surgeEvaluationRunId}` returns one evaluation run with candidate- and confirmation-level outcomes so confirmed, filtered, suppressed, and failed paths are reviewable even when no notification event exists.
- `GET /api/v1/surge-alerts/events` returns confirmed surge notification events for operational review with canonical scope, surge-magnitude, confirmation-time, and delivery-status fields.
- `GET /api/v1/surge-alerts/events/{surgeNotificationEventId}` returns one surge notification event with candidate metrics, confirmation details, and channel-attempt records.
- Automatic execution on ingestion completion remains the primary trigger path; the trigger endpoint exists for manual replay, acceptance testing, and operational recovery only.

### Implementation Notes

- Residual computation always uses the newly ingested actual demand and the currently active LightGBM P50 forecast for the same canonical scope and comparable time bucket.
- Surge detection selects only the UC-03 daily forecast product (`ForecastVersion` and `ForecastBucket`); UC-04 weekly forecast products are explicitly excluded because ingestion-triggered actuals align to intraday or daily buckets.
- Confirmation is singular and deterministic: both z-score and percent-above-forecast thresholds must pass in the same evaluation before a surge can become confirmed.
- If `forecast_p50_value = 0`, confirmation still remains deterministic: any positive actual demand satisfies the percent-above-forecast floor, zero actual demand does not, and the numeric percent-above-forecast value may remain null in persisted review payloads.
- Configuration matching follows UC-10-style precedence: for the same category and overlapping active window, a geography-specific `SurgeDetectionConfiguration` overrides a category-wide rule, while overlapping peers at the same specificity level are rejected during configuration authoring.
- A flagged candidate that fails either threshold is persisted as filtered and never creates a notification event.
- A confirmed candidate for a scope already marked as `active` in `SurgeState` is persisted as suppressed and does not create a second notification event.
- `SurgeState` re-arms only when a later evaluation for the same scope no longer satisfies both confirmation thresholds.
- Delivery semantics reuse UC-10 vocabulary: `delivered`, `partial_delivery`, `retry_pending`, and `manual_review_required`.
- Alert review must expose enough information to distinguish detector failure, filtered candidate, active-surge suppression, zero-notification evaluation outcomes, and delivery failure without requiring operators to infer state from raw logs.

## Post-Design Constitution Check

- `PASS`: Design artifacts preserve UC-11 and UC-11-AT traceability and keep the accepted residual-based detection, dual-threshold confirmation, ingestion-triggering, and re-arm behavior explicit.
- `PASS`: Surge alerting remains downstream of canonical ingestion and forecast lineage and does not alter UC-01 through UC-04 source-of-truth responsibilities.
- `PASS`: Route handlers are limited to typed API concerns; surge-evaluation orchestration is isolated in the pipeline layer; residual-baseline logic, confirmation, state transitions, and delivery aggregation remain isolated in services and repositories.
- `PASS`: The design covers authentication, role-aware access, explicit logging, and stable contract vocabulary required by the constitution.
- `PASS`: Operational safety is preserved because replay, review, filtered outcomes, and failed deliveries remain traceable even when detector processing or notification providers fail.

## Complexity Tracking

No constitution violations or complexity exemptions are required.
