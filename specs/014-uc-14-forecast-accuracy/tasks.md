# Tasks: View Forecast Accuracy and Compare Predictions to Actuals

**Input**: Design documents from `/specs/014-uc-14-forecast-accuracy/`
**Prerequisites**: [plan.md](/Users/sahmed/Documents/311-forecast-system/specs/014-uc-14-forecast-accuracy/plan.md), [spec.md](/Users/sahmed/Documents/311-forecast-system/specs/014-uc-14-forecast-accuracy/spec.md), [research.md](/Users/sahmed/Documents/311-forecast-system/specs/014-uc-14-forecast-accuracy/research.md), [data-model.md](/Users/sahmed/Documents/311-forecast-system/specs/014-uc-14-forecast-accuracy/data-model.md), [forecast-accuracy-api.yaml](/Users/sahmed/Documents/311-forecast-system/specs/014-uc-14-forecast-accuracy/contracts/forecast-accuracy-api.yaml), [quickstart.md](/Users/sahmed/Documents/311-forecast-system/specs/014-uc-14-forecast-accuracy/quickstart.md)

**Tests**: Include backend unit, integration, and contract tests plus frontend interaction tests because UC-14 requires authenticated forecast-performance retrieval, exact-bucket alignment, metrics reuse and fallback, explicit unavailable or error states, and render-event observability.

**Organization**: Tasks are grouped by user story so each story can be implemented and verified independently while preserving the shared forecast-accuracy retrieval, metric-resolution, alignment, and observability architecture.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel when the task touches different files and does not depend on incomplete work
- **[Story]**: User story mapping for implementation and test traceability
- All task descriptions include exact file paths

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the planned backend, frontend, and test scaffolding for the shared forecast-accuracy workflow.

- [ ] T001 Create the planned backend, frontend, and test directories in `backend/src/api/routes/`, `backend/src/api/schemas/`, `backend/src/services/`, `backend/src/repositories/`, `backend/src/models/`, `backend/src/clients/`, `backend/src/core/`, `frontend/src/api/`, `frontend/src/features/forecast-accuracy/components/`, `frontend/src/features/forecast-accuracy/hooks/`, `frontend/src/features/forecast-accuracy/state/`, `frontend/src/pages/`, `frontend/src/types/`, `frontend/tests/`, `tests/contract/`, `tests/integration/`, and `tests/unit/`
- [ ] T002 Create backend Python module scaffolding for forecast-accuracy retrieval and render-event reporting in `backend/src/api/routes/forecast_accuracy.py`, `backend/src/api/schemas/forecast_accuracy.py`, `backend/src/services/forecast_accuracy_query_service.py`, `backend/src/services/forecast_accuracy_metric_service.py`, `backend/src/services/forecast_accuracy_alignment_service.py`, `backend/src/services/forecast_accuracy_observability_service.py`, `backend/src/repositories/forecast_accuracy_repository.py`, and `backend/src/models/forecast_accuracy.py`
- [ ] T003 [P] Create frontend TypeScript scaffolding for the forecast-performance page, API access, and typed state in `frontend/src/api/forecastAccuracyApi.ts`, `frontend/src/types/forecastAccuracy.ts`, `frontend/src/features/forecast-accuracy/hooks/useForecastAccuracy.ts`, `frontend/src/features/forecast-accuracy/state/forecastAccuracyState.ts`, and `frontend/src/pages/ForecastAccuracyPage.tsx`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build shared persistence, typed contracts, authorization, source retrieval, alignment, metric fallback, and observability before story-specific behavior.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T004 Create the UC-14 persistence models and canonical vocabularies for `ForecastAccuracyRequest`, `ForecastAccuracyMetricResolution`, `ForecastAccuracyComparisonResult`, `ForecastAccuracyAlignedBucket`, and `ForecastAccuracyRenderEvent` in `backend/src/models/forecast_accuracy.py`
- [ ] T005 [P] Create the initial forecast-accuracy schema migration in `backend/src/models/migrations/014_forecast_accuracy.py`
- [ ] T006 [P] Implement repository methods for request creation, terminal request updates, metric-resolution persistence, prepared-result persistence, aligned-bucket persistence, render-event persistence, and prepared-result lookup in `backend/src/repositories/forecast_accuracy_repository.py`
- [ ] T007 [P] Define typed request and response schemas for forecast-accuracy view retrieval, unavailable and error states, and render-event submission in `backend/src/api/schemas/forecast_accuracy.py`
- [ ] T008 [P] Implement authenticated and role-aware route dependencies for forecast-accuracy endpoints in `backend/src/core/auth.py` and `backend/src/api/routes/forecast_accuracy.py`
- [ ] T009 [P] Implement retained historical-source lookup helpers for daily forecast lineage plus approved actual-demand lineage in `backend/src/clients/forecast_history_client.py` and `backend/src/clients/actual_demand_client.py`
- [ ] T010 [P] Implement structured logging helpers for request start, forecast retrieval, actual retrieval, metric fallback, alignment refusal, prepared-result storage, and render outcomes in `backend/src/core/logging.py`
- [ ] T011 [P] Create frontend typed contracts and API client support for authenticated `GET /api/v1/forecast-accuracy` and `POST /api/v1/forecast-accuracy/{forecastAccuracyRequestId}/render-events` in `frontend/src/types/forecastAccuracy.ts` and `frontend/src/api/forecastAccuracyApi.ts`
- [ ] T012 Implement default-scope resolution, exact-window metric-match rules, and shared view-status derivation helpers in `backend/src/services/forecast_accuracy_query_service.py` and `backend/src/services/forecast_accuracy_metric_service.py`
- [ ] T013 Implement the shared alignment service for matching-bucket selection, excluded-bucket counting, and unsafe-overlap rejection in `backend/src/services/forecast_accuracy_alignment_service.py`
- [ ] T014 Implement the shared observability service for correlation-id propagation, request lifecycle updates, and render-failure status transitions in `backend/src/services/forecast_accuracy_observability_service.py`

**Checkpoint**: Shared persistence, authorization, retained-source access, metric fallback rules, alignment behavior, logging, and typed contracts are ready. User story implementation can begin.

---

## Phase 3: User Story 1 - Review forecast accuracy for a selected scope (Priority: P1) 🎯 MVP

**Goal**: Let an authorized city planner load the default or selected forecast-performance scope, retrieve retained historical forecasts and matching actual demand, reuse or compute MAE/RMSE/MAPE for the same scope, align buckets correctly, and render interpretable prediction-versus-actual output.

**Independent Test**: Open the forecast-performance page as an authorized planner, load the default last 30 completed days, change scope inputs, and verify aligned comparison buckets plus MAE, RMSE, and MAPE appear for the same time window without off-by-one mismatches.

### Tests for User Story 1

- [ ] T015 [P] [US1] Add contract tests for authenticated `GET /api/v1/forecast-accuracy` `200`, `401`, `403`, and `422` responses plus authenticated `POST /render-events` `202` success in `tests/contract/test_forecast_accuracy_api.py`
- [ ] T016 [P] [US1] Add backend unit tests for default last-30-completed-days scope resolution, exact retained-metric matching, daily forecast selection, and view-status derivation in `tests/unit/test_forecast_accuracy_services.py`
- [ ] T017 [P] [US1] Add integration tests for successful request persistence, retained forecast retrieval, approved actual retrieval, aligned-bucket persistence, prepared-result storage, and success logging in `tests/integration/test_forecast_accuracy_success.py`
- [ ] T018 [P] [US1] Add frontend interaction tests for authenticated default load, scope changes, aligned comparison rendering, and metrics display in `frontend/tests/test_forecast_accuracy_success.tsx`

### Implementation for User Story 1

- [ ] T019 [P] [US1] Implement retained forecast and actual-demand retrieval plus exact-scope request assembly in `backend/src/services/forecast_accuracy_query_service.py`
- [ ] T020 [P] [US1] Implement precomputed metric reuse and on-demand MAE, RMSE, and MAPE computation for exact matching windows in `backend/src/services/forecast_accuracy_metric_service.py`
- [ ] T021 [P] [US1] Implement aligned comparison-result assembly, bucket-level error calculation, and prepared-view persistence in `backend/src/services/forecast_accuracy_alignment_service.py` and `backend/src/repositories/forecast_accuracy_repository.py`
- [ ] T022 [US1] Implement the authenticated forecast-accuracy retrieval endpoint with thin request handling in `backend/src/api/routes/forecast_accuracy.py`
- [ ] T023 [P] [US1] Build the forecast-performance UI for scope filters, metrics summary, and prediction-versus-actual comparison output in `frontend/src/features/forecast-accuracy/components/ForecastAccuracyFilters.tsx`, `frontend/src/features/forecast-accuracy/components/ForecastAccuracyMetrics.tsx`, and `frontend/src/features/forecast-accuracy/components/ForecastAccuracyComparison.tsx`
- [ ] T024 [US1] Implement the forecast-accuracy hook, state transitions, and page composition for default load, scope updates, and successful render reporting in `frontend/src/features/forecast-accuracy/hooks/useForecastAccuracy.ts`, `frontend/src/features/forecast-accuracy/state/forecastAccuracyState.ts`, and `frontend/src/pages/ForecastAccuracyPage.tsx`

**Checkpoint**: User Story 1 is independently functional and testable.

---

## Phase 4: User Story 2 - Continue analysis when metrics are unavailable (Priority: P2)

**Goal**: Preserve useful prediction-versus-actual analysis when retained metrics are missing or on-demand computation fails, while clearly indicating that summary metrics are unavailable.

**Independent Test**: Request forecast-performance data for a scope where aligned forecasts and actuals exist but retained metrics do not, verify one on-demand computation attempt occurs, and confirm the UI renders aligned comparisons with explicit metrics-unavailable messaging if computation also fails.

### Tests for User Story 2

- [ ] T025 [P] [US2] Add contract tests for `GET /api/v1/forecast-accuracy` responses with `rendered_without_metrics` status and explicit `metricResolutionStatus` or `statusMessage` fields in `tests/contract/test_forecast_accuracy_metrics_fallback.py`
- [ ] T026 [P] [US2] Add backend unit tests for missing-precomputed-metrics logging, on-demand metric fallback, and metrics-unavailable view shaping in `tests/unit/test_forecast_accuracy_metric_fallback.py`
- [ ] T027 [P] [US2] Add integration tests for retained-metrics miss, on-demand metric-computation attempt, unavailable-metrics persistence, and correlation-aware logging in `tests/integration/test_forecast_accuracy_metrics_fallback.py`
- [ ] T028 [P] [US2] Add frontend interaction tests for metrics-unavailable messaging while comparison buckets remain visible in `frontend/tests/test_forecast_accuracy_metrics_fallback.tsx`

### Implementation for User Story 2

- [ ] T029 [US2] Implement missing-precomputed-metrics logging, on-demand metric fallback, and `rendered_without_metrics` result creation in `backend/src/services/forecast_accuracy_metric_service.py` and `backend/src/services/forecast_accuracy_observability_service.py`
- [ ] T030 [P] [US2] Persist metric-resolution outcomes and comparison results for fallback requests in `backend/src/repositories/forecast_accuracy_repository.py`
- [ ] T031 [P] [US2] Build frontend metrics-unavailable messaging and degraded-summary presentation in `frontend/src/features/forecast-accuracy/components/ForecastAccuracyMetricsUnavailable.tsx`
- [ ] T032 [US2] Integrate fallback response handling into `frontend/src/features/forecast-accuracy/hooks/useForecastAccuracy.ts` and `frontend/src/pages/ForecastAccuracyPage.tsx`

**Checkpoint**: User Stories 1 and 2 are independently functional and testable.

---

## Phase 5: User Story 3 - See a clear failure state when required data or visualization is unavailable (Priority: P3)

**Goal**: Show explicit unavailable or error states when forecasts are missing, actuals are missing, alignment is unsafe, or client rendering fails, while preserving traceable operational records for each request.

**Independent Test**: Trigger missing forecast data, missing actual demand, empty overlap, and a client render failure, then verify the UI never shows misleading partial comparisons and the backend records the matching unavailable or render-failed outcome.

### Tests for User Story 3

- [ ] T033 [P] [US3] Add contract tests for `GET /api/v1/forecast-accuracy` unavailable or error responses and `POST /render-events` `401`, `403`, `404`, and `422` responses in `tests/contract/test_forecast_accuracy_failure_states.py`
- [ ] T034 [P] [US3] Add backend unit tests for forecast-missing, actual-missing, alignment-unavailable, and render-failed status transitions in `tests/unit/test_forecast_accuracy_failure_states.py`
- [ ] T035 [P] [US3] Add integration tests for missing-forecast, missing-actual, empty-overlap, and render-failure observability flows in `tests/integration/test_forecast_accuracy_failure_states.py`
- [ ] T036 [P] [US3] Add frontend interaction tests for unavailable-state messaging, error-state rendering, and failed-render reporting in `frontend/tests/test_forecast_accuracy_failure_states.tsx`

### Implementation for User Story 3

- [ ] T037 [US3] Implement missing-forecast, missing-actual, and unsafe-alignment outcome handling with terminal request updates and zero-bucket prepared results in `backend/src/services/forecast_accuracy_query_service.py`, `backend/src/services/forecast_accuracy_alignment_service.py`, and `backend/src/repositories/forecast_accuracy_repository.py`
- [ ] T038 [P] [US3] Implement the authenticated render-event endpoint, render-failure acceptance, and request-status update logic in `backend/src/api/routes/forecast_accuracy.py` and `backend/src/services/forecast_accuracy_observability_service.py`
- [ ] T039 [P] [US3] Build frontend unavailable and error-state components plus render-failure reporting helpers in `frontend/src/features/forecast-accuracy/components/ForecastAccuracyUnavailable.tsx`, `frontend/src/features/forecast-accuracy/components/ForecastAccuracyError.tsx`, and `frontend/src/api/forecastAccuracyApi.ts`
- [ ] T040 [US3] Integrate unavailable-state rendering, error-state rendering, and render-event reporting into `frontend/src/features/forecast-accuracy/hooks/useForecastAccuracy.ts` and `frontend/src/pages/ForecastAccuracyPage.tsx`

**Checkpoint**: All user stories are independently functional and reviewable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finish acceptance traceability, contract alignment, observability assertions, and end-to-end verification for the shared forecast-accuracy workflow.

- [ ] T041 [P] Map implementation and verification steps for AT-01 through AT-12 in `specs/014-uc-14-forecast-accuracy/quickstart.md`
- [ ] T042 [P] Align request and response examples for rendered-with-metrics, rendered-without-metrics, unavailable, error, and render-event outcomes in `specs/014-uc-14-forecast-accuracy/contracts/forecast-accuracy-api.yaml`
- [ ] T043 [P] Add observability and correlation-id assertions for success, metrics fallback, unavailable, and render-failure flows in `tests/integration/test_forecast_accuracy_success.py`, `tests/integration/test_forecast_accuracy_metrics_fallback.py`, and `tests/integration/test_forecast_accuracy_failure_states.py`
- [ ] T044 Run end-to-end verification for contract, unit, integration, and frontend interaction suites covering forecast-accuracy retrieval and render-event outcomes in `tests/contract/`, `tests/unit/`, `tests/integration/`, and `frontend/tests/`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1: Setup**: No dependencies.
- **Phase 2: Foundational**: Depends on Phase 1 and blocks all user story work.
- **Phase 3: US1**: Depends on Phase 2 only; this is the MVP slice.
- **Phase 4: US2**: Depends on Phase 2 and on the successful retrieval and alignment path established in US1.
- **Phase 5: US3**: Depends on Phase 2 and on the retrieval, alignment, and observability path established in US1.
- **Phase 6: Polish**: Depends on the user stories being shipped.

### User Story Dependencies

- **US1 (P1)**: No dependency on other user stories after Foundational.
- **US2 (P2)**: Depends on US1 retrieval and alignment behavior, but remains independently testable through metrics-fallback handling.
- **US3 (P3)**: Depends on US1 retrieval and observability behavior; it can proceed independently of US2 once the prepared-result lifecycle exists.

### Within Each User Story

- Contract, unit, integration, and frontend interaction tests should be written before or alongside implementation and must fail before implementation is considered complete.
- Source retrieval, metric resolution, and alignment behavior precede route finalization.
- Route and frontend state handling depend on the relevant backend services and typed contracts.
- Render-event handling depends on prepared-result persistence and authenticated request ownership checks.

### Explicit Task Prerequisites

- `T002` depends on `T001`.
- `T003` depends on `T001`.
- `T005` depends on `T004`.
- `T012` depends on `T007`, `T009`, and `T010`.
- `T013` depends on `T004`, `T006`, and `T009`.
- `T014` depends on `T004`, `T006`, and `T010`.
- `T019` depends on `T012`.
- `T020` depends on `T012` and `T019`.
- `T021` depends on `T013`, `T019`, and `T020`.
- `T022` depends on `T007`, `T008`, `T019`, `T020`, and `T021`.
- `T023` depends on `T011`.
- `T024` depends on `T011`, `T022`, and `T023`.
- `T029` depends on `T020` and `T014`.
- `T030` depends on `T006` and `T029`.
- `T031` depends on `T023`.
- `T032` depends on `T024` and `T031`.
- `T037` depends on `T019`, `T021`, and `T014`.
- `T038` depends on `T007`, `T008`, `T014`, and `T006`.
- `T039` depends on `T011`.
- `T040` depends on `T024`, `T038`, and `T039`.
- `T044` depends on `T022`, `T032`, `T040`, and the related test tasks for each story.

## Parallel Opportunities

- Phase 1: `T003` can run in parallel with `T002` after `T001`.
- Phase 2: `T005` through `T011` can run in parallel after `T004`; `T012`, `T013`, and `T014` begin once the shared persistence, schema, source, and logging scaffolding are ready.
- US1: `T015`, `T016`, `T017`, and `T018` can run in parallel; `T019`, `T020`, and `T023` can run in parallel after the foundational services are in place; `T021` can proceed once retrieval and metric services exist.
- US2: `T025`, `T026`, `T027`, and `T028` can run in parallel; `T030` and `T031` can run in parallel after `T029`.
- US3: `T033`, `T034`, `T035`, and `T036` can run in parallel; `T038` and `T039` can run in parallel after the request and prepared-result lifecycle is stable.
- Phase 6: `T041`, `T042`, and `T043` can run in parallel before `T044`.

## Parallel Example: User Story 1

```bash
Task: "Add contract tests for GET /api/v1/forecast-accuracy and successful POST render-event handling in tests/contract/test_forecast_accuracy_api.py"
Task: "Add backend unit tests for default scope resolution, product selection, and view-status derivation in tests/unit/test_forecast_accuracy_services.py"
Task: "Add integration tests for successful request persistence and aligned-bucket storage in tests/integration/test_forecast_accuracy_success.py"
Task: "Add frontend interaction tests for default load, scope changes, and metrics rendering in frontend/tests/test_forecast_accuracy_success.tsx"
```

```bash
Task: "Implement retained forecast and actual-demand retrieval in backend/src/services/forecast_accuracy_query_service.py"
Task: "Implement precomputed metric reuse and on-demand MAE, RMSE, and MAPE computation in backend/src/services/forecast_accuracy_metric_service.py"
Task: "Build the forecast-performance UI in frontend/src/features/forecast-accuracy/components/ForecastAccuracyComparison.tsx"
```

## Parallel Example: User Story 2

```bash
Task: "Add contract tests for rendered_without_metrics responses in tests/contract/test_forecast_accuracy_metrics_fallback.py"
Task: "Add integration tests for retained-metrics miss and on-demand fallback outcomes in tests/integration/test_forecast_accuracy_metrics_fallback.py"
Task: "Add frontend interaction tests for metrics-unavailable messaging in frontend/tests/test_forecast_accuracy_metrics_fallback.tsx"
```

## Parallel Example: User Story 3

```bash
Task: "Add contract tests for unavailable or error retrieval responses and POST render-event failure responses in tests/contract/test_forecast_accuracy_failure_states.py"
Task: "Add integration tests for missing-forecast, missing-actual, empty-overlap, and render-failure observability in tests/integration/test_forecast_accuracy_failure_states.py"
Task: "Add frontend interaction tests for unavailable and error states plus failed-render reporting in frontend/tests/test_forecast_accuracy_failure_states.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. Validate the full authenticated forecast-performance retrieval and aligned-render path before expanding scope.

### Incremental Delivery

1. Deliver US1 to establish authenticated scope loading, source retrieval, exact-bucket alignment, and metrics-present rendering.
2. Add US2 to support retained-metrics miss handling and metrics-unavailable fallback without losing valid comparisons.
3. Add US3 to harden unavailable and error-state handling plus render-failure observability.
4. Finish with Phase 6 traceability, contract alignment, and cross-cutting verification.

### Parallel Team Strategy

1. One engineer can own persistence, migration, and backend service work in Phase 2.
2. In US1, backend retrieval and metric work can proceed in parallel with frontend filter and visualization work after shared types are in place.
3. In later phases, metrics-fallback handling and failure-state or render-event handling can be split between backend outcome logic and frontend response-state rendering.
