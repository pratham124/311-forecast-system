# Tasks: Drill Alert Details and Context

**Input**: Design documents from `/specs/012-uc-12-drill-alert-details/`
**Prerequisites**: [plan.md](/Users/sahmed/Documents/311-forecast-system/specs/012-uc-12-drill-alert-details/plan.md), [spec.md](/Users/sahmed/Documents/311-forecast-system/specs/012-uc-12-drill-alert-details/spec.md), [research.md](/Users/sahmed/Documents/311-forecast-system/specs/012-uc-12-drill-alert-details/research.md), [data-model.md](/Users/sahmed/Documents/311-forecast-system/specs/012-uc-12-drill-alert-details/data-model.md), [alert-detail-context-api.yaml](/Users/sahmed/Documents/311-forecast-system/specs/012-uc-12-drill-alert-details/contracts/alert-detail-context-api.yaml), [quickstart.md](/Users/sahmed/Documents/311-forecast-system/specs/012-uc-12-drill-alert-details/quickstart.md)

**Tests**: Include backend unit, integration, and contract tests plus frontend interaction tests because the plan and quickstart require acceptance-aligned verification for complete, partial, and error detail states.

**Organization**: Tasks are grouped by user story so each story can be implemented and verified independently while preserving the shared authenticated drill-down architecture.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel when the task touches different files and does not depend on incomplete work
- **[Story]**: User story mapping for implementation and test traceability
- All task descriptions include exact file paths

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the planned backend, frontend, and test scaffolding for the alert-detail drill-down feature.

- [ ] T001 Create the planned backend, frontend, and test directories in `backend/src/api/routes/`, `backend/src/api/schemas/`, `backend/src/repositories/`, `backend/src/services/`, `backend/src/models/`, `backend/src/core/`, `frontend/src/api/`, `frontend/src/features/alert-details/components/`, `frontend/src/features/alert-details/hooks/`, `frontend/src/features/alert-details/state/`, `frontend/src/pages/`, `frontend/src/types/`, `tests/contract/`, `tests/integration/`, and `tests/unit/`
- [ ] T002 Create backend Python module scaffolding for the drill-down surface in `backend/src/api/routes/alert_details.py`, `backend/src/api/schemas/alert_details.py`, `backend/src/repositories/alert_detail_repository.py`, `backend/src/services/alert_detail_service.py`, and `backend/src/models/alert_detail_load_record.py`
- [ ] T003 [P] Create frontend TypeScript scaffolding for alert-detail retrieval and rendering in `frontend/src/api/alertDetailsApi.ts`, `frontend/src/types/alertDetails.ts`, `frontend/src/features/alert-details/hooks/useAlertDetails.ts`, and `frontend/src/pages/AlertDetailPage.tsx`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build the shared persistence, typed contracts, source resolution, and observability infrastructure required before story-specific behavior.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T004 Create the UC-12 observability model and canonical vocabularies for `AlertDetailLoadRecord` in `backend/src/models/alert_detail_load_record.py`
- [ ] T005 [P] Create the initial alert-detail persistence migration in `backend/src/models/migrations/012_alert_detail_load_records.py`
- [ ] T006 [P] Implement repository methods for alert-detail load creation, component-status updates, terminal-state persistence, and render-event recording in `backend/src/repositories/alert_detail_repository.py`
- [ ] T007 [P] Define typed request and response schemas for detail retrieval and render-event reporting in `backend/src/api/schemas/alert_details.py`
- [ ] T008 [P] Implement authenticated and role-aware route dependencies for alert-detail endpoints in `backend/src/core/auth.py` and `backend/src/api/routes/alert_details.py`
- [ ] T009 [P] Implement shared alert-source resolution for `threshold_alert` and `surge_alert` lineage lookup in `backend/src/services/alert_source_resolution_service.py`
- [ ] T010 [P] Implement structured logging helpers for detail-request start, component retrieval outcomes, preparation status, render status, and failures in `backend/src/core/logging.py`
- [ ] T011 [P] Create frontend typed contracts and API client support for alert-detail `GET` and render-event `POST` calls in `frontend/src/types/alertDetails.ts` and `frontend/src/api/alertDetailsApi.ts`
- [ ] T012 Implement the shared alert-detail orchestration service skeleton and response assembly entrypoint in `backend/src/services/alert_detail_service.py`

**Checkpoint**: Shared persistence, source resolution, auth, logging, and typed contracts are ready. User story implementation can begin.

---

## Phase 3: User Story 1 - Review complete alert context (Priority: P1) 🎯 MVP

**Goal**: Let an operational manager open one selected alert and see forecast distribution, top-5 driver attribution, and the previous 7 days of anomaly context in one coherent detail view with correlated success observability.

**Independent Test**: Select an alert with all supporting context available and verify the backend returns a fully prepared detail payload, the frontend renders all three components together, and correlated load records show successful retrieval, preparation, and render completion.

### Tests for User Story 1

- [ ] T013 [P] [US1] Add contract tests for authenticated `GET /api/v1/alert-details/{alertSource}/{alertId}` success, `401`, `403`, and `404` responses plus unsupported-source validation in `tests/contract/test_alert_detail_context.py`
- [ ] T014 [P] [US1] Add backend unit tests for top-5 driver trimming, 7-day anomaly-window bounding, and view-status derivation for complete detail payloads in `tests/unit/test_alert_detail_service.py`
- [ ] T015 [P] [US1] Add integration tests for successful threshold-alert and surge-alert detail retrieval, load-record persistence, and preparation completion in `tests/integration/test_alert_detail_success.py`
- [ ] T016 [P] [US1] Add frontend interaction tests for selected-alert metadata, complete detail rendering, and render-success reporting in `frontend/tests/test_alert_detail_success.tsx`

### Implementation for User Story 1

- [ ] T017 [P] [US1] Implement forecast-distribution context retrieval and normalization for selected alerts in `backend/src/services/alert_distribution_context_service.py`
- [ ] T018 [P] [US1] Implement top-5 driver-attribution retrieval and normalization for selected alerts in `backend/src/services/alert_driver_context_service.py`
- [ ] T019 [P] [US1] Implement 7-day anomaly-context retrieval and normalization for selected alerts in `backend/src/services/alert_anomaly_context_service.py`
- [ ] T020 [US1] Implement full alert-detail assembly, successful preparation persistence, and rendered-response shaping in `backend/src/services/alert_detail_service.py`
- [ ] T021 [US1] Implement the authenticated alert-detail retrieval endpoint with thin request handling in `backend/src/api/routes/alert_details.py`
- [ ] T022 [P] [US1] Build alert-detail UI sections for selected alert metadata, forecast distribution, driver attribution, and anomaly timeline in `frontend/src/features/alert-details/components/AlertDetailView.tsx`
- [ ] T023 [US1] Implement the alert-detail data hook and page composition for loading state, complete response handling, and render-success submission in `frontend/src/features/alert-details/hooks/useAlertDetails.ts` and `frontend/src/pages/AlertDetailPage.tsx`

**Checkpoint**: User Story 1 is independently functional and testable.

---

## Phase 4: User Story 2 - Continue review when some context is unavailable (Priority: P2)

**Goal**: Preserve decision support when one or more supporting components are unavailable by returning a truthful partial payload when reliable context remains, and by showing a clear unavailable-detail state when no reliable component remains.

**Independent Test**: Select alerts where distribution, drivers, or anomalies are unavailable individually and in combinations, including cases where all supporting components are unavailable, and verify the detail view shows remaining reliable context when present, falls back to an unavailable-detail state when none remains, omits misleading empty visualizations, and logs each unavailable component.

### Tests for User Story 2

- [ ] T024 [P] [US2] Add contract tests for `partial` alert-detail responses with single and multiple unavailable components plus the all-components-unavailable response in `tests/contract/test_alert_detail_partial_contract.py`
- [ ] T025 [P] [US2] Add backend unit tests for component-status assignment, missing-component lists, partial-view status messaging, and the no-reliable-component unavailable state in `tests/unit/test_alert_detail_partial_states.py`
- [ ] T026 [P] [US2] Add integration tests for single-component, multi-component, and all-components-unavailable flows with persisted outcomes in `tests/integration/test_alert_detail_partial.py`
- [ ] T027 [P] [US2] Add frontend interaction tests for unavailable-component messaging, reliable-component-only rendering, and the unavailable-detail fallback state in `frontend/tests/test_alert_detail_partial.tsx`

### Implementation for User Story 2

- [ ] T028 [US2] Implement unavailable-component classification, partial-view status selection, and the no-reliable-component unavailable state in `backend/src/services/alert_detail_service.py`
- [ ] T029 [P] [US2] Persist explicit unavailable-component outcomes and partial terminal states in `backend/src/repositories/alert_detail_repository.py`
- [ ] T030 [P] [US2] Build UI treatment for unavailable distribution, drivers, and anomalies plus the unavailable-detail fallback state without empty placeholder charts in `frontend/src/features/alert-details/components/AlertDetailUnavailableState.tsx`
- [ ] T031 [US2] Integrate partial-view rendering, unavailable-component messaging, and the no-reliable-component fallback state into `frontend/src/features/alert-details/hooks/useAlertDetails.ts` and `frontend/src/pages/AlertDetailPage.tsx`

**Checkpoint**: User Stories 1 and 2 are independently functional and testable.

---

## Phase 5: User Story 3 - See a clear failure state when details cannot be displayed (Priority: P3)

**Goal**: Surface a full error state when component retrieval or visualization rendering fails, while preserving correlated failure observability for backend and client-side failures.

**Independent Test**: Force a component retrieval failure and a client render failure, then verify the UI shows an error state instead of a partial or corrupted detail view and the persisted load record captures failure category, failure reason, and final error status.

### Tests for User Story 3

- [ ] T032 [P] [US3] Add contract tests for error-state detail responses and authenticated `POST /api/v1/alert-details/{alertDetailLoadId}/render-events` success, `401`, `403`, validation, and `404` handling in `tests/contract/test_alert_detail_render_events.py`
- [ ] T033 [P] [US3] Add backend unit tests for failed-component escalation, preparation-failure handling, and render-failure terminal transitions in `tests/unit/test_alert_detail_error_states.py`
- [ ] T034 [P] [US3] Add integration tests for retrieval timeout or service-failure flows plus persisted error outcomes in `tests/integration/test_alert_detail_failures.py`
- [ ] T035 [P] [US3] Add frontend interaction tests for full error-state rendering and render-failure reporting in `frontend/tests/test_alert_detail_error.tsx`

### Implementation for User Story 3

- [ ] T036 [US3] Implement failed-component classification, failure-category mapping, and error-response assembly in `backend/src/services/alert_detail_service.py`
- [ ] T037 [P] [US3] Persist retrieval failures, preparation failures, and render-failure terminal outcomes in `backend/src/repositories/alert_detail_repository.py`
- [ ] T038 [US3] Implement the authenticated render-event endpoint for final client render outcome reporting in `backend/src/api/routes/alert_details.py`
- [ ] T039 [P] [US3] Build frontend error-state rendering and failed-render fallback messaging in `frontend/src/features/alert-details/components/AlertDetailErrorState.tsx`
- [ ] T040 [US3] Integrate render-failure reporting and terminal error handling into `frontend/src/features/alert-details/hooks/useAlertDetails.ts` and `frontend/src/pages/AlertDetailPage.tsx`

**Checkpoint**: All user stories are independently functional and reviewable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finish traceability, acceptance alignment, and final verification across complete, partial, and error states.

- [ ] T041 [P] Map implementation and verification steps for AT-01 through AT-12 plus clarification-backed multi-missing-component behavior in `specs/012-uc-12-drill-alert-details/quickstart.md`
- [ ] T042 [P] Add observability and correlation-id assertions for successful, partial, and error alert-detail loads in `tests/integration/test_alert_detail_success.py`, `tests/integration/test_alert_detail_partial.py`, and `tests/integration/test_alert_detail_failures.py`
- [ ] T043 [P] Align request and response examples for rendered, partial, and error payloads plus render-event reporting in `specs/012-uc-12-drill-alert-details/contracts/alert-detail-context-api.yaml`
- [ ] T044 Run end-to-end verification for contract, unit, integration, and frontend interaction suites covering alert-detail drill-down in `tests/contract/`, `tests/unit/`, `tests/integration/`, and `frontend/tests/`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1: Setup**: No dependencies.
- **Phase 2: Foundational**: Depends on Phase 1 and blocks all user story work.
- **Phase 3: US1**: Depends on Phase 2 only; this is the MVP slice.
- **Phase 4: US2**: Depends on Phase 2 and on the complete detail assembly established in US1.
- **Phase 5: US3**: Depends on Phase 2 and on the shared load-record and response pipeline established in US1.
- **Phase 6: Polish**: Depends on the user stories being shipped.

### User Story Dependencies

- **US1 (P1)**: No dependency on other user stories after Foundational.
- **US2 (P2)**: Depends on US1 detail assembly and frontend rendering behavior, but remains independently testable through partial states.
- **US3 (P3)**: Depends on US1 load-record creation and normalized response handling; it can proceed independently of US2.

### Within Each User Story

- Contract, unit, integration, and frontend interaction tests should be written before or alongside implementation and must fail before implementation is considered complete.
- Backend context-retrieval helpers precede service orchestration.
- Service orchestration precedes route and frontend state finalization.
- Frontend render reporting closes only after backend load-record and render-event handling are stable.

### Explicit Task Prerequisites

- `T002` depends on `T001`.
- `T003` depends on `T001`.
- `T005` depends on `T004`.
- `T012` depends on `T004`, `T006`, `T009`, and `T010`.
- `T017`, `T018`, and `T019` depend on `T009`.
- `T020` depends on `T012`, `T017`, `T018`, and `T019`.
- `T021` depends on `T007`, `T008`, and `T020`.
- `T022` depends on `T011`.
- `T023` depends on `T011`, `T021`, and `T022`.
- `T028` depends on `T020`.
- `T029` depends on `T006` and `T028`.
- `T030` depends on `T022`.
- `T031` depends on `T023` and `T030`.
- `T036` depends on `T020`.
- `T037` depends on `T006` and `T036`.
- `T038` depends on `T007`, `T008`, and `T037`.
- `T039` depends on `T022`.
- `T040` depends on `T023`, `T038`, and `T039`.
- `T044` depends on `T021`, `T031`, `T038`, and `T040`.

## Parallel Opportunities

- Phase 1: `T003` can run in parallel with `T002` after `T001`.
- Phase 2: `T005` through `T011` can run in parallel after `T004`; `T012` begins once repository, source-resolution, and logging scaffolding are ready.
- US1: `T013`, `T014`, `T015`, and `T016` can run in parallel; `T017`, `T018`, and `T019` can run in parallel before `T020`; `T022` can proceed in parallel with backend service work after typed contracts exist.
- US2: `T024`, `T025`, `T026`, and `T027` can run in parallel; `T029` and `T030` can run in parallel after `T028`.
- US3: `T032`, `T033`, `T034`, and `T035` can run in parallel; `T037` and `T039` can run in parallel after `T036`.
- Phase 6: `T041`, `T042`, and `T043` can run in parallel before `T044`.

## Parallel Example: User Story 1

```bash
Task: "Add contract tests for authenticated GET /api/v1/alert-details/{alertSource}/{alertId} success, 401, 403, and 404 responses in tests/contract/test_alert_detail_context.py"
Task: "Add backend unit tests for top-5 driver trimming, 7-day anomaly-window bounding, and view-status derivation in tests/unit/test_alert_detail_service.py"
Task: "Add integration tests for successful threshold-alert and surge-alert detail retrieval in tests/integration/test_alert_detail_success.py"
Task: "Add frontend interaction tests for complete detail rendering and render-success reporting in frontend/tests/test_alert_detail_success.tsx"
```

```bash
Task: "Implement forecast-distribution context retrieval and normalization in backend/src/services/alert_distribution_context_service.py"
Task: "Implement top-5 driver-attribution retrieval and normalization in backend/src/services/alert_driver_context_service.py"
Task: "Implement 7-day anomaly-context retrieval and normalization in backend/src/services/alert_anomaly_context_service.py"
```

## Parallel Example: User Story 2

```bash
Task: "Add contract tests for partial alert-detail responses with single and multiple unavailable components in tests/contract/test_alert_detail_partial_contract.py"
Task: "Add integration tests for single-component and multi-component unavailable flows in tests/integration/test_alert_detail_partial.py"
Task: "Add frontend interaction tests for unavailable-component messaging and reliable-component-only rendering in frontend/tests/test_alert_detail_partial.tsx"
```

## Parallel Example: User Story 3

```bash
Task: "Add contract tests for error-state detail responses and POST /api/v1/alert-details/{alertDetailLoadId}/render-events handling in tests/contract/test_alert_detail_render_events.py"
Task: "Add integration tests for retrieval timeout or service-failure flows plus persisted error outcomes in tests/integration/test_alert_detail_failures.py"
Task: "Add frontend interaction tests for full error-state rendering and render-failure reporting in frontend/tests/test_alert_detail_error.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. Validate the full detail-rendering flow before expanding scope.

### Incremental Delivery

1. Deliver US1 to establish authenticated alert-detail retrieval, normalization, and complete rendering.
2. Add US2 to preserve truthful partial drill-down behavior when supporting components are unavailable.
3. Add US3 to harden retrieval-failure and render-failure handling with explicit terminal error states.
4. Finish with Phase 6 traceability and cross-cutting verification.

### Parallel Team Strategy

1. One engineer can own persistence, auth, and repository work in Phase 2.
2. In US1, backend component-retrieval work and frontend rendering work can proceed in parallel after shared types are in place.
3. After US1, one engineer can implement partial-state behavior for US2 while another implements error-state and render-event handling for US3.

---

## Notes

- The task list preserves UC-12’s requirement to reuse UC-10 and UC-11 alert lineage rather than creating a new alert source of truth.
- Every user story phase is independently testable against the spec and `docs/UC-12-AT.md`.
- All tasks follow the required checklist format with task IDs, optional parallel markers, story labels where required, and exact file paths.
- `tasks.md` remains a planning checklist rather than a place to record execution results.
