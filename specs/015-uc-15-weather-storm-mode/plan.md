# Implementation Plan: Storm Mode Forecast Adjustments

**Branch**: `015-uc-15-weather-storm-mode` | **Date**: 2026-03-13 | **Spec**: [spec.md](/Users/sahmed/Documents/311-forecast-system/specs/015-uc-15-weather-storm-mode/spec.md)
**Input**: Feature specification from `/specs/015-uc-15-weather-storm-mode/spec.md`

## Summary

Implement UC-15 as a backend-driven storm-mode decisioning flow that monitors approved weather signals, validates scope-limited storm triggers, activates storm mode only for the affected category, optional geography, and time window, widens forecast uncertainty for that same scope, applies more sensitive alert parameters only where business rules allow, reuses the existing alert-notification workflow for delivery, and preserves one correlated operational record trail for successful, baseline-fallback, adjustment-failure, and notification-failure outcomes.

## Technical Context

**Language/Version**: Python 3.11 backend services and TypeScript React frontend  
**Primary Dependencies**: FastAPI, Pydantic-style typed schemas, SQLAlchemy-compatible PostgreSQL access layer, APScheduler-compatible scheduling, structured logging, LightGBM forecast services, Government of Canada MSC GeoMet or equivalent approved weather ingestion modules, JWT authentication, role-based authorization dependencies  
**Storage**: PostgreSQL for reused UC-01 through UC-14 lineage plus storm-mode evaluation runs, trigger assessments, activation records, forecast-adjustment outcomes, and alert-evaluation diagnostics; existing shared alert-notification records remain the source of truth for delivery status  
**Testing**: pytest for backend unit, integration, and contract coverage; frontend or operational diagnostic tests for active-state inspection where applicable; acceptance tests aligned to [UC-15-AT.md](/Users/sahmed/Documents/311-forecast-system/docs/UC-15-AT.md)  
**Target Platform**: Linux-hosted web application with FastAPI backend and React frontend  
**Project Type**: Web application with backend API plus typed frontend  
**Performance Goals**: Complete storm-mode trigger validation, activation, and downstream adjustment selection before the dependent forecast-refresh and alert-evaluation cycle for the same scope proceeds, and persist a terminal diagnostic outcome for 100% of monitored storm-mode evaluations  
**Constraints**: Storm mode activates only for validated scopes; weather unavailability and rejected triggers must fall back to baseline behavior; forecast-adjustment failure must revert both uncertainty and alert sensitivity to baseline for the same scope; existing notification-service delivery records remain canonical; effective uncertainty and alert-sensitivity parameters must be inspectable through persisted records or authenticated diagnostics; no storm-mode behavior may leak into unaffected scopes  
**Scale/Scope**: Edmonton 311 forecast and alert scopes already governed by UC-01 through UC-14, extended with weather-aware storm-mode decisioning and diagnostics rather than a second forecasting or notification system

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- `PASS`: Use-case traceability is preserved. The plan remains bounded to [UC-15.md](/Users/sahmed/Documents/311-forecast-system/docs/UC-15.md), [UC-15-AT.md](/Users/sahmed/Documents/311-forecast-system/docs/UC-15-AT.md), and the current UC-15 spec.
- `PASS`: Canonical lineage reuse is preserved. UC-15 extends the existing forecast, weather, alert, notification, and observability lineage from UC-01 through UC-14 instead of redefining shared entities.
- `PASS`: Layered backend architecture is preserved. Route handlers remain thin; weather monitoring, trigger validation, scope activation, forecast-adjustment selection, alert-sensitivity selection, and persistence remain in backend services, pipelines, and repositories.
- `PASS`: Typed contract coverage is preserved. The API contract exposes one canonical storm-mode vocabulary for trigger, activation, forecast-adjustment, and alert-evaluation diagnostics.
- `PASS`: Security coverage is preserved. Storm-mode diagnostic endpoints remain authenticated and role-aware, and no client bypasses backend authorization.
- `PASS`: Operational safety is preserved. Weather unavailability, rejected triggers, adjustment failure, notification retry state, and baseline reversion remain explicit persisted outcomes rather than log-only side effects.
- `PASS`: No constitution waiver is required. The design stays within the required Python/FastAPI/PostgreSQL backend and React TypeScript frontend architecture.

## Phase 0 Research Decisions

- Reuse approved weather retrieval rules from UC-09 instead of creating a second location-mapping or provider-selection policy for storm mode.
- Persist one `StormModeEvaluationRun` per monitoring cycle or equivalent decisioning pass so monitoring, validation, activation, adjustment, and notification outcomes share one correlation anchor.
- Keep storm-mode activation scope-limited to service category, optional geography, and effective time window; there is no system-wide storm-mode switch.
- Reuse existing alert-notification persistence from UC-10 and UC-11 for delivery truth, and add UC-15-specific linkage records rather than a duplicate notification-event table.
- Treat forecast-adjustment failure as a forced reversion of both uncertainty and alert sensitivity to baseline behavior for the affected scope, matching the safe-degradation requirement in the spec.
- Expose current activation state and detailed evaluation outcomes through authenticated diagnostic reads so effective uncertainty and alert-sensitivity parameters are inspectable without depending only on raw logs.

## Project Structure

### Documentation (this feature)

```text
specs/015-uc-15-weather-storm-mode/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── storm-mode-api.yaml
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

**Structure Decision**: Use the existing FastAPI backend and React frontend split. Storm-mode monitoring and decision orchestration belong in backend pipeline and service layers, while authenticated diagnostic consumption remains a thin frontend or operational client concern over typed backend APIs.

## Phase 1 Design

### Data Model Direction

- Reuse shared lineage and vocabularies from UC-01 through UC-14 without redefining those entities in UC-15, especially approved demand lineage, retained forecast lineage, weather-retrieval conventions, threshold-alert and surge-alert delivery records, alert-configuration context, and authenticated observability patterns.
- `StormModeEvaluationRun` records one monitoring or replay decision pass and anchors traceability for all downstream UC-15 records.
- `StormModeTriggerAssessment` records whether weather signals for one canonical scope were validated, rejected, unavailable, or absent.
- `StormModeActivation` records the effective storm-mode state and parameter profile for one validated scope and time window.
- `StormModeForecastAdjustment` records whether forecast uncertainty was widened or reverted to baseline for one activation and one reused forecast lineage reference.
- `StormModeAlertEvaluation` records the effective alert-sensitivity parameters, whether a storm-adjusted alert path created a linked shared notification event, and whether delivery remained successful or moved into retry or manual follow-up through the existing notification workflow.

### Pipeline Direction

- `StormModeEvaluationPipeline` owns one full decision pass for weather monitoring, trigger validation, scope activation, forecast-adjustment selection, alert-sensitivity selection, and correlation persistence.
- The pipeline invokes existing forecast and alert services rather than replacing them, and it is the only module responsible for UC-15 end-to-end orchestration.

### Service Direction

- `StormModeTriggerService` normalizes approved weather inputs, detects candidate severe conditions, validates them against storm-mode business rules, and produces scope-limited trigger outcomes.
- `StormModeActivationService` applies validated triggers to category, optional geography, and time-window scopes and persists effective uncertainty and alert-sensitivity parameter profiles.
- `StormModeForecastAdjustmentService` maps one active storm-mode scope onto retained forecast lineage, widens uncertainty parameters when adjustment succeeds, and records baseline reversion when adjustment fails.
- `StormModeAlertSensitivityService` determines whether the evaluated scope qualifies for storm-adjusted sensitivity, executes alert evaluation through existing alert flows, and links the resulting shared notification record when one is created.
- `StormModeObservabilityService` records correlation ids, failure reasons, terminal outcomes, and parameter snapshots needed for diagnosis and acceptance review.

### API Contract Direction

- `GET /api/v1/storm-mode/activations/current` returns the current storm-mode activation view for active or recently reverted scopes, including effective parameter snapshots and scope boundaries.
- `GET /api/v1/storm-mode/evaluations` returns recent storm-mode evaluation runs for operational review.
- `GET /api/v1/storm-mode/evaluations/{stormModeEvaluationRunId}` returns one detailed diagnostic view including trigger assessments, activations, forecast adjustments, alert evaluations, and linked notification-delivery status.
- All diagnostic endpoints require authenticated operational-manager or administrator access; there is no anonymous storm-mode surface.

### Implementation Notes

- Storm-mode validation is singular and deterministic: detection alone is insufficient, and only a validated trigger may produce an `active` activation record.
- When weather data is unavailable, UC-15 records the missing external data condition and keeps downstream uncertainty and alert sensitivity at baseline for the affected scope.
- When a trigger is rejected during validation, no activation record may become `active`, and all downstream evaluation for that scope remains baseline.
- Forecast-adjustment failure is stronger than a partial degradation: it forces the paired alert-sensitivity outcome for that scope back to baseline as well, matching FR-012 and FR-013.
- UC-15 widens uncertainty only for the affected scope and linked retained forecast outputs; it must not mutate unrelated forecast buckets or redefine the shared forecast entities.
- Notification delivery truth remains owned by the reused shared notification records from UC-10 or UC-11. UC-15 stores linkage and delivery snapshots for diagnosis but does not duplicate channel-attempt persistence.
- Effective uncertainty and alert-sensitivity parameters must be persisted in stable fields rather than inferable only from free-form logs so acceptance review can verify storm-mode behavior objectively.

## Post-Design Constitution Check

- `PASS`: Design artifacts preserve UC-15 and UC-15-AT traceability and keep storm trigger validation, scope-limited activation, safe fallback, and notification retry handling concrete.
- `PASS`: Storm mode remains downstream of canonical demand, forecast, weather, alert, and notification lineage from UC-01 through UC-14 and does not duplicate source-of-truth entities.
- `PASS`: Route handlers are limited to typed API concerns; weather monitoring, trigger validation, activation, forecast adjustment, alert evaluation, and observability remain isolated in pipeline, service, and repository layers.
- `PASS`: The design covers authenticated diagnostics, stable contract vocabulary, and explicit operational correlation required by the constitution and the spec.
- `PASS`: Operational safety is preserved because unavailable weather data, rejected triggers, adjustment failure, and notification-delivery follow-up all remain explicit, reviewable outcomes.

## Complexity Tracking

No constitution violations or complexity exemptions are required.
