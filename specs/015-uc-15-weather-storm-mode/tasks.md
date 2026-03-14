# Tasks: Storm Mode Forecast Adjustments

**Input**: Design documents from `/specs/015-uc-15-weather-storm-mode/`
**Prerequisites**: [plan.md](/Users/sahmed/Documents/311-forecast-system/specs/015-uc-15-weather-storm-mode/plan.md), [spec.md](/Users/sahmed/Documents/311-forecast-system/specs/015-uc-15-weather-storm-mode/spec.md), [research.md](/Users/sahmed/Documents/311-forecast-system/specs/015-uc-15-weather-storm-mode/research.md), [data-model.md](/Users/sahmed/Documents/311-forecast-system/specs/015-uc-15-weather-storm-mode/data-model.md), [storm-mode-api.yaml](/Users/sahmed/Documents/311-forecast-system/specs/015-uc-15-weather-storm-mode/contracts/storm-mode-api.yaml), [quickstart.md](/Users/sahmed/Documents/311-forecast-system/specs/015-uc-15-weather-storm-mode/quickstart.md)

**Tests**: Include backend unit, integration, and contract tests plus targeted frontend interaction tests for authenticated storm-mode diagnostics because UC-15 requires validated scope-limited activation, inspectable effective parameters, safe baseline fallback, and traceable notification outcomes.

**Organization**: Tasks are grouped by user story so each story can be implemented and verified independently while preserving one shared storm-mode evaluation, activation, adjustment, alerting, and observability architecture.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel when the task touches different files and does not depend on incomplete work
- **[Story]**: User story mapping for implementation and test traceability
- All task descriptions include exact file paths

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the planned backend, frontend, and test scaffolding for the storm-mode workflow.

- [ ] T001 Create the planned backend, frontend, and test directories in `backend/src/api/routes/`, `backend/src/api/schemas/`, `backend/src/pipelines/`, `backend/src/services/`, `backend/src/repositories/`, `backend/src/models/`, `backend/src/clients/`, `backend/src/core/`, `frontend/src/api/`, `frontend/src/features/storm-mode/components/`, `frontend/src/features/storm-mode/hooks/`, `frontend/src/features/storm-mode/state/`, `frontend/src/pages/`, `frontend/src/types/`, `frontend/tests/`, `tests/contract/`, `tests/integration/`, and `tests/unit/`
- [ ] T002 Create backend Python module scaffolding for storm-mode routing, orchestration, services, repositories, and models in `backend/src/api/routes/storm_mode.py`, `backend/src/api/schemas/storm_mode.py`, `backend/src/pipelines/storm_mode_evaluation_pipeline.py`, `backend/src/services/storm_mode_trigger_service.py`, `backend/src/services/storm_mode_activation_service.py`, `backend/src/services/storm_mode_forecast_adjustment_service.py`, `backend/src/services/storm_mode_alert_sensitivity_service.py`, `backend/src/services/storm_mode_observability_service.py`, `backend/src/services/storm_mode_query_service.py`, `backend/src/repositories/storm_mode_repository.py`, and `backend/src/models/storm_mode.py`
- [ ] T003 [P] Create frontend TypeScript scaffolding for storm-mode diagnostics, API access, and typed state in `frontend/src/api/stormModeApi.ts`, `frontend/src/types/stormMode.ts`, `frontend/src/features/storm-mode/hooks/useStormModeDiagnostics.ts`, `frontend/src/features/storm-mode/state/stormModeDiagnosticsState.ts`, and `frontend/src/pages/StormModeDiagnosticsPage.tsx`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build shared persistence, typed contracts, weather-source reuse, authorization, and observability before story-specific behavior.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T004 Create the UC-15 persistence models and canonical vocabularies for `StormModeEvaluationRun`, `StormModeTriggerAssessment`, `StormModeActivation`, `StormModeForecastAdjustment`, and `StormModeAlertEvaluation` in `backend/src/models/storm_mode.py`
- [ ] T005 [P] Create the initial storm-mode schema migration in `backend/src/models/migrations/015_storm_mode.py`
- [ ] T006 [P] Implement repository methods for evaluation-run persistence, trigger-assessment persistence, activation persistence, forecast-adjustment persistence, alert-evaluation persistence, current-activation lookup, evaluation summary lookup, and evaluation-detail lookup in `backend/src/repositories/storm_mode_repository.py`
- [ ] T007 [P] Define typed request and response schemas for current activation retrieval, evaluation list retrieval, and evaluation detail retrieval in `backend/src/api/schemas/storm_mode.py`
- [ ] T008 [P] Implement authenticated and role-aware route dependencies for storm-mode endpoints in `backend/src/core/auth.py` and `backend/src/api/routes/storm_mode.py`
- [ ] T009 [P] Implement approved weather-provider and geography-alignment client helpers reused from UC-09 in `backend/src/clients/weather_monitoring_client.py` and `backend/src/clients/weather_scope_alignment_client.py`
- [ ] T010 [P] Implement shared forecast-lineage and alert-notification linkage helpers for UC-03 through UC-11 reuse in `backend/src/clients/forecast_lineage_client.py` and `backend/src/clients/alert_notification_client.py`
- [ ] T011 [P] Implement structured logging helpers for monitoring start, trigger detection, validation outcomes, activation state changes, forecast-adjustment outcomes, alert-evaluation outcomes, and notification linkage outcomes in `backend/src/core/logging.py`
- [ ] T012 [P] Create frontend typed contracts and API client support for authenticated `GET /api/v1/storm-mode/activations/current`, `GET /api/v1/storm-mode/evaluations`, and `GET /api/v1/storm-mode/evaluations/{stormModeEvaluationRunId}` in `frontend/src/types/stormMode.ts` and `frontend/src/api/stormModeApi.ts`
- [ ] T013 Implement shared scope-normalization, time-window derivation, and parameter-profile helpers in `backend/src/services/storm_mode_trigger_service.py`, `backend/src/services/storm_mode_activation_service.py`, and `backend/src/services/storm_mode_alert_sensitivity_service.py`
- [ ] T014 Implement the shared observability service for correlation-id propagation, terminal outcome updates, and effective-parameter snapshot persistence in `backend/src/services/storm_mode_observability_service.py`
- [ ] T015 Implement the shared storm-mode query service for current activation views, evaluation summaries, and detailed evaluation assembly in `backend/src/services/storm_mode_query_service.py`

**Checkpoint**: Shared persistence, authorization, external-source reuse, observability, and typed contracts are ready. User story implementation can begin.

---

## Phase 3: User Story 1 - Receive more cautious forecasts and more sensitive alerts during storm conditions (Priority: P1) 🎯 MVP

**Goal**: Detect and validate storm triggers for the affected scope, activate storm mode only for that scope, widen forecast uncertainty, apply more sensitive alert logic where allowed, link notification outcomes, and expose the resulting diagnostic state.

**Independent Test**: Feed approved weather conditions that satisfy storm-mode criteria for one service category and geography, run storm-mode evaluation plus downstream forecast and alert logic, and verify the system activates only that scope, widens uncertainty, applies storm-adjusted sensitivity where applicable, creates the linked alert notification, and returns a fully correlated diagnostic record.

### Tests for User Story 1

- [ ] T016 [P] [US1] Add contract and schema-validation tests for authenticated `GET /api/v1/storm-mode/activations/current`, `GET /api/v1/storm-mode/evaluations`, and `GET /api/v1/storm-mode/evaluations/{stormModeEvaluationRunId}` `200`, `401`, `403`, `404`, and `422` responses in `tests/contract/test_storm_mode_api.py`
- [ ] T017 [P] [US1] Add backend unit tests for storm-trigger detection, validation-rule success, scope-limited activation derivation, uncertainty-profile widening, and storm-adjusted alert-sensitivity selection in `tests/unit/test_storm_mode_services.py`
- [ ] T018 [P] [US1] Add integration tests for validated-trigger persistence, activation creation, forecast-adjustment persistence, alert-evaluation persistence, notification linkage, and correlated success logging in `tests/integration/test_storm_mode_success.py`
- [ ] T019 [P] [US1] Add frontend interaction tests for authenticated activation-list loading, evaluation-history loading, evaluation-detail rendering, and effective-parameter visibility in `frontend/tests/test_storm_mode_success.tsx`

### Implementation for User Story 1

- [ ] T020 [P] [US1] Implement candidate storm detection, validation against approved criteria, and scope-limited trigger-outcome assembly in `backend/src/services/storm_mode_trigger_service.py`
- [ ] T021 [P] [US1] Implement activation-state creation and effective uncertainty plus alert-sensitivity profile persistence for validated scopes in `backend/src/services/storm_mode_activation_service.py` and `backend/src/repositories/storm_mode_repository.py`
- [ ] T022 [P] [US1] Implement retained forecast-lineage lookup and successful storm-mode uncertainty widening in `backend/src/services/storm_mode_forecast_adjustment_service.py`
- [ ] T023 [P] [US1] Implement storm-adjusted alert-sensitivity selection, downstream alert evaluation, and shared notification-event linkage in `backend/src/services/storm_mode_alert_sensitivity_service.py` and `backend/src/clients/alert_notification_client.py`
- [ ] T024 [US1] Implement end-to-end evaluation orchestration for monitoring, validation, activation, forecast adjustment, alert evaluation, and run completion in `backend/src/pipelines/storm_mode_evaluation_pipeline.py`
- [ ] T025 [US1] Implement authenticated storm-mode route handlers for activation and evaluation diagnostics in `backend/src/api/routes/storm_mode.py`
- [ ] T026 [P] [US1] Build the storm-mode diagnostics UI for current activations, recent evaluation summaries, and evaluation detail timelines in `frontend/src/features/storm-mode/components/StormModeActivationList.tsx`, `frontend/src/features/storm-mode/components/StormModeEvaluationList.tsx`, and `frontend/src/features/storm-mode/components/StormModeEvaluationDetail.tsx`
- [ ] T027 [US1] Implement the diagnostics hook, state transitions, and page composition for activation, summary, and detail retrieval in `frontend/src/features/storm-mode/hooks/useStormModeDiagnostics.ts`, `frontend/src/features/storm-mode/state/stormModeDiagnosticsState.ts`, and `frontend/src/pages/StormModeDiagnosticsPage.tsx`

**Checkpoint**: User Story 1 is independently functional and testable.

---

## Phase 4: User Story 2 - Safely fall back to standard logic when storm mode should not apply (Priority: P2)

**Goal**: Keep the system on baseline forecasting and alert behavior when weather data is unavailable, no valid trigger exists, or validation rejects the candidate condition, while making those outcomes explicit and reviewable.

**Independent Test**: Force weather unavailability and false-trigger scenarios for the same supported scope, then verify no activation becomes active, baseline uncertainty and baseline alert sensitivity remain in effect, and the current activation and evaluation diagnostics clearly show the fallback reasons.

### Tests for User Story 2

- [ ] T028 [P] [US2] Add contract tests for current-activation and evaluation-detail fallback payloads covering `weather_unavailable`, `rejected`, and `no_trigger` outcomes in `tests/contract/test_storm_mode_fallback_api.py`
- [ ] T029 [P] [US2] Add backend unit tests for weather-unavailable handling, rejected-trigger handling, no-trigger handling, baseline profile selection, and unaffected-scope protection in `tests/unit/test_storm_mode_fallbacks.py`
- [ ] T030 [P] [US2] Add integration tests for weather-provider failure, rejected-trigger persistence, no-activation fallback, baseline-only alert evaluation, and fallback observability in `tests/integration/test_storm_mode_fallbacks.py`
- [ ] T031 [P] [US2] Add frontend interaction tests for fallback-state messaging, baseline-only parameter display, and filtered diagnostics by scope in `frontend/tests/test_storm_mode_fallbacks.tsx`

### Implementation for User Story 2

- [ ] T032 [US2] Implement weather-unavailable, rejected-trigger, and no-trigger outcome handling with explicit validation reasons and no active activation creation in `backend/src/services/storm_mode_trigger_service.py` and `backend/src/repositories/storm_mode_repository.py`
- [ ] T033 [P] [US2] Implement baseline-only activation and alert-parameter outcomes for unsupported or unaffected scopes in `backend/src/services/storm_mode_activation_service.py` and `backend/src/services/storm_mode_alert_sensitivity_service.py`
- [ ] T034 [US2] Integrate fallback branching and baseline continuation behavior into `backend/src/pipelines/storm_mode_evaluation_pipeline.py`
- [ ] T035 [P] [US2] Build frontend fallback and inactive-state components for weather unavailable, trigger rejected, no trigger, and unaffected-scope views in `frontend/src/features/storm-mode/components/StormModeFallbackState.tsx` and `frontend/src/features/storm-mode/components/StormModeInactiveState.tsx`
- [ ] T036 [US2] Integrate fallback-state rendering and scope filtering into `frontend/src/features/storm-mode/hooks/useStormModeDiagnostics.ts` and `frontend/src/pages/StormModeDiagnosticsPage.tsx`

**Checkpoint**: User Stories 1 and 2 are independently functional and testable.

---

## Phase 5: User Story 3 - Preserve traceability when storm-mode adjustment or notification delivery fails (Priority: P3)

**Goal**: Revert safely to baseline when forecast adjustment fails, preserve retry-eligible notification state when delivery fails, and keep the full storm-mode lifecycle traceable through one run-level correlation context.

**Independent Test**: Force a forecast-adjustment failure and a notification-delivery failure for an otherwise validated storm scenario, then verify uncertainty and alert sensitivity revert to baseline for the affected scope, delivery is not marked successful, retry-eligible status is preserved, and the detailed evaluation diagnostics expose the full failure trail.

### Tests for User Story 3

- [ ] T037 [P] [US3] Add contract tests for detailed evaluation responses that include `adjustment_failed`, `reverted_to_baseline`, and retry-eligible notification-delivery outcomes in `tests/contract/test_storm_mode_failure_api.py`
- [ ] T038 [P] [US3] Add backend unit tests for adjustment-failure reversion, alert-sensitivity rollback, notification retry-state mapping, and run-status failure summarization in `tests/unit/test_storm_mode_failures.py`
- [ ] T039 [P] [US3] Add integration tests for forecast-adjustment failure fallback, notification-delivery failure persistence, retry-eligible linkage, and cross-record correlation in `tests/integration/test_storm_mode_failures.py`
- [ ] T040 [P] [US3] Add frontend interaction tests for reverted-to-baseline activation display, failed-delivery status rendering, and failure-detail inspection in `frontend/tests/test_storm_mode_failures.tsx`

### Implementation for User Story 3

- [ ] T041 [US3] Implement adjustment-failure handling that forces baseline uncertainty and baseline alert sensitivity for the affected scope in `backend/src/services/storm_mode_forecast_adjustment_service.py` and `backend/src/services/storm_mode_activation_service.py`
- [ ] T042 [P] [US3] Implement notification-delivery failure linkage, retry-pending status capture, and manual-review status capture in `backend/src/services/storm_mode_alert_sensitivity_service.py` and `backend/src/clients/alert_notification_client.py`
- [ ] T043 [US3] Implement failure-aware run finalization, baseline-reversion counting, and correlated failure-summary persistence in `backend/src/services/storm_mode_observability_service.py` and `backend/src/repositories/storm_mode_repository.py`
- [ ] T044 [US3] Integrate adjustment-failure rollback and notification-failure continuation behavior into `backend/src/pipelines/storm_mode_evaluation_pipeline.py`
- [ ] T045 [P] [US3] Build frontend failure-state components for reverted activations and failed notification outcomes in `frontend/src/features/storm-mode/components/StormModeRevertedState.tsx` and `frontend/src/features/storm-mode/components/StormModeNotificationFailure.tsx`
- [ ] T046 [US3] Integrate failure-state rendering and correlation-detail display into `frontend/src/features/storm-mode/hooks/useStormModeDiagnostics.ts` and `frontend/src/pages/StormModeDiagnosticsPage.tsx`

**Checkpoint**: All user stories are independently functional and reviewable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finish acceptance traceability, contract alignment, observability assertions, and end-to-end verification for the shared storm-mode workflow.

- [ ] T047 [P] Review `docs/UC-15-AT.md` for acceptance-test alignment and map implementation plus verification steps for AT-01 through AT-12 in `specs/015-uc-15-weather-storm-mode/quickstart.md`
- [ ] T048 [P] Align request and response examples for active, inactive, reverted, fallback, and failure-path diagnostics in `specs/015-uc-15-weather-storm-mode/contracts/storm-mode-api.yaml`
- [ ] T049 [P] Add observability and correlation-id assertions for success, fallback, adjustment-failure, and notification-failure flows in `tests/integration/test_storm_mode_success.py`, `tests/integration/test_storm_mode_fallbacks.py`, and `tests/integration/test_storm_mode_failures.py`
- [ ] T050 Run end-to-end verification for contract, unit, integration, and frontend interaction suites covering storm-mode activation and evaluation diagnostics in `tests/contract/`, `tests/unit/`, `tests/integration/`, and `frontend/tests/`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1: Setup**: No dependencies.
- **Phase 2: Foundational**: Depends on Phase 1 and blocks all user story work.
- **Phase 3: US1**: Depends on Phase 2 only; this is the MVP slice.
- **Phase 4: US2**: Depends on Phase 2 and on the shared evaluation and diagnostic flow established in US1.
- **Phase 5: US3**: Depends on Phase 2 and on the activation, forecast-adjustment, and notification-linkage flow established in US1.
- **Phase 6: Polish**: Depends on the user stories being shipped.

### User Story Dependencies

- **US1 (P1)**: No dependency on other user stories after Foundational.
- **US2 (P2)**: Depends on US1 query and diagnostic behavior, but remains independently testable through fallback and baseline-only scenarios.
- **US3 (P3)**: Depends on US1 activation, adjustment, and notification linkage behavior; it can proceed independently of US2 once the shared evaluation lifecycle exists.

### Within Each User Story

- Contract, unit, integration, and frontend interaction tests should be written before or alongside implementation and must fail before implementation is considered complete.
- Trigger detection and scope validation precede activation persistence.
- Activation and forecast-adjustment behavior precede route finalization for detailed evaluation responses.
- Route and frontend diagnostic tasks depend on the relevant backend services and typed contracts.
- Failure handling depends on the successful evaluation lifecycle being present first.

### Explicit Task Prerequisites

- `T002` depends on `T001`.
- `T003` depends on `T001`.
- `T005` depends on `T004`.
- `T013` depends on `T007`, `T009`, and `T010`.
- `T014` depends on `T004`, `T006`, and `T011`.
- `T015` depends on `T006`, `T007`, and `T014`.
- `T020` depends on `T013`.
- `T021` depends on `T004`, `T006`, and `T020`.
- `T022` depends on `T010`, `T013`, and `T021`.
- `T023` depends on `T010`, `T013`, `T021`, and `T022`.
- `T024` depends on `T006`, `T014`, `T020`, `T021`, `T022`, and `T023`.
- `T025` depends on `T007`, `T008`, and `T015`.
- `T026` depends on `T012`.
- `T027` depends on `T012`, `T025`, and `T026`.
- `T032` depends on `T013` and `T014`.
- `T033` depends on `T013` and `T021`.
- `T034` depends on `T024`, `T032`, and `T033`.
- `T035` depends on `T012`.
- `T036` depends on `T027` and `T035`.
- `T041` depends on `T022` and `T021`.
- `T042` depends on `T023`.
- `T043` depends on `T014`, `T024`, `T041`, and `T042`.
- `T044` depends on `T024`, `T041`, `T042`, and `T043`.
- `T045` depends on `T012`.
- `T046` depends on `T027`, `T045`, and `T044`.
- `T050` depends on `T025`, `T036`, `T044`, and `T046`.

## Parallel Opportunities

- Phase 1: `T003` can run in parallel with `T002` after `T001`.
- Phase 2: `T005` through `T012` can run in parallel after `T004`; `T013`, `T014`, and `T015` begin once the shared persistence, schema, source, and logging scaffolding are ready.
- US1: `T016`, `T017`, `T018`, and `T019` can run in parallel; `T020`, `T021`, `T022`, `T023`, and `T026` can run in parallel once foundational services exist, with `T024` and `T027` following their dependencies.
- US2: `T028`, `T029`, `T030`, and `T031` can run in parallel; `T033` and `T035` can run in parallel after foundational work, then `T032`, `T034`, and `T036` follow in dependency order.
- US3: `T037`, `T038`, `T039`, and `T040` can run in parallel; `T041`, `T042`, and `T045` can run in parallel after the shared evaluation lifecycle is stable, followed by `T043`, `T044`, and `T046`.
- Phase 6: `T047`, `T048`, and `T049` can run in parallel before `T050`.

## Parallel Example: User Story 1

```bash
Task: "Add contract tests for authenticated storm-mode activation and evaluation endpoints in tests/contract/test_storm_mode_api.py"
Task: "Add backend unit tests for trigger validation, activation derivation, and uncertainty widening in tests/unit/test_storm_mode_services.py"
Task: "Add integration tests for validated-trigger persistence and correlated success logging in tests/integration/test_storm_mode_success.py"
Task: "Add frontend interaction tests for storm-mode diagnostics loading and parameter visibility in frontend/tests/test_storm_mode_success.tsx"
```

```bash
Task: "Implement candidate storm detection and validation in backend/src/services/storm_mode_trigger_service.py"
Task: "Implement successful uncertainty widening in backend/src/services/storm_mode_forecast_adjustment_service.py"
Task: "Build the storm-mode diagnostics UI in frontend/src/features/storm-mode/components/StormModeEvaluationDetail.tsx"
```

## Parallel Example: User Story 2

```bash
Task: "Add contract tests for fallback payloads in tests/contract/test_storm_mode_fallback_api.py"
Task: "Add integration tests for weather-unavailable and rejected-trigger fallback behavior in tests/integration/test_storm_mode_fallbacks.py"
Task: "Add frontend interaction tests for fallback-state rendering in frontend/tests/test_storm_mode_fallbacks.tsx"
```

## Parallel Example: User Story 3

```bash
Task: "Add contract tests for adjustment-failure and retry-eligible notification responses in tests/contract/test_storm_mode_failure_api.py"
Task: "Add integration tests for baseline reversion and failed-delivery persistence in tests/integration/test_storm_mode_failures.py"
Task: "Add frontend interaction tests for reverted activation and failed notification display in frontend/tests/test_storm_mode_failures.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. Validate the full validated-trigger, scope-limited activation, uncertainty-widening, and linked-notification path before expanding scope.

### Incremental Delivery

1. Deliver US1 to establish validated activation, wider uncertainty, increased sensitivity, notification linkage, and authenticated diagnostics.
2. Add US2 to support weather-unavailable, rejected-trigger, and no-trigger fallback behavior without leaking storm-mode parameters into unsupported scopes.
3. Add US3 to harden adjustment-failure rollback, notification-delivery failure handling, and fully correlated failure diagnostics.
4. Finish with Phase 6 traceability, contract alignment, and cross-cutting verification.

### Parallel Team Strategy

1. One engineer can own persistence, migration, and backend service work in Phase 2.
2. In US1, backend storm-mode orchestration and frontend diagnostics can proceed in parallel after shared types are in place.
3. In later phases, fallback handling and failure handling can be split between backend outcome logic and frontend diagnostic-state rendering.
