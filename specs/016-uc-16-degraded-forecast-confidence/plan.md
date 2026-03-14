# Implementation Plan: Indicate Degraded Forecast Confidence in UI

**Branch**: `016-uc-16-degraded-forecast-confidence` | **Date**: 2026-03-13 | **Spec**: [spec.md](/Users/sahmed/Documents/311-forecast-system/specs/016-uc-16-degraded-forecast-confidence/spec.md)
**Input**: Feature specification from `/specs/016-uc-16-degraded-forecast-confidence/spec.md`

## Summary

Implement UC-16 as an authenticated forecast-visualization extension that reuses the existing forecast view, resolves available confidence and quality signals for the same scope, applies one centrally managed degraded-confidence rule set, prepares a clear warning state only when degradation is confirmed, preserves normal forecast display when signals are missing or dismissed as non-material, and records one correlated trail for retrieval, assessment, rendering, and final display outcomes.

## Technical Context

**Language/Version**: Python 3.11 backend services and TypeScript React frontend  
**Primary Dependencies**: FastAPI, Pydantic-style typed schemas, SQLAlchemy-compatible PostgreSQL access layer, structured logging, React, TypeScript, Tailwind CSS, shared typed API or domain models, JWT authentication, role-based authorization dependencies  
**Storage**: PostgreSQL for reused UC-01 through UC-15 lineage plus UC-16 request observability, confidence-signal resolution outcomes, prepared confidence-display views, and final render-event reporting  
**Testing**: pytest for backend unit, integration, and contract coverage, frontend interaction tests for degraded, normal, missing-signal, dismissed, and render-failure states, and acceptance tests aligned to [UC-16-AT.md](/Users/sahmed/Documents/311-forecast-system/docs/UC-16-AT.md)  
**Target Platform**: Linux-hosted web application with FastAPI backend and React frontend  
**Project Type**: Web application with backend API plus typed frontend  
**Performance Goals**: Resolve confidence status within the same interactive forecast-view load path, return one normalized confidence-display payload per request, and preserve a terminal observable outcome for 100% of degraded, missing-signal, dismissed, normal, and render-failure flows  
**Constraints**: Only authenticated and authorized operational managers may access confidence-display data; degraded-confidence warnings may be shown only when supported by retrieved and validated signals; one centrally managed degradation rule set must apply consistently across supported scopes; forecast access must remain available when indicator rendering fails or confidence signals are unavailable; shared forecast, evaluation, weather, alert, and visualization entities from UC-01 through UC-15 must be reused rather than redefined  
**Scale/Scope**: Operational-manager forecast views already delivered by the platform, extended with confidence-status evaluation and display semantics rather than a second forecast-serving surface

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- `PASS`: Use-case traceability is preserved. The plan remains bounded to [UC-16.md](/Users/sahmed/Documents/311-forecast-system/docs/UC-16.md), [UC-16-AT.md](/Users/sahmed/Documents/311-forecast-system/docs/UC-16-AT.md), and the current UC-16 spec.
- `PASS`: Canonical lineage reuse is preserved. UC-16 extends forecast visualization and observability behavior defined across UC-01 through UC-15 without redefining shared upstream entities.
- `PASS`: Layered backend architecture is preserved. Route handlers remain thin; forecast-context loading, confidence-signal retrieval, degraded-confidence validation, response preparation, and persistence remain in services and repositories.
- `PASS`: Typed contract coverage is preserved. The API contract exposes one canonical vocabulary for confidence assessment state, indicator state, reason category, and render outcome.
- `PASS`: Security coverage is preserved. Confidence-display endpoints remain authenticated and role-aware, and no client infers privileged confidence state outside backend authorization.
- `PASS`: Operational safety is preserved. Missing signals, dismissed signals, and render failures remain explicit persisted outcomes rather than silent UI-only behavior.
- `PASS`: No constitution waiver is required. The design stays within the required Python/FastAPI/PostgreSQL backend and React TypeScript frontend architecture.

## Phase 0 Research Decisions

- Reuse the existing UC-05 forecast visualization retrieval flow rather than introducing a separate forecast-confidence page or duplicate forecast payload.
- Persist one request-scoped confidence-display load record so signal retrieval, assessment, response preparation, and render outcomes share one correlation anchor.
- Apply one centrally managed degraded-confidence rule set to all supported forecast scopes; scope-specific overrides remain out of scope unless approved by a later use case.
- Treat missing confidence signals and dismissed non-material signals as separate explicit terminal outcomes so the UI can stay normal without implying those cases are equivalent.
- Report final client render outcomes separately from backend preparation so indicator-render failures are observable even when the forecast response was otherwise prepared correctly.
- Keep UC-16 limited to confidence communication and traceability; upstream production of forecasts, anomalies, quality flags, or weather-driven adjustments remains owned by earlier use cases.

## Project Structure

### Documentation (this feature)

```text
specs/016-uc-16-degraded-forecast-confidence/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── degraded-forecast-confidence-api.yaml
└── spec.md
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   ├── services/
│   ├── repositories/
│   ├── models/
│   ├── clients/
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

**Structure Decision**: Use the existing FastAPI backend and React frontend split. Confidence evaluation belongs in backend services because it combines protected forecast context, quality signals, and centrally managed materiality rules. The frontend remains a typed consumer of the normalized confidence-display payload and reports the final render outcome through a separate authenticated endpoint.

## Phase 1 Design

### Data Model Direction

- Reuse UC-01 through UC-15 entities and vocabularies without redefining them in UC-16, especially forecast lineage from UC-03 and UC-04, visualization conventions from UC-05, evaluation and anomaly lineage from UC-06 through UC-09, authenticated alert and observability patterns from UC-10 through UC-14, and weather or storm-mode quality context from UC-09 and UC-15 where confidence reasons reference those upstream signals.
- `ForecastConfidenceRequest` records one operational-manager attempt to load confidence status for a forecast visualization scope.
- `ForecastConfidenceSignalResolution` records which confidence or quality signals were resolved, whether they were missing, and whether any candidate degradation reason was dismissed as non-material.
- `ForecastConfidenceAssessmentResult` stores the prepared normalized confidence-display result for one request, including the indicator state the UI should use.
- `ForecastConfidenceRenderEvent` records the final client render outcome so indicator-render failures remain traceable without mutating the prepared result.

### Service Direction

- `ForecastConfidenceQueryService` resolves the requested forecast scope, loads the forecast context required for display, and requests associated confidence or quality signals from reused upstream sources.
- `ForecastConfidenceRuleService` applies the centrally managed degraded-confidence and materiality rules, derives one assessment state, and normalizes supported reason categories such as missing inputs, shock, and anomaly.
- `ForecastConfidencePresentationService` prepares one typed response that distinguishes degraded, normal, missing-signal, dismissed, and preparation-failure semantics without blocking forecast access.
- `ForecastConfidenceObservabilityService` records request lifecycle, signal-resolution status, assessment outcomes, and final render outcomes under one correlation context.

### API Contract Direction

- `GET /api/v1/forecast-views/confidence-status` returns one normalized confidence-display view for the requested forecast scope and selected forecast view context.
- `POST /api/v1/forecast-views/confidence-status/{forecastConfidenceRequestId}/render-events` records whether the client rendered the degraded-confidence indicator successfully or failed during rendering.
- Successful retrieval returns a typed response that can represent `degraded_confirmed`, `normal`, `signals_missing`, `dismissed`, or `error` states through one canonical assessment and indicator vocabulary.
- Missing or invalid scope parameters return typed validation errors rather than inferred default confidence state.
- All endpoints require authenticated operational-manager access with backend authorization checks; there is no anonymous confidence-status surface.

### Implementation Notes

- UC-16 must remain downstream of the existing forecast view. It augments the forecast display with confidence semantics but does not become a new source of forecast values.
- Confidence or quality signals may come from multiple upstream features, but UC-16 must normalize them into one canonical reason-category vocabulary before assessment and response generation.
- A degraded-confidence warning may appear only when retrieved signals and centralized rules confirm material degradation for the same scope and window shown in the forecast view.
- When signals are missing, UC-16 must record that explicit outcome and return a normal forecast-display state without implying confidence is healthy.
- When a candidate degradation signal is dismissed after validation, the response must remain normal while preserving the dismissed reason in observability records.
- A render-failure report must not change the already prepared assessment result from degraded to non-degraded; it augments observability by recording that the prepared indicator was not successfully shown.
- Reason categories shown to users should remain generic and explanatory, such as missing inputs, shock, or anomaly, instead of exposing internal raw rule or model details.

## Post-Design Constitution Check

- `PASS`: Design artifacts preserve UC-16 and UC-16-AT traceability and keep confirmed degradation, missing signals, dismissed signals, and render failures concrete.
- `PASS`: Confidence-display behavior remains downstream of canonical forecast, evaluation, visualization, and weather lineage from UC-01 through UC-15 and does not duplicate shared source-of-truth entities.
- `PASS`: Route handlers are limited to typed API concerns; scope resolution, signal normalization, rule evaluation, response preparation, and observability remain isolated in service and repository layers.
- `PASS`: The design covers authenticated access, stable contract vocabulary, additive persistence, and explicit render-failure observability required by the constitution and the spec.
- `PASS`: Operational safety is preserved because misleading warnings are prevented by explicit missing-signal and dismissed-signal outcomes, and forecast access remains available when the indicator cannot be rendered.

## Complexity Tracking

No constitution violations or complexity exemptions are required.
