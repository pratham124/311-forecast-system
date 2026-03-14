# Implementation Plan: Configure Alert Thresholds and Notification Channels

**Branch**: `013-uc-13-configure-alert-thresholds` | **Date**: 2026-03-13 | **Spec**: [spec.md](/Users/sahmed/Documents/311-forecast-system/specs/013-uc-13-configure-alert-thresholds/spec.md)
**Input**: Feature specification from `/specs/013-uc-13-configure-alert-thresholds/spec.md`

## Summary

Implement UC-13 as an authenticated shared-configuration workflow that lets authorized operational managers load the one active alert configuration, edit threshold rules by service category and optional geography, select one or more supported delivery channels, define scoped frequency and deduplication controls, and save a new active configuration version only after validation succeeds. The design keeps configuration retrieval and save orchestration in dedicated backend services, persists one immutable configuration snapshot per successful save plus one structured update-attempt record per save request, and exposes a minimal typed API for loading the active configuration and replacing it safely without disrupting the currently active alert behavior on validation or storage failure.

## Technical Context

**Language/Version**: Python 3.11 backend services and TypeScript React frontend  
**Primary Dependencies**: FastAPI, Pydantic-style typed schemas, SQLAlchemy-compatible PostgreSQL access layer, structured logging, React, TypeScript, Tailwind CSS, shared typed API or domain models, JWT authentication, role-based authorization dependencies  
**Storage**: PostgreSQL for reused UC-01 through UC-12 lineage plus `AlertConfigurationVersion`, `ActiveAlertConfigurationMarker`, `AlertConfigurationThresholdRule`, `AlertConfigurationChannelSelection`, `AlertConfigurationDeliveryPreference`, and `AlertConfigurationUpdateAttempt` persistence  
**Testing**: pytest for backend unit, integration, and contract coverage, frontend interaction tests for load, edit, validation, success, and storage-failure states, and acceptance tests aligned to [UC-13-AT.md](/Users/sahmed/Documents/311-forecast-system/docs/UC-13-AT.md)  
**Target Platform**: Linux-hosted web application with FastAPI backend and React frontend  
**Project Type**: Web application with backend API plus typed frontend  
**Performance Goals**: Return the active configuration quickly enough for interactive settings use and complete valid save requests in one synchronous request while preserving atomic activation of the new configuration version  
**Constraints**: Exactly one shared active configuration governs the alerting system at a time; at least one supported notification channel is required for every saved configuration version; threshold, frequency, and deduplication rules are scoped by service category with optional geography; category-only and category-plus-geography rules must remain distinguishable; validation or storage failure must leave the previous active configuration unchanged; supported channel availability is supplied by an upstream platform capability rather than authored locally in UC-13  
**Scale/Scope**: Operational-manager configuration of the shared threshold-alert behavior consumed by existing alerting workflows, with future downstream alert evaluations reading the current active configuration rather than per-user preferences

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- `PASS`: Use-case traceability is preserved. The plan remains bounded to [UC-13.md](/Users/sahmed/Documents/311-forecast-system/docs/UC-13.md), [UC-13-AT.md](/Users/sahmed/Documents/311-forecast-system/docs/UC-13-AT.md), and the accepted clarifications captured in the feature spec.
- `PASS`: Canonical lineage reuse is preserved. UC-13 reuses upstream alerting and notification lineage from UC-10 through UC-12 and adds only shared-configuration persistence needed to author future alert behavior.
- `PASS`: Layered backend architecture is preserved. Route handlers remain thin; configuration loading, validation, version creation, activation, and update-attempt logging live in dedicated services and repositories; frontend rendering remains a consumer of typed backend payloads.
- `PASS`: Typed contract coverage is preserved. The API contract uses one canonical save-outcome vocabulary and one canonical delivery-scope vocabulary across load and save operations.
- `PASS`: Security coverage is preserved. Configuration endpoints remain authenticated and role-aware, consistent with the constitution and the operational-manager access required by the use case.
- `PASS`: Operational safety is preserved. Validation rejection, storage failure, successful activation, and active-configuration continuity are all first-class observable outcomes rather than log-only side effects.
- `PASS`: No constitution waiver is required. The design stays within the required Python/FastAPI/PostgreSQL backend and React TypeScript frontend architecture.

## Phase 0 Research Decisions

- Use one shared active configuration for the entire alerting system instead of per-manager saved preferences.
- Persist one immutable configuration snapshot per successful save and switch the active pointer atomically on activation.
- Record every save attempt separately so validation rejection and storage failure remain reviewable without promoting invalid drafts to active state.
- Validate selected channels against a supported-channel capability view supplied by the platform at save time.
- Keep scoped frequency and deduplication controls in one UC-13 delivery-preference record keyed by service category and optional geography.
- Keep downstream alert evaluation flows in UC-10 and UC-11 as consumers of the active configuration rather than duplicating alert-authoring state in those use cases.

## Project Structure

### Documentation (this feature)

```text
specs/013-uc-13-configure-alert-thresholds/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── alert-configuration-api.yaml
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
│   ├── pipelines/
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

**Structure Decision**: Use the existing FastAPI backend and React frontend split. Alert-configuration loading and save orchestration belong in backend services and repositories rather than in scheduled pipelines, because UC-13 is an interactive settings flow. Downstream alert-evaluation consumers that read the active configuration remain in dedicated pipeline modules to preserve constitution-required pipeline isolation. Frontend work stays limited to authenticated configuration viewing, editing, validation display, and save-result handling through typed backend APIs.

## Phase 1 Design

### Data Model Direction

- Reuse shared lineage and vocabularies from UC-01 through UC-12 without redefining those entities in UC-13.
- `AlertConfigurationVersion` stores one immutable saved configuration snapshot and carries lifecycle state needed for active-versus-superseded tracking.
- `ActiveAlertConfigurationMarker` points to exactly one current configuration version for the whole alerting system.
- `AlertConfigurationThresholdRule` stores threshold values by service category and optional geography within a saved configuration version.
- `AlertConfigurationChannelSelection` stores the supported channels selected for one saved configuration version.
- `AlertConfigurationDeliveryPreference` stores frequency and deduplication controls by service category and optional geography within a saved configuration version.
- `AlertConfigurationUpdateAttempt` records one authorized save attempt and whether it ended in validation rejection, stored successfully, or storage failure.

### Service Direction

- `AlertConfigurationQueryService` loads the active marker, expands the active configuration version into one frontend-ready read model, and resolves the currently supported channel options supplied by the platform.
- `AlertConfigurationCommandService` owns validation, immutable configuration-version creation, atomic active-marker replacement, and update-attempt persistence for each save request.
- Scoped validation helpers enforce threshold range rules, category-versus-category-plus-geography distinctness, at-least-one-channel selection, and frequency or deduplication policy checks before any new version is activated.

### API Contract Direction

- `GET /api/v1/alert-configurations/active` returns the single active alert configuration with threshold rules, selected channels, scoped delivery preferences, and supported channel options.
- `PUT /api/v1/alert-configurations/active` validates and replaces the active configuration in one authenticated request.
- Successful saves return the new active configuration version identifier and a `stored_successfully` outcome.
- Validation rejection returns field-level issues and leaves the previous active configuration unchanged.
- Storage failure returns an explicit save-failure response and leaves the previous active configuration unchanged.
- All endpoints require authenticated operational-manager access with backend authorization checks; there is no anonymous or public configuration surface.

### Implementation Notes

- The frontend draft state is client-side only until the save request passes backend validation and the new immutable configuration version is persisted.
- Category-only and category-plus-geography scope are distinct and must be represented explicitly in both threshold rules and delivery preferences so later alert evaluation can select the correct scope.
- Supported notification channels are not authored in UC-13. The backend reads them from the platform capability layer at load and save time, and save validation must reject channels that are unsupported or unavailable at that moment.
- A successful save creates a new configuration version and moves the active marker to it in the same transaction; the prior version becomes superseded but remains retained for auditability.
- Validation rejection must not create a new configuration version. Storage failure may create an update-attempt record but must not move the active marker.
- Future alert evaluation flows read only the current active configuration marker and must not infer alert behavior from stale draft content or failed save attempts.

## Post-Design Constitution Check

- `PASS`: Design artifacts preserve UC-13 and UC-13-AT traceability and keep the one-shared-active-configuration, required-channel, and scoped frequency or deduplication constraints explicit.
- `PASS`: Alert configuration remains downstream of the canonical alerting and notification lineage already defined in UC-10 through UC-12 and does not duplicate shared upstream entities.
- `PASS`: Route handlers are limited to typed API concerns; configuration load, validation, version activation, and save-attempt observability remain isolated in service and repository layers.
- `PASS`: The design covers authentication, role-aware access, stable contract vocabulary, and explicit operational logging required by the constitution.
- `PASS`: Operational safety is preserved because validation rejection and storage failure both keep the previous active configuration in force while leaving traceable update-attempt records.

## Complexity Tracking

No constitution violations or complexity exemptions are required.
