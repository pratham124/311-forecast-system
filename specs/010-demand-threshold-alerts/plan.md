# Implementation Plan: Demand Threshold Alerts

**Branch**: `010-demand-threshold-alerts` | **Date**: 2026-03-13 | **Spec**: [spec.md](/root/311-forecast-system/specs/010-demand-threshold-alerts/spec.md)
**Input**: Feature specification from `/specs/010-demand-threshold-alerts/spec.md`

## Summary

Implement UC-10 as a backend-driven threshold alerting flow that evaluates each published daily or weekly forecast bucket against the applicable threshold for its service category, optional geographic region, forecast window type, and forecast window; creates one alert event only when that scope newly crosses above threshold; attempts all configured notification channels for that alert; and preserves reviewable records for delivered, partial-delivery, retry-pending, and manual-review-required outcomes. The design keeps alert-evaluation orchestration in a dedicated pipeline module, with threshold precedence, threshold-state transitions, and delivery aggregation delegated to backend services and repositories, while exposing a minimal typed API for evaluation triggering and alert review.

## Technical Context

**Language/Version**: Python 3.11 backend services and TypeScript React frontend  
**Primary Dependencies**: FastAPI, Pydantic-style typed schemas, SQLAlchemy-compatible PostgreSQL access layer, APScheduler-compatible scheduling, structured logging, JWT authentication, role-based authorization dependencies  
**Storage**: PostgreSQL for threshold configuration, evaluation runs, per-scope evaluation outcomes, threshold state, notification events, and channel-attempt records  
**Testing**: pytest for backend unit/integration/contract coverage, frontend interaction tests for alert review visibility, and acceptance tests aligned to [UC-10-AT.md](/root/311-forecast-system/docs/UC-10-AT.md)  
**Target Platform**: Linux-hosted web application with FastAPI backend and React frontend  
**Project Type**: Web application with backend API plus typed frontend  
**Performance Goals**: Meet `SC-002` by completing successful alert delivery within 5 minutes of the forecast update becoming available for evaluation while keeping threshold evaluation bounded to the published forecast scope being processed  
**Constraints**: No alert for missing thresholds or non-exceedance; category-plus-geography thresholds take precedence over category-only thresholds for the same regional forecast bucket; duplicate alerts stay suppressed until that same scope returns to or below threshold and later exceeds again; all configured channels are attempted for each alert; delivery status must distinguish complete success from partial delivery; and failures must remain reviewable for retry or manual follow-up  
**Scale/Scope**: Edmonton 311 forecast categories with optional supported geography scopes and forecast windows already produced by the governed daily and weekly forecast products

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- `PASS`: Use-case traceability is preserved. The plan remains bounded to [UC-10.md](/root/311-forecast-system/docs/UC-10.md), [UC-10-AT.md](/root/311-forecast-system/docs/UC-10-AT.md), and the current feature spec, including the accepted duplicate-suppression and multi-channel delivery clarifications.
- `PASS`: Canonical Edmonton data and time-safe forecasting are preserved. Alert evaluation consumes the already-governed forecast lineage and does not introduce alternate forecasting or source-data logic.
- `PASS`: Layered backend architecture is preserved. Route handlers remain thin; alert-evaluation orchestration lives in a dedicated pipeline module; threshold selection, precedence, state transitions, delivery aggregation, and persistence remain isolated in backend services, repositories, and notification integration modules.
- `PASS`: Typed contract coverage is preserved. The API contract uses one canonical forecast-window vocabulary and one canonical delivery-status vocabulary across trigger and review endpoints.
- `PASS`: Security coverage is preserved. Trigger and review endpoints remain authenticated and role-aware, consistent with the constitution.
- `PASS`: Operational safety is preserved. Missing thresholds, suppressed duplicates, partial channel failures, and total delivery failures are explicit outcomes; alert review remains available independently of downstream provider health.
- `PASS`: No constitution waiver is required. The design stays within the required Python/FastAPI/PostgreSQL architecture and does not alter upstream forecast lineage or activation rules.

## Phase 0 Research Decisions

- Reuse upstream forecast lineage as the only evaluation input source; threshold alerting does not create a parallel forecast copy.
- Use one canonical evaluation scope: service category, optional geographic region, forecast window type, and forecast window.
- Apply one threshold precedence rule: when both a category-only threshold and a category-plus-geography threshold could match the same regional forecast bucket, evaluate only the category-plus-geography threshold for that regional scope.
- Evaluate daily forecast products using the published daily forecast bucket and forecast window type, and weekly forecast products using the published weekly forecast bucket and forecast window type.
- Use one canonical delivery-status vocabulary for alert events: `delivered`, `partial_delivery`, `retry_pending`, and `manual_review_required`.
- Treat `delivered` as all configured channels succeeded, `partial_delivery` as at least one configured channel succeeded while at least one configured channel failed, `retry_pending` as no channel succeeded and retry remains queued, and `manual_review_required` as no channel succeeded and operator follow-up is required.
- Recalculate threshold eligibility on every evaluation using the currently active threshold settings, including when thresholds change between consecutive evaluations of the same scope.

## Project Structure

### Documentation (this feature)

```text
specs/010-demand-threshold-alerts/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── threshold-alerts-api.yaml
└── tasks.md
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

**Structure Decision**: Use the constitution-mandated FastAPI backend and React frontend split. Alert-evaluation orchestration belongs in `backend/src/pipelines/`; threshold precedence, duplicate suppression, threshold-state reconciliation, and delivery aggregation belong in backend services and repositories; frontend usage is limited to authenticated alert review through typed backend APIs.

## Phase 1 Design

### Data Model Direction

- `ThresholdConfiguration` remains the authoritative business rule and includes category-only and category-plus-geography thresholds by forecast window type.
- `ThresholdEvaluationRun` captures one evaluation pass tied to one published forecast product.
- `ThresholdScopeEvaluation` uses the canonical scope vocabulary: service category, optional geographic region, forecast window type, forecast window, and forecast bucket value.
- `ThresholdScopeEvaluation` records one per-scope outcome vocabulary: `configuration_missing`, `below_or_equal`, `exceeded_alert_created`, `exceeded_suppressed`, or `delivery_failed`.
- `ThresholdState` tracks one evaluated scope at a time using the same canonical scope vocabulary and is recomputed against the currently active threshold configuration on each evaluation.
- `NotificationEvent` represents one threshold-crossing alert event and uses one overall delivery-status vocabulary: `delivered`, `partial_delivery`, `retry_pending`, or `manual_review_required`.
- `NotificationChannelAttempt` records every configured channel attempt so the distinction between all-channel success and partial success remains implementation-safe and reviewable.

### Pipeline Direction

- `ThresholdAlertEvaluationPipeline` owns one full evaluation pass for a published forecast product and coordinates forecast-scope extraction, threshold selection, threshold-state reconciliation, alert creation, and delivery dispatch.
- The pipeline invokes services and repositories but is the only module responsible for end-to-end alert-evaluation orchestration.

### API Contract Direction

- `POST /api/v1/forecast-alerts/evaluations` triggers evaluation for a published forecast reference and returns the accepted evaluation-run identifier.
- `GET /api/v1/forecast-alerts/events` returns alert events for operational review with canonical fields for service category, optional geography, forecast window type, forecast window, forecast bucket value, threshold value, and overall delivery status.
- `GET /api/v1/forecast-alerts/events/{notificationEventId}` returns one alert event with its review details, including failed channel attempts and follow-up reason where applicable.
- Trigger requests require protected backend access suitable for scheduled jobs or internal operational actions; no user-facing trigger flow is required in the frontend. Read endpoints require authenticated operational-manager or administrator access.

### Implementation Notes

- Threshold precedence is singular and deterministic: category-plus-geography overrides category-only for the same regional forecast bucket, and only one threshold may be evaluated for that regional scope in a single run.
- Category-only thresholds still apply to scopes that do not have a matching geography-specific threshold.
- Daily and weekly forecast products are evaluated only against their own published forecast buckets and forecast window types; the alerting flow must not remap one product into the other’s window semantics.
- Threshold-state transitions always use the currently active threshold settings. If threshold settings change between consecutive evaluations of the same scope, the next evaluation reconciles the tracked threshold-state record to the updated threshold configuration before comparing the current forecast bucket value, then either creates a new alert, keeps suppression active, or re-arms the scope accordingly.
- `delivered` means every configured channel attempt succeeded; `partial_delivery` means at least one configured channel succeeded and at least one configured channel failed; `retry_pending` and `manual_review_required` mean no configured channel succeeded.
- Alert review must expose enough information to distinguish complete success, partial delivery, and total failure without requiring operators to infer state from raw channel attempts alone.

## Post-Design Constitution Check

- `PASS`: Design artifacts preserve UC-10 and UC-10-AT traceability and keep the clarified threshold-precedence, duplicate-suppression, and multi-channel delivery rules explicit.
- `PASS`: Forecast alerting remains downstream of the canonical Edmonton forecast pipeline and does not alter time-safe training, inference, or dataset lineage obligations.
- `PASS`: Route handlers are limited to typed API concerns; alert-evaluation orchestration is isolated in the pipeline layer; threshold precedence, threshold-state transitions, and delivery aggregation remain isolated in service and repository layers.
- `PASS`: The design covers authentication, role-aware access, explicit logging, and stable contract vocabulary required by the constitution.
- `PASS`: Operational safety is preserved because alert evaluation and alert review remain traceable even when thresholds change between evaluations or notification providers partially fail.

## Complexity Tracking

No constitution violations or complexity exemptions are required.
