# Tasks: Indicate Degraded Forecast Confidence in UI

**Input**: Design documents from `/specs/016-uc-16-degraded-forecast-confidence/`
**Prerequisites**: [plan.md](/Users/sahmed/Documents/311-forecast-system/specs/016-uc-16-degraded-forecast-confidence/plan.md), [spec.md](/Users/sahmed/Documents/311-forecast-system/specs/016-uc-16-degraded-forecast-confidence/spec.md), [research.md](/Users/sahmed/Documents/311-forecast-system/specs/016-uc-16-degraded-forecast-confidence/research.md), [data-model.md](/Users/sahmed/Documents/311-forecast-system/specs/016-uc-16-degraded-forecast-confidence/data-model.md), [degraded-forecast-confidence-api.yaml](/Users/sahmed/Documents/311-forecast-system/specs/016-uc-16-degraded-forecast-confidence/contracts/degraded-forecast-confidence-api.yaml), [quickstart.md](/Users/sahmed/Documents/311-forecast-system/specs/016-uc-16-degraded-forecast-confidence/quickstart.md)

**Tests**: Include backend unit, integration, and contract tests plus frontend interaction tests because UC-16 requires authenticated confidence-status retrieval, centrally managed degraded-confidence assessment, safe missing-signal and dismissed-signal fallback, and traceable render-failure observability.

**Organization**: Tasks are grouped by user story so each story can be implemented and verified independently while preserving one shared confidence-resolution, assessment, presentation, and render-observability architecture.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel when the task touches different files and does not depend on incomplete work
- **[Story]**: User story mapping for implementation and test traceability
- All task descriptions include exact file paths

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the planned backend, frontend, and test scaffolding for degraded-confidence retrieval, display, and render reporting.

- [ ] T001 Create the planned backend, frontend, and test directories in `backend/src/api/routes/`, `backend/src/api/schemas/`, `backend/src/services/`, `backend/src/repositories/`, `backend/src/models/`, `backend/src/clients/`, `backend/src/core/`, `frontend/src/api/`, `frontend/src/features/forecast-confidence/components/`, `frontend/src/features/forecast-confidence/hooks/`, `frontend/src/features/forecast-confidence/state/`, `frontend/src/pages/`, `frontend/src/types/`, `frontend/tests/`, `tests/contract/`, `tests/integration/`, and `tests/unit/`
- [ ] T002 Create backend Python module scaffolding for confidence-status routes, schemas, services, repositories, and models in `backend/src/api/routes/forecast_confidence.py`, `backend/src/api/schemas/forecast_confidence.py`, `backend/src/services/forecast_confidence_query_service.py`, `backend/src/services/forecast_confidence_rule_service.py`, `backend/src/services/forecast_confidence_presentation_service.py`, `backend/src/services/forecast_confidence_observability_service.py`, `backend/src/repositories/forecast_confidence_repository.py`, and `backend/src/models/forecast_confidence.py`
- [ ] T003 [P] Create frontend TypeScript scaffolding for confidence-status retrieval, indicator rendering, and render-event reporting in `frontend/src/api/forecastConfidenceApi.ts`, `frontend/src/types/forecastConfidence.ts`, `frontend/src/features/forecast-confidence/hooks/useForecastConfidence.ts`, `frontend/src/features/forecast-confidence/state/forecastConfidenceState.ts`, and `frontend/src/features/forecast-confidence/components/ForecastConfidenceIndicator.tsx`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build shared persistence, typed contracts, authenticated access, upstream signal reuse, and observability before story-specific behavior.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T004 Create the UC-16 persistence models and canonical vocabularies for `ForecastConfidenceRequest`, `ForecastConfidenceSignalResolution`, `ForecastConfidenceAssessmentResult`, and `ForecastConfidenceRenderEvent` in `backend/src/models/forecast_confidence.py`
- [ ] T005 [P] Create the initial forecast-confidence schema migration in `backend/src/models/migrations/016_forecast_confidence.py`
- [ ] T006 [P] Implement repository methods for request creation, signal-resolution persistence, prepared-result persistence, render-event persistence, request lookup, and terminal-state updates in `backend/src/repositories/forecast_confidence_repository.py`
- [ ] T007 [P] Define typed request and response schemas for confidence-status retrieval and render-event reporting in `backend/src/api/schemas/forecast_confidence.py`
- [ ] T008 [P] Implement authenticated and role-aware route dependencies for forecast-confidence endpoints in `backend/src/core/auth.py` and `backend/src/api/routes/forecast_confidence.py`
- [ ] T009 [P] Implement shared forecast-scope resolution and retained forecast-view lookup helpers reused from UC-03 through UC-05 in `backend/src/clients/forecast_view_client.py` and `backend/src/services/forecast_confidence_query_service.py`
- [ ] T010 [P] Implement upstream confidence-signal, anomaly, evaluation, and storm-mode lookup helpers reused from UC-06 through UC-15 in `backend/src/clients/forecast_quality_signal_client.py`, `backend/src/clients/anomaly_signal_client.py`, and `backend/src/clients/storm_mode_context_client.py`
- [ ] T011 [P] Implement structured logging helpers for confidence-request start, signal-resolution outcomes, assessment outcomes, prepared-response outcomes, and render-event outcomes in `backend/src/core/logging.py`
- [ ] T012 [P] Create frontend typed contracts and API client support for authenticated `GET /api/v1/forecast-views/confidence-status` and `POST /api/v1/forecast-views/confidence-status/{forecastConfidenceRequestId}/render-events` in `frontend/src/types/forecastConfidence.ts` and `frontend/src/api/forecastConfidenceApi.ts`
- [ ] T013 Implement shared scope normalization, canonical reason-category mapping, and centralized materiality-rule configuration in `backend/src/services/forecast_confidence_rule_service.py`
- [ ] T014 Implement the shared observability service for correlation-id propagation, request lifecycle updates, and terminal render-outcome handling in `backend/src/services/forecast_confidence_observability_service.py`
- [ ] T015 Implement the shared confidence-query service for forecast-context loading, upstream signal retrieval, and normalized signal-resolution assembly in `backend/src/services/forecast_confidence_query_service.py`
- [ ] T016 Implement the shared presentation service for normalized confidence-view shaping across degraded, normal, missing-signal, dismissed, and error states in `backend/src/services/forecast_confidence_presentation_service.py`

**Checkpoint**: Shared persistence, auth, upstream-source reuse, centralized rule vocabulary, observability, and typed contracts are ready. User story implementation can begin.

---

## Phase 3: User Story 1 - See a clear degraded-confidence indicator with the forecast (Priority: P1) 🎯 MVP

**Goal**: Retrieve the forecast scope and associated signals, confirm materially degraded confidence through centralized rules, prepare a clear indicator, render it with the forecast, and preserve correlated success observability.

**Independent Test**: Open a forecast view for a scope with confirmed degraded-confidence signals, verify the backend returns `degraded_confirmed` with `display_required`, verify the frontend shows the warning alongside the forecast, and verify request, assessment, and render outcomes are correlated in observability records.

### Tests for User Story 1

- [ ] T017 [P] [US1] Add contract and schema-validation tests for authenticated `GET /api/v1/forecast-views/confidence-status` success, `401`, `403`, and `422` responses plus degraded-confirmed payload requirements in `tests/contract/test_forecast_confidence_api.py`
- [ ] T018 [P] [US1] Add backend unit tests for scope normalization, signal-category mapping, centralized materiality-rule success, reason-category derivation, and degraded-view shaping in `tests/unit/test_forecast_confidence_services.py`
- [ ] T019 [P] [US1] Add integration tests for successful confidence-request persistence, resolved-signal persistence, degraded assessment-result persistence, and correlated render-success handling in `tests/integration/test_forecast_confidence_success.py`
- [ ] T020 [P] [US1] Add frontend interaction tests for degraded-warning display, reason-category messaging, forecast-visible behavior, and render-success submission in `frontend/tests/test_forecast_confidence_success.tsx`

### Implementation for User Story 1

- [ ] T021 [P] [US1] Implement forecast-context retrieval, upstream signal loading, and resolved-signal normalization for degraded-confidence candidates in `backend/src/services/forecast_confidence_query_service.py`
- [ ] T022 [P] [US1] Implement centralized degraded-confidence confirmation, materiality evaluation, and reason-category selection in `backend/src/services/forecast_confidence_rule_service.py`
- [ ] T023 [P] [US1] Implement degraded-confirmed assessment-result creation and warning-message preparation in `backend/src/services/forecast_confidence_presentation_service.py` and `backend/src/repositories/forecast_confidence_repository.py`
- [ ] T024 [US1] Implement end-to-end confidence-status orchestration for request creation, signal retrieval, rule evaluation, prepared-result persistence, and response assembly in `backend/src/services/forecast_confidence_query_service.py`, `backend/src/services/forecast_confidence_presentation_service.py`, and `backend/src/services/forecast_confidence_observability_service.py`
- [ ] T025 [US1] Implement the authenticated confidence-status retrieval endpoint with thin request handling in `backend/src/api/routes/forecast_confidence.py`
- [ ] T026 [P] [US1] Build the degraded-confidence UI treatment for warning banner, reason-category copy, and forecast-visible indicator placement in `frontend/src/features/forecast-confidence/components/ForecastConfidenceIndicator.tsx`
- [ ] T027 [US1] Implement the confidence-status hook, state transitions, and forecast-view integration for degraded-confirmed responses in `frontend/src/features/forecast-confidence/hooks/useForecastConfidence.ts`, `frontend/src/features/forecast-confidence/state/forecastConfidenceState.ts`, and `frontend/src/pages/ForecastPage.tsx`

**Checkpoint**: User Story 1 is independently functional and testable.

---

## Phase 4: User Story 2 - Avoid misleading warnings when confidence cannot be confirmed (Priority: P2)

**Goal**: Preserve a normal forecast display when signals are unavailable or dismissed as non-material while keeping those outcomes explicit and reviewable in backend records and UI state.

**Independent Test**: Open forecast views for one missing-signal scenario and one dismissed-signal scenario, then verify the backend returns `signals_missing` or `dismissed` with `not_displayed`, the forecast remains visible without a warning, and observability records distinguish the two terminal outcomes.

### Tests for User Story 2

- [ ] T028 [P] [US2] Add contract tests for `signals_missing` and `dismissed` confidence-status payloads, including required status messaging and no-warning semantics, in `tests/contract/test_forecast_confidence_fallback_api.py`
- [ ] T029 [P] [US2] Add backend unit tests for missing-signal classification, dismissed-signal materiality rejection, status-message derivation, and warning-suppression logic in `tests/unit/test_forecast_confidence_fallbacks.py`
- [ ] T030 [P] [US2] Add integration tests for missing-signal persistence, dismissed-signal persistence, normal forecast visibility, and distinct terminal observability outcomes in `tests/integration/test_forecast_confidence_fallbacks.py`
- [ ] T031 [P] [US2] Add frontend interaction tests for missing-signal messaging, dismissed-signal messaging, and normal forecast rendering with no degraded-warning display in `frontend/tests/test_forecast_confidence_fallbacks.tsx`

### Implementation for User Story 2

- [ ] T032 [US2] Implement missing-signal and failed-signal normalization that preserves explicit `signals_missing` outcomes without inferring degraded confidence in `backend/src/services/forecast_confidence_query_service.py` and `backend/src/repositories/forecast_confidence_repository.py`
- [ ] T033 [P] [US2] Implement false-signal dismissal and non-materiality handling with explicit dismissal reasons and `dismissed` assessment shaping in `backend/src/services/forecast_confidence_rule_service.py` and `backend/src/services/forecast_confidence_presentation_service.py`
- [ ] T034 [US2] Integrate fallback branching for `signals_missing` and `dismissed` response assembly plus terminal request updates in `backend/src/services/forecast_confidence_observability_service.py`, `backend/src/services/forecast_confidence_query_service.py`, and `backend/src/services/forecast_confidence_presentation_service.py`
- [ ] T035 [P] [US2] Build frontend fallback-state rendering for missing-signal and dismissed-signal responses without empty warning placeholders in `frontend/src/features/forecast-confidence/components/ForecastConfidenceUnavailableState.tsx` and `frontend/src/features/forecast-confidence/components/ForecastConfidenceDismissedState.tsx`
- [ ] T036 [US2] Integrate fallback-state handling and no-warning rendering into `frontend/src/features/forecast-confidence/hooks/useForecastConfidence.ts`, `frontend/src/features/forecast-confidence/state/forecastConfidenceState.ts`, and `frontend/src/pages/ForecastPage.tsx`

**Checkpoint**: User Stories 1 and 2 are independently functional and testable.

---

## Phase 5: User Story 3 - Preserve traceability when the degradation indicator cannot be rendered (Priority: P3)

**Goal**: Record final client render failures for prepared degraded-confidence indicators, keep the forecast visible when possible, and avoid falsely claiming that the warning rendered successfully.

**Independent Test**: Force a degraded-confidence response, inject an indicator render failure on the client, verify the forecast stays visible without the warning, verify the backend accepts and persists a `render_failed` event, and verify correlated records preserve the original degraded assessment plus the failed render outcome.

### Tests for User Story 3

- [ ] T037 [P] [US3] Add contract tests for authenticated `POST /api/v1/forecast-views/confidence-status/{forecastConfidenceRequestId}/render-events` `202`, `401`, `403`, `404`, and `422` handling plus render-failure payload validation in `tests/contract/test_forecast_confidence_render_events.py`
- [ ] T038 [P] [US3] Add backend unit tests for render-event validation, terminal render-outcome transitions, prepared-result immutability, and render-failure view-state projection in `tests/unit/test_forecast_confidence_render_failures.py`
- [ ] T039 [P] [US3] Add integration tests for render-failure event persistence, correlated request and result lookup, non-mutation of degraded assessment status, and accepted render-success reporting in `tests/integration/test_forecast_confidence_render_failures.py`
- [ ] T040 [P] [US3] Add frontend interaction tests for injected indicator render failure, forecast-visible fallback behavior, and render-failure submission in `frontend/tests/test_forecast_confidence_render_failures.tsx`

### Implementation for User Story 3

- [ ] T041 [US3] Implement render-event validation, request-result correlation checks, and render-event persistence in `backend/src/api/routes/forecast_confidence.py`, `backend/src/services/forecast_confidence_observability_service.py`, and `backend/src/repositories/forecast_confidence_repository.py`
- [ ] T042 [P] [US3] Implement render-failure outcome projection and `indicator_state = render_failed` read-model shaping without mutating prepared assessment status in `backend/src/services/forecast_confidence_presentation_service.py`
- [ ] T043 [US3] Implement the authenticated render-event endpoint with thin request handling and accepted-response semantics in `backend/src/api/routes/forecast_confidence.py`
- [ ] T044 [P] [US3] Build frontend render-failure fallback handling and failure-report submission around the confidence indicator in `frontend/src/features/forecast-confidence/components/ForecastConfidenceRenderFailure.tsx` and `frontend/src/features/forecast-confidence/components/ForecastConfidenceIndicator.tsx`
- [ ] T045 [US3] Integrate render-failure reporting, indicator-suppression fallback, and terminal client state handling into `frontend/src/features/forecast-confidence/hooks/useForecastConfidence.ts`, `frontend/src/features/forecast-confidence/state/forecastConfidenceState.ts`, and `frontend/src/pages/ForecastPage.tsx`

**Checkpoint**: All user stories are independently functional and reviewable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finish acceptance traceability, contract example alignment, observability assertions, and end-to-end verification for the shared degraded-confidence workflow.

- [ ] T046 [P] Review `docs/UC-16-AT.md` for acceptance-test alignment and map implementation plus verification steps for AT-01 through AT-09 in `specs/016-uc-16-degraded-forecast-confidence/quickstart.md`
- [ ] T047 [P] Align request and response examples for degraded-confirmed, normal, missing-signal, dismissed, and render-failure payloads in `specs/016-uc-16-degraded-forecast-confidence/contracts/degraded-forecast-confidence-api.yaml`
- [ ] T048 [P] Add observability and correlation-id assertions for success, missing-signal, dismissed-signal, and render-failure flows in `tests/integration/test_forecast_confidence_success.py`, `tests/integration/test_forecast_confidence_fallbacks.py`, and `tests/integration/test_forecast_confidence_render_failures.py`
- [ ] T049 Run end-to-end verification for contract, unit, integration, and frontend interaction suites covering degraded-confidence retrieval and render reporting in `tests/contract/`, `tests/unit/`, `tests/integration/`, and `frontend/tests/`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1: Setup**: No dependencies.
- **Phase 2: Foundational**: Depends on Phase 1 and blocks all user story work.
- **Phase 3: US1**: Depends on Phase 2 only; this is the MVP slice.
- **Phase 4: US2**: Depends on Phase 2 and on the shared confidence-retrieval and response flow established in US1.
- **Phase 5: US3**: Depends on Phase 2 and on the degraded-confidence preparation flow established in US1.
- **Phase 6: Polish**: Depends on the user stories being shipped.

### User Story Dependencies

- **US1 (P1)**: No dependency on other user stories after Foundational.
- **US2 (P2)**: Depends on US1 query, rule-evaluation, and response-shaping behavior, but remains independently testable through missing-signal and dismissed-signal scenarios.
- **US3 (P3)**: Depends on US1 prepared degraded-confidence results and frontend indicator rendering, and can proceed independently of US2.

### Within Each User Story

- Contract, unit, integration, and frontend interaction tests should be written before or alongside implementation and must fail before implementation is considered complete.
- Scope resolution and upstream signal retrieval precede rule evaluation.
- Rule evaluation precedes prepared-result persistence and route finalization.
- Frontend render and render-event reporting close only after backend request, prepared-result, and render-event persistence are stable.

### Explicit Task Prerequisites

- `T002` depends on `T001`.
- `T003` depends on `T001`.
- `T005` depends on `T004`.
- `T013` depends on `T007` and `T010`.
- `T014` depends on `T004`, `T006`, and `T011`.
- `T015` depends on `T006`, `T009`, and `T010`.
- `T016` depends on `T006`, `T007`, `T013`, and `T014`.
- `T021` depends on `T015`.
- `T022` depends on `T013` and `T015`.
- `T023` depends on `T006`, `T014`, `T016`, `T021`, and `T022`.
- `T024` depends on `T014`, `T015`, `T016`, `T021`, `T022`, and `T023`.
- `T025` depends on `T007`, `T008`, and `T024`.
- `T026` depends on `T012`.
- `T027` depends on `T012`, `T025`, and `T026`.
- `T032` depends on `T015` and `T024`.
- `T033` depends on `T013`, `T016`, and `T022`.
- `T034` depends on `T014`, `T024`, `T032`, and `T033`.
- `T035` depends on `T012`.
- `T036` depends on `T027` and `T035`.
- `T041` depends on `T006`, `T007`, `T014`, `T024`, and `T025`.
- `T042` depends on `T016` and `T041`.
- `T043` depends on `T007`, `T008`, and `T041`.
- `T044` depends on `T026`.
- `T045` depends on `T027`, `T043`, and `T044`.
- `T049` depends on `T025`, `T036`, `T043`, and `T045`.

## Parallel Opportunities

- Phase 1: `T003` can run in parallel with `T002` after `T001`.
- Phase 2: `T005` through `T012` can run in parallel after `T004`; `T013`, `T014`, `T015`, and `T016` begin once repository, upstream-source, schema, and logging scaffolding are ready.
- US1: `T017`, `T018`, `T019`, and `T020` can run in parallel; `T021`, `T022`, `T023`, and `T026` can run in parallel once foundational services exist, with `T024`, `T025`, and `T027` following their dependencies.
- US2: `T028`, `T029`, `T030`, and `T031` can run in parallel; `T033` and `T035` can run in parallel before `T032`, `T034`, and `T036` complete the fallback flow.
- US3: `T037`, `T038`, `T039`, and `T040` can run in parallel; `T042` and `T044` can run in parallel after render-event persistence is in place, followed by `T043` and `T045`.
- Phase 6: `T046`, `T047`, and `T048` can run in parallel before `T049`.

## Parallel Example: User Story 1

```bash
Task: "Add contract tests for authenticated GET /api/v1/forecast-views/confidence-status degraded-confirmed responses in tests/contract/test_forecast_confidence_api.py"
Task: "Add backend unit tests for centralized degraded-confidence rule evaluation in tests/unit/test_forecast_confidence_services.py"
Task: "Add integration tests for resolved-signal persistence and degraded assessment-result persistence in tests/integration/test_forecast_confidence_success.py"
Task: "Add frontend interaction tests for degraded-warning display and render-success submission in frontend/tests/test_forecast_confidence_success.tsx"
```

```bash
Task: "Implement forecast-context retrieval and signal normalization in backend/src/services/forecast_confidence_query_service.py"
Task: "Implement centralized degraded-confidence confirmation in backend/src/services/forecast_confidence_rule_service.py"
Task: "Build the degraded-confidence warning UI in frontend/src/features/forecast-confidence/components/ForecastConfidenceIndicator.tsx"
```

## Parallel Example: User Story 2

```bash
Task: "Add contract tests for signals_missing and dismissed confidence-status payloads in tests/contract/test_forecast_confidence_fallback_api.py"
Task: "Add integration tests for missing-signal and dismissed-signal observability in tests/integration/test_forecast_confidence_fallbacks.py"
Task: "Add frontend interaction tests for missing-signal and dismissed-signal fallback messaging in frontend/tests/test_forecast_confidence_fallbacks.tsx"
```

## Parallel Example: User Story 3

```bash
Task: "Add contract tests for POST /api/v1/forecast-views/confidence-status/{forecastConfidenceRequestId}/render-events handling in tests/contract/test_forecast_confidence_render_events.py"
Task: "Add integration tests for render-failure event persistence and degraded-result immutability in tests/integration/test_forecast_confidence_render_failures.py"
Task: "Add frontend interaction tests for indicator render failure fallback and reporting in frontend/tests/test_forecast_confidence_render_failures.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. Validate the full degraded-confidence retrieval, warning display, and render-success path before expanding scope.

### Incremental Delivery

1. Deliver US1 to establish authenticated confidence-status retrieval, centralized degraded-confidence confirmation, prepared warning display, and correlated success observability.
2. Add US2 to preserve truthful normal-display behavior when signals are missing or dismissed as non-material.
3. Add US3 to harden render-failure reporting, forecast-visible fallback, and non-mutating observability for failed indicator display.
4. Finish with Phase 6 traceability, contract alignment, and cross-cutting verification.

### Parallel Team Strategy

1. One engineer can own persistence, migrations, auth, and backend source-integration work in Phase 2.
2. In US1, backend confidence retrieval and rule-evaluation work can proceed in parallel with frontend indicator rendering after shared types are in place.
3. After US1, one engineer can own fallback-state behavior for US2 while another owns render-failure handling for US3.

---

## Notes

- The task list preserves UC-16’s requirement to reuse forecast, evaluation, anomaly, visualization, and storm-mode lineage from UC-01 through UC-15 rather than creating a new forecast source of truth.
- Every user story phase is independently testable against the spec and `docs/UC-16-AT.md`.
- All tasks follow the required checklist format with task IDs, optional parallel markers, story labels where required, and exact file paths.
- `tasks.md` remains a planning checklist rather than a place to record execution results.
