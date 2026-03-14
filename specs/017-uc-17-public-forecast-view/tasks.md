# Tasks: View Public Forecast of 311 Demand by Category

**Input**: Design documents from `/specs/017-uc-17-public-forecast-view/`
**Prerequisites**: [plan.md](/Users/sahmed/Documents/311-forecast-system/specs/017-uc-17-public-forecast-view/plan.md), [spec.md](/Users/sahmed/Documents/311-forecast-system/specs/017-uc-17-public-forecast-view/spec.md), [research.md](/Users/sahmed/Documents/311-forecast-system/specs/017-uc-17-public-forecast-view/research.md), [data-model.md](/Users/sahmed/Documents/311-forecast-system/specs/017-uc-17-public-forecast-view/data-model.md), [public-forecast-api.yaml](/Users/sahmed/Documents/311-forecast-system/specs/017-uc-17-public-forecast-view/contracts/public-forecast-api.yaml), [quickstart.md](/Users/sahmed/Documents/311-forecast-system/specs/017-uc-17-public-forecast-view/quickstart.md)

**Tests**: Include backend unit, integration, and contract coverage plus frontend interaction tests because the quickstart and acceptance suite require validation of successful public display, sanitization, incomplete coverage, missing-data states, and render-failure reporting.

**Organization**: Tasks are grouped by user story so each story can be implemented and verified independently after foundational portal infrastructure is complete.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel when the task touches different files and has no unresolved dependency
- **[Story]**: User story mapping for traceability (`[US1]`, `[US2]`, `[US3]`)
- All task descriptions include exact file paths

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the planned backend, frontend, and test scaffolding for the anonymous public forecast portal.

- [ ] T001 Create the planned backend, frontend, and test directories in `backend/app/api/routes/`, `backend/app/schemas/`, `backend/app/repositories/`, `backend/app/services/`, `backend/app/models/`, `backend/app/core/`, `frontend/src/api/`, `frontend/src/features/public-forecast/components/`, `frontend/src/features/public-forecast/hooks/`, `frontend/src/pages/`, `frontend/src/types/`, `backend/tests/contract/`, `backend/tests/integration/`, `backend/tests/unit/`, and `frontend/tests/`
- [ ] T002 Create backend module scaffolding for the public forecast portal in `backend/app/api/routes/public_forecast.py`, `backend/app/schemas/public_forecast.py`, `backend/app/repositories/public_forecast_repository.py`, `backend/app/services/public_forecast_service.py`, and `backend/app/models/public_forecast_portal.py`
- [ ] T003 [P] Create frontend module scaffolding for anonymous public forecast retrieval and display in `frontend/src/api/publicForecastApi.ts`, `frontend/src/types/publicForecast.ts`, `frontend/src/features/public-forecast/hooks/usePublicForecast.ts`, and `frontend/src/pages/PublicForecastPage.tsx`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build the shared persistence, typed contract, sanitization, coverage, and observability infrastructure required before story-specific behavior.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T004 Create the UC-17 persistence models and canonical vocabularies for `PublicForecastPortalRequest`, `PublicForecastSanitizationOutcome`, `PublicForecastVisualizationPayload`, and `PublicForecastDisplayEvent` in `backend/app/models/public_forecast_portal.py`
- [ ] T005 [P] Create the UC-17 migration for portal requests, sanitization outcomes, payload records, and display events in `backend/app/models/migrations/017_public_forecast_portal.py`
- [ ] T006 [P] Implement repository methods for approved public-forecast lookup, request creation, sanitization persistence, payload persistence, and display-event writes in `backend/app/repositories/public_forecast_repository.py`
- [ ] T007 [P] Define typed request and response schemas for `PublicForecastView` and display-event reporting in `backend/app/schemas/public_forecast.py`
- [ ] T008 [P] Register anonymous public forecast routes in `backend/app/api/routes/__init__.py` and implement any public-route dependency helpers in `backend/app/api/routes/public_forecast.py`
- [ ] T009 [P] Implement structured logging helpers for request start, retrieval success, sanitization outcome, incomplete coverage, missing data, and render failure in `backend/app/core/logging.py`
- [ ] T010 [P] Implement backend helpers for approved-version resolution, public-safety field filtering, and coverage-status derivation in `backend/app/services/public_forecast_source_service.py` and `backend/app/services/public_forecast_sanitization_service.py`
- [ ] T011 [P] Create frontend typed models and API client support for anonymous `GET` and display-event `POST` calls in `frontend/src/types/publicForecast.ts` and `frontend/src/api/publicForecastApi.ts`
- [ ] T012 Implement the shared public forecast orchestration service skeleton and response assembly entrypoint in `backend/app/services/public_forecast_service.py`

**Checkpoint**: Shared persistence, source resolution, sanitization, logging, and typed contracts are ready. User story implementation can begin.

---

## Phase 3: User Story 1 - View approved public demand forecasts by category (Priority: P1) 🎯 MVP

**Goal**: Let an anonymous public resident load the current approved public-safe forecast and view understandable category-level demand summaries with correlated successful display reporting.

**Independent Test**: Open the public portal with approved public-safe forecast data available and verify the backend returns one coherent public-safe forecast view, the UI renders category demand summaries, and correlated retrieval and display-success records are stored.

### Tests for User Story 1

- [ ] T013 [P] [US1] Add contract tests for anonymous `GET /api/v1/public/forecast-categories/current` available responses and schema shape in `backend/tests/contract/test_public_forecast_api.py`
- [ ] T014 [P] [US1] Add backend unit tests for category-summary normalization, approved-version consistency, and available-status view assembly in `backend/tests/unit/test_public_forecast_service.py`
- [ ] T015 [P] [US1] Add integration tests for successful approved public forecast retrieval, payload persistence, and request completion logging in `backend/tests/integration/test_public_forecast_success.py`
- [ ] T016 [P] [US1] Add frontend interaction tests for public page load, loading state, category summary rendering, and render-success reporting in `frontend/tests/public-forecast-success.test.tsx`

### Implementation for User Story 1

- [ ] T017 [P] [US1] Implement approved public-safe forecast selection and immutable request-scoped version binding in `backend/app/services/public_forecast_source_service.py`
- [ ] T018 [P] [US1] Implement category-level public payload normalization with forecast window and publication metadata in `backend/app/services/public_forecast_service.py`
- [ ] T019 [US1] Implement the anonymous `GET /api/v1/public/forecast-categories/current` endpoint with thin request handling and normalized `PublicForecastView` responses in `backend/app/api/routes/public_forecast.py`
- [ ] T020 [P] [US1] Implement the public forecast page content view for category summaries, forecast window labeling, and publication timestamp display in `frontend/src/features/public-forecast/components/PublicForecastView.tsx`
- [ ] T021 [P] [US1] Implement the public forecast loading-state UI in `frontend/src/features/public-forecast/components/PublicForecastLoadingState.tsx`
- [ ] T022 [US1] Implement the public forecast data hook and page composition for anonymous loading, successful-response handling, and render-success submission in `frontend/src/features/public-forecast/hooks/usePublicForecast.ts` and `frontend/src/pages/PublicForecastPage.tsx`

**Checkpoint**: User Story 1 is independently functional and testable.

---

## Phase 4: User Story 2 - Show only public-safe forecast information (Priority: P2)

**Goal**: Ensure the public portal shows only sanitized public-safe category content and explicitly marks incomplete category coverage rather than implying omitted categories have zero demand.

**Independent Test**: Load the portal with forecast data containing restricted details and partial category coverage, then verify the backend removes restricted detail, returns only safe fields, and the UI shows the incomplete-coverage message without fabricating zero-demand categories.

### Tests for User Story 2

- [ ] T023 [P] [US2] Extend contract tests for sanitized available responses and incomplete-coverage payload requirements in `backend/tests/contract/test_public_forecast_api.py`
- [ ] T024 [P] [US2] Add backend unit tests for sanitization-status assignment, removed-detail counting, and incomplete-coverage message derivation in `backend/tests/unit/test_public_forecast_sanitization.py`
- [ ] T025 [P] [US2] Add integration tests for restricted-detail sanitization and partial-category-coverage responses with persisted sanitization outcomes in `backend/tests/integration/test_public_forecast_sanitized.py`
- [ ] T026 [P] [US2] Add frontend interaction tests for sanitized summary rendering and incomplete-coverage messaging in `frontend/tests/public-forecast-sanitized.test.tsx`

### Implementation for User Story 2

- [ ] T027 [US2] Implement restricted-detail filtering, sanitization outcome persistence, and blocked-field exclusion in `backend/app/services/public_forecast_sanitization_service.py` and `backend/app/services/public_forecast_service.py`
- [ ] T028 [P] [US2] Implement incomplete-category-coverage detection and coverage-message persistence in `backend/app/services/public_forecast_service.py` and `backend/app/repositories/public_forecast_repository.py`
- [ ] T029 [P] [US2] Implement UI treatment for sanitization summaries and explicit incomplete-coverage messaging in `frontend/src/features/public-forecast/components/PublicForecastCoverageNotice.tsx`
- [ ] T030 [US2] Integrate sanitized-response handling and coverage notice rendering into `frontend/src/features/public-forecast/hooks/usePublicForecast.ts` and `frontend/src/features/public-forecast/components/PublicForecastView.tsx`

**Checkpoint**: User Stories 1 and 2 are independently functional and testable.

---

## Phase 5: User Story 3 - Handle missing data or rendering failures with a clear public error state (Priority: P3)

**Goal**: Show explicit unavailable or error states when approved forecast data is missing or the client cannot render the prepared payload, while preserving request-scoped observability for both backend and frontend failure paths.

**Independent Test**: Force missing approved forecast data and frontend render failure scenarios, then verify the UI shows clear non-misleading error states, no partial or corrupted visuals are displayed, and the appropriate missing-data or render-failure events are recorded.

### Tests for User Story 3

- [ ] T031 [P] [US3] Extend contract tests for `unavailable` and `error` `PublicForecastView` responses plus `POST /api/v1/public/forecast-categories/{publicForecastRequestId}/display-events` success, `404`, and `422` flows in `backend/tests/contract/test_public_forecast_api.py`
- [ ] T032 [P] [US3] Add backend unit tests for missing-data status mapping, preparation-failure escalation, and display-event validation in `backend/tests/unit/test_public_forecast_error_states.py`
- [ ] T033 [P] [US3] Add integration tests for unavailable approved forecast data, retrieval/preparation failures, and persisted display-event outcomes in `backend/tests/integration/test_public_forecast_failures.py`
- [ ] T034 [P] [US3] Add frontend interaction tests for unavailable-state rendering, error-state rendering, and render-failure reporting in `frontend/tests/public-forecast-error-states.test.tsx`

### Implementation for User Story 3

- [ ] T035 [US3] Implement unavailable-status and error-status response assembly, including missing-data and preparation-failure reason mapping, in `backend/app/services/public_forecast_service.py`
- [ ] T036 [P] [US3] Persist missing-data, preparation-failure, and render-failure terminal outcomes in `backend/app/repositories/public_forecast_repository.py`
- [ ] T037 [US3] Implement `POST /api/v1/public/forecast-categories/{publicForecastRequestId}/display-events` in `backend/app/api/routes/public_forecast.py`
- [ ] T038 [P] [US3] Implement explicit unavailable and error-state UI that withholds blank, partial, stale, corrupted, or unsanitized visuals in `frontend/src/features/public-forecast/components/PublicForecastErrorState.tsx`
- [ ] T039 [US3] Integrate render-failure reporting and terminal error handling into `frontend/src/features/public-forecast/hooks/usePublicForecast.ts` and `frontend/src/pages/PublicForecastPage.tsx`

**Checkpoint**: All user stories are independently functional and reviewable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finish acceptance alignment, contract consistency, and end-to-end verification across success, sanitization, coverage, and failure states.

- [ ] T040 [P] Align quickstart verification steps with delivered available, sanitized, incomplete-coverage, unavailable, and render-failure behavior in `specs/017-uc-17-public-forecast-view/quickstart.md`
- [ ] T041 [P] Align response examples and vocabulary consistency in `specs/017-uc-17-public-forecast-view/contracts/public-forecast-api.yaml`
- [ ] T042 [P] Add correlation-id and terminal-outcome assertions across successful, sanitized, unavailable, and render-failure integration flows in `backend/tests/integration/test_public_forecast_success.py`, `backend/tests/integration/test_public_forecast_sanitized.py`, and `backend/tests/integration/test_public_forecast_failures.py`
- [ ] T043 Run end-to-end readiness validation against [spec.md](/Users/sahmed/Documents/311-forecast-system/specs/017-uc-17-public-forecast-view/spec.md), [UC-17.md](/Users/sahmed/Documents/311-forecast-system/docs/UC-17.md), and [UC-17-AT.md](/Users/sahmed/Documents/311-forecast-system/docs/UC-17-AT.md)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1: Setup**: No dependencies.
- **Phase 2: Foundational**: Depends on Phase 1 and blocks all user story work.
- **Phase 3: US1**: Depends on Phase 2 only and defines the MVP slice.
- **Phase 4: US2**: Depends on Phase 2 and extends the same public retrieval surface delivered in US1.
- **Phase 5: US3**: Depends on Phase 2 and on the shared request/payload pipeline established in US1.
- **Phase 6: Polish**: Depends on the selected user stories being completed.

### User Story Dependencies

- **US1 (P1)**: No dependency on other user stories after Foundational.
- **US2 (P2)**: Depends on US1 public-view assembly and rendering surfaces, but remains independently testable through sanitization and incomplete-coverage scenarios.
- **US3 (P3)**: Depends on US1 request creation and normalized public response handling; it does not depend on US2.

### Within Each User Story

- Contract, unit, integration, and frontend interaction tests should be written before or alongside implementation.
- Backend source resolution and sanitization helpers precede route finalization.
- Backend response mapping precedes frontend integration.
- Frontend display-event reporting closes only after backend request and event persistence are stable.

### Explicit Task Prerequisites

- `T002` depends on `T001`.
- `T003` depends on `T001`.
- `T005` depends on `T004`.
- `T012` depends on `T004`, `T006`, `T007`, `T009`, and `T010`.
- `T017` depends on `T010`.
- `T018` depends on `T012` and `T017`.
- `T019` depends on `T007`, `T008`, and `T018`.
- `T020` depends on `T011`.
- `T022` depends on `T011`, `T019`, `T020`, and `T021`.
- `T027` depends on `T012` and `T017`.
- `T028` depends on `T018` and `T006`.
- `T029` depends on `T020`.
- `T030` depends on `T022` and `T029`.
- `T035` depends on `T012`.
- `T036` depends on `T006` and `T035`.
- `T037` depends on `T007`, `T008`, and `T036`.
- `T038` depends on `T020`.
- `T039` depends on `T022`, `T037`, and `T038`.
- `T043` depends on `T041` and `T042`.

## Parallel Opportunities

- Phase 1: `T003` can run in parallel with `T002` after `T001`.
- Phase 2: `T005` through `T011` can run in parallel after `T004`; `T012` begins once repository, schema, logging, and helper scaffolding are ready.
- US1: `T013`, `T014`, `T015`, and `T016` can run in parallel; `T017` and `T020` can run in parallel after foundations are in place; `T021` can run in parallel with backend service work; `T022` follows route and UI readiness.
- US2: `T023`, `T024`, `T025`, and `T026` can run in parallel; `T028` and `T029` can run in parallel after the sanitization path is stable.
- US3: `T031`, `T032`, `T033`, and `T034` can run in parallel; `T036` and `T038` can run in parallel after failure semantics are defined in `T035`.
- Phase 6: `T040`, `T041`, and `T042` can run in parallel before `T043`.

## Parallel Example: User Story 1

```bash
Task: "Add contract tests for anonymous GET /api/v1/public/forecast-categories/current available responses in backend/tests/contract/test_public_forecast_api.py"
Task: "Add backend unit tests for category-summary normalization and available-status view assembly in backend/tests/unit/test_public_forecast_service.py"
Task: "Add integration tests for successful approved public forecast retrieval and payload persistence in backend/tests/integration/test_public_forecast_success.py"
Task: "Add frontend interaction tests for public page load, category summary rendering, and render-success reporting in frontend/tests/public-forecast-success.test.tsx"
```

```bash
Task: "Implement approved public-safe forecast selection and immutable request-scoped version binding in backend/app/services/public_forecast_source_service.py"
Task: "Implement the public forecast page content view for category summaries and publication metadata in frontend/src/features/public-forecast/components/PublicForecastView.tsx"
Task: "Implement the public forecast loading-state UI in frontend/src/features/public-forecast/components/PublicForecastLoadingState.tsx"
```

## Parallel Example: User Story 2

```bash
Task: "Extend contract tests for sanitized available responses and incomplete-coverage payload requirements in backend/tests/contract/test_public_forecast_api.py"
Task: "Add integration tests for restricted-detail sanitization and partial-category-coverage responses in backend/tests/integration/test_public_forecast_sanitized.py"
Task: "Add frontend interaction tests for sanitized summary rendering and incomplete-coverage messaging in frontend/tests/public-forecast-sanitized.test.tsx"
```

## Parallel Example: User Story 3

```bash
Task: "Extend contract tests for unavailable and error PublicForecastView responses plus POST /api/v1/public/forecast-categories/{publicForecastRequestId}/display-events flows in backend/tests/contract/test_public_forecast_api.py"
Task: "Add integration tests for unavailable approved forecast data and persisted display-event outcomes in backend/tests/integration/test_public_forecast_failures.py"
Task: "Add frontend interaction tests for unavailable-state rendering, error-state rendering, and render-failure reporting in frontend/tests/public-forecast-error-states.test.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. Validate anonymous public loading, category display, and successful display-event capture.

### Incremental Delivery

1. Deliver US1 for basic anonymous forecast retrieval and understandable category display.
2. Add US2 for sanitization and incomplete-coverage truthfulness.
3. Add US3 for missing-data and render-failure handling with explicit error states.
4. Finish with Phase 6 acceptance alignment and readiness validation.

### Parallel Team Strategy

1. One engineer can own persistence, repository, and route foundations in Phase 2.
2. After Phase 2, backend source-resolution work and frontend page rendering work can proceed in parallel for US1.
3. After US1, one engineer can focus on sanitization and coverage behavior for US2 while another handles failure-state and display-event flows for US3.

---

## Notes

- The task list preserves UC-17's requirement to read only the already approved public-safe forecast version from shared upstream lineage.
- Every story phase remains independently testable against [UC-17.md](/Users/sahmed/Documents/311-forecast-system/docs/UC-17.md) and [UC-17-AT.md](/Users/sahmed/Documents/311-forecast-system/docs/UC-17-AT.md).
- All tasks follow the required checklist format with task IDs, optional parallel markers, story labels where required, and exact file paths.
