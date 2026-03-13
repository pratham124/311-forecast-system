# Tasks: Add Weather Overlay

**Input**: Design documents from `/specs/009-add-weather-overlay/`
**Prerequisites**: [plan.md](/root/311-forecast-system/specs/009-add-weather-overlay/plan.md), [spec.md](/root/311-forecast-system/specs/009-add-weather-overlay/spec.md), [research.md](/root/311-forecast-system/specs/009-add-weather-overlay/research.md), [data-model.md](/root/311-forecast-system/specs/009-add-weather-overlay/data-model.md), [weather-overlay-api.yaml](/root/311-forecast-system/specs/009-add-weather-overlay/contracts/weather-overlay-api.yaml), [quickstart.md](/root/311-forecast-system/specs/009-add-weather-overlay/quickstart.md)

**Tests**: Include contract, integration, and frontend interaction tests because UC-09 is governed by acceptance coverage in `docs/UC-09-AT.md`.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (`[US1]`, `[US2]`, `[US3]`)
- Every task includes an exact file path

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the planned backend, frontend, and test scaffolding for the feature.

- [ ] T001 Create the planned project directories in `backend/src/api/dependencies/`, `backend/src/api/routes/`, `backend/src/api/schemas/`, `backend/src/clients/`, `backend/src/models/`, `backend/src/repositories/`, `backend/src/services/`, `frontend/src/api/`, `frontend/src/components/`, `frontend/src/features/weather-overlay/components/`, `frontend/src/features/weather-overlay/hooks/`, `frontend/src/features/weather-overlay/state/`, `frontend/src/features/forecast-explorer/`, `frontend/src/hooks/`, `frontend/src/pages/`, `frontend/src/types/`, `frontend/src/utils/`, `frontend/tests/weather-overlay/`, `tests/contract/`, `tests/integration/`, and `tests/unit/`
- [ ] T002 Create backend Python project scaffolding in `backend/pyproject.toml`, `backend/src/__init__.py`, and `backend/src/api/__init__.py`
- [ ] T003 [P] Create frontend TypeScript project scaffolding in `frontend/package.json`, `frontend/tsconfig.json`, and `frontend/tailwind.config.ts`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core shared models, services, contracts, and plumbing that every user story depends on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create canonical backend overlay domain models in `backend/src/models/weather_overlay.py`
- [ ] T005 [P] Create backend request and response schema models for overlay `GET` and render-event `POST` in `backend/src/api/schemas/weather_overlay.py`
- [ ] T006 [P] Implement the normalized MSC GeoMet client interface in `backend/src/clients/geomet_client.py`
- [ ] T007 [P] Implement approved geography-to-Edmonton-station alignment rules plus explicit unsupported-geography detection in `backend/src/services/weather_overlay_alignment.py`
- [ ] T008 [P] Create overlay state and observability repository interfaces in `backend/src/repositories/weather_overlay_repository.py`
- [ ] T009 [P] Add authenticated and authorized route dependencies for weather-overlay endpoints in `backend/src/api/dependencies/auth.py`
- [ ] T010 Implement the shared weather overlay orchestration service skeleton in `backend/src/services/weather_overlay_service.py`
- [ ] T011 [P] Create frontend overlay contract types matching the OpenAPI schema in `frontend/src/types/weatherOverlay.ts`
- [ ] T012 [P] Create the frontend API client for overlay `GET` and render-event `POST` calls in `frontend/src/api/weatherOverlayApi.ts`
- [ ] T013 Configure shared overlay error/status mapping for unsupported geography, alignment failure, and other non-visible states in `backend/src/api/errors.py` and `frontend/src/features/weather-overlay/state/statusMessages.ts`

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - View weather context with forecasts (Priority: P1) 🎯 MVP

**Goal**: Let an operational manager enable the optional overlay for a supported selection and see one aligned weather measure on the forecast explorer.

**Independent Test**: Open the forecast explorer for a supported geography and time range, enable the overlay, pick one supported weather measure, and verify the aligned weather layer appears alongside forecast and historical demand.

### Tests for User Story 1

- [ ] T014 [P] [US1] Add contract tests for authenticated `GET /api/v1/forecast-explorer/weather-overlay` visible responses, including `401` and `403` cases, in `tests/contract/test_weather_overlay_get_contract.py`
- [ ] T015 [P] [US1] Add contract tests for invalid weather-overlay `GET` query inputs and schema validation failures in `tests/contract/test_weather_overlay_get_validation.py`
- [ ] T016 [P] [US1] Add backend integration tests for successful supported-selection retrieval and alignment in `tests/integration/test_weather_overlay_visible_flow.py`
- [ ] T017 [P] [US1] Add backend integration tests for successful `POST /render-events` logging and persisted render-success context in `tests/integration/test_weather_overlay_render_event_success.py`
- [ ] T018 [P] [US1] Add frontend interaction tests for enabling the overlay and selecting one measure in `frontend/tests/weather-overlay/WeatherOverlayControls.test.tsx`

### Implementation for User Story 1

- [ ] T019 [US1] Implement successful supported-selection retrieval, alignment, and visible-state assembly in `backend/src/services/weather_overlay_service.py`
- [ ] T020 [US1] Implement schema-validated and auth-protected weather overlay API routes, including the initial successful `POST /render-events` ingestion path, in `backend/src/api/routes/weather_overlay.py`
- [ ] T021 [P] [US1] Build the overlay toggle and single-measure selector in `frontend/src/features/weather-overlay/components/WeatherOverlayControls.tsx`
- [ ] T022 [P] [US1] Build the aligned weather layer renderer in `frontend/src/features/weather-overlay/components/WeatherOverlayLayer.tsx`
- [ ] T023 [US1] Create the overlay data hook that reads the stable response and posts render success in `frontend/src/features/weather-overlay/hooks/useWeatherOverlay.ts`
- [ ] T024 [US1] Integrate the weather overlay controls and layer into the real page entrypoint in `frontend/src/pages/ForecastExplorerPage.tsx`

**Checkpoint**: User Story 1 is fully functional and testable on its own

---

## Phase 4: User Story 2 - Continue analysis when weather data cannot be shown (Priority: P2)

**Goal**: Preserve the base forecast explorer and show explicit non-visible overlay states for missing data, retrieval failure, alignment failure, and render failure.

**Independent Test**: Force missing records, provider retrieval failure, alignment failure, and render failure; verify the weather layer is suppressed, the base forecast explorer remains usable, and the correct status is surfaced.

### Tests for User Story 2

- [ ] T025 [P] [US2] Add contract tests for `unavailable`, `retrieval-failed`, `misaligned`, and `failed-to-render` `WeatherOverlayResponse` states in `tests/contract/test_weather_overlay_non_visible_contract.py`
- [ ] T026 [P] [US2] Add contract tests for authenticated `POST /render-events` success, failure, `401`, `403`, and invalid body handling in `tests/contract/test_weather_overlay_render_event_contract.py`
- [ ] T027 [P] [US2] Add backend integration tests for missing-data, unsupported-geography, and post-match alignment-failure flows in `tests/integration/test_weather_overlay_non_visible_flow.py`
- [ ] T028 [P] [US2] Add backend integration tests for `failed-to-render` render-event persistence and logged failure context in `tests/integration/test_weather_overlay_render_event_failure.py`
- [ ] T029 [P] [US2] Add frontend interaction tests for non-visible status messaging and base-view preservation in `frontend/tests/weather-overlay/WeatherOverlayStatus.test.tsx`

### Implementation for User Story 2

- [ ] T030 [US2] Implement backend classification for `unavailable`, `retrieval-failed`, unsupported-geography, and post-match `misaligned` outcomes in `backend/src/services/weather_overlay_service.py`
- [ ] T031 [P] [US2] Persist failure categories, unsupported-geography diagnostics, and non-visible overlay states in `backend/src/repositories/weather_overlay_repository.py`
- [ ] T032 [US2] Implement schema-validated render-event ingestion and `failed-to-render` state updates in `backend/src/api/routes/weather_overlay.py` and `backend/src/services/weather_overlay_service.py`
- [ ] T033 [P] [US2] Build explicit non-visible overlay status rendering with separate geography-match and alignment-failure messages in `frontend/src/features/weather-overlay/components/WeatherOverlayStatus.tsx`
- [ ] T034 [US2] Integrate non-visible overlay handling so the base explorer stays authoritative in `frontend/src/pages/ForecastExplorerPage.tsx`

**Checkpoint**: User Stories 1 and 2 both work independently, and all required non-visible states preserve the base explorer

---

## Phase 5: User Story 3 - Keep overlay synchronized with user selections (Priority: P3)

**Goal**: Keep overlay state synchronized with disable, measure changes, geography changes, and time-range changes so stale overlay data never remains visible.

**Independent Test**: Enable the overlay, disable it, re-enable it, and change geography/time range while requests are in flight; verify only the latest supported selection can affect the visible overlay.

### Tests for User Story 3

- [ ] T035 [P] [US3] Add backend integration tests for disabled `GET` read-model responses and superseded overlay requests in `tests/integration/test_weather_overlay_supersession_flow.py`
- [ ] T036 [P] [US3] Add frontend interaction tests for toggle and filter synchronization in `frontend/tests/weather-overlay/WeatherOverlaySync.test.tsx`

### Implementation for User Story 3

- [ ] T037 [US3] Implement disabled-state and superseded-request transitions in `backend/src/services/weather_overlay_service.py`
- [ ] T038 [P] [US3] Update repository handling for latest-selection tracking and supersession logging in `backend/src/repositories/weather_overlay_repository.py`
- [ ] T039 [P] [US3] Implement request cancellation and latest-selection handling in `frontend/src/features/weather-overlay/hooks/useWeatherOverlay.ts`
- [ ] T040 [US3] Update overlay controls and the real forecast-explorer page entrypoint to clear stale layers on disable or filter changes in `frontend/src/features/weather-overlay/components/WeatherOverlayControls.tsx` and `frontend/src/pages/ForecastExplorerPage.tsx`
- [ ] T041 [US3] Reject render-event submission for disabled or superseded requests in `frontend/src/api/weatherOverlayApi.ts` and `backend/src/api/routes/weather_overlay.py`

**Checkpoint**: All user stories are independently functional and synchronized correctly

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final hardening, coverage completion, and feature-level verification across stories

- [ ] T042 [P] Add backend unit tests for alignment rules, unsupported-geography handling, and overlay state selection in `tests/unit/test_weather_overlay_service.py`
- [ ] T043 [P] Add frontend component tests for weather-layer readability and render-failure fallback in `frontend/tests/weather-overlay/WeatherOverlayLayer.test.tsx`
- [ ] T044 Add supported-selection latency validation for the 5-second target in `tests/integration/test_weather_overlay_latency.py`
- [ ] T045 Update quickstart verification steps for SC-001 through SC-004, including SC-002 usability validation, in `specs/009-add-weather-overlay/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1: Setup**: No dependencies
- **Phase 2: Foundational**: Depends on Phase 1 and blocks all user stories
- **Phase 3: US1**: Depends on Phase 2 and is the recommended MVP
- **Phase 4: US2**: Depends on Phase 2 and the shared API/service structure established in US1
- **Phase 5: US3**: Depends on Phase 2 and the shared overlay flow established in US1
- **Phase 6: Polish**: Depends on the user stories you choose to complete

### User Story Dependencies

- **US1 (P1)**: No dependency on other user stories after foundational work
- **US2 (P2)**: Reuses the same overlay endpoints and service flow as US1, but remains independently testable through non-visible outcomes
- **US3 (P3)**: Reuses the same overlay control and state flow as US1, but remains independently testable through disable and supersession behavior

### Within Each User Story

- Contract, integration, and frontend interaction tests should be written before implementation for that story
- Backend models/services must exist before route or UI integration
- Frontend hook work should land before final forecast-explorer integration

### Explicit Task Prerequisites

- `T017` depends on `T020` because `T020` introduces the initial successful `POST /render-events` ingestion path that `T017` verifies.
- `T020` depends on `T019` for visible-state assembly before exposing the authenticated `GET` route and initial successful render-event route.
- `T023` depends on `T012` and `T020` so the hook can call the typed API client against the first working overlay and render-event routes.
- `T024` depends on `T021`, `T022`, and `T023` so the real page entrypoint only integrates completed controls, layer rendering, and hook behavior.
- `T030` depends on `T019` because non-visible backend classification extends the supported-selection retrieval and alignment flow built for the visible state.
- `T032` depends on `T020` because failed-to-render ingestion extends the first route and service support for successful render-event ingestion.
- `T034` depends on `T024` and `T033` so non-visible page integration builds on the completed visible-overlay page wiring and explicit status component.
- `T037` depends on `T030` because disabled and superseded transitions extend the backend outcome classification already established for visible and non-visible overlay states.
- `T040` depends on `T039` and `T024` so stale-layer clearing builds on the existing synchronized hook behavior and visible-overlay page integration.
- `T041` depends on `T032`, `T037`, and `T039` so disabled or superseded render-event rejection is layered on top of working render-event ingestion, backend transition handling, and frontend latest-selection logic.
- `T044` should run only after final overlay behavior is stable across US1, US2, and US3 so the latency check measures the completed supported-selection path.

### Parallel Opportunities

- **Setup**: `T003` can run in parallel with `T002` after `T001`
- **Foundational**: `T005`, `T006`, `T007`, `T008`, `T009`, `T011`, and `T012` can run in parallel after `T004`
- **US1**: `T014`, `T015`, `T016`, and `T018` can run in parallel; `T017` runs after `T020`; `T021` and `T022` can run in parallel after the shared types and API client are in place
- **US2**: `T025`, `T026`, `T027`, `T028`, and `T029` can run in parallel; `T031` and `T033` can run in parallel after `T030`
- **US3**: `T035` and `T036` can run in parallel; `T038` and `T039` can run in parallel after `T037`
- **Polish**: `T042`, `T043`, and `T044` can run in parallel

---

## Parallel Example: User Story 1

```bash
Task: "Add contract tests for authenticated GET /api/v1/forecast-explorer/weather-overlay visible responses, including 401 and 403 cases, in tests/contract/test_weather_overlay_get_contract.py"
Task: "Add contract tests for invalid weather-overlay GET query inputs and schema validation failures in tests/contract/test_weather_overlay_get_validation.py"
Task: "Add backend integration tests for successful supported-selection retrieval and alignment in tests/integration/test_weather_overlay_visible_flow.py"
```

```bash
Task: "Build the overlay toggle and single-measure selector in frontend/src/features/weather-overlay/components/WeatherOverlayControls.tsx"
Task: "Build the aligned weather layer renderer in frontend/src/features/weather-overlay/components/WeatherOverlayLayer.tsx"
```

## Parallel Example: User Story 2

```bash
Task: "Add contract tests for unavailable, retrieval-failed, misaligned, and failed-to-render WeatherOverlayResponse states in tests/contract/test_weather_overlay_non_visible_contract.py"
Task: "Add contract tests for authenticated POST /render-events success, failure, 401, 403, and invalid body handling in tests/contract/test_weather_overlay_render_event_contract.py"
Task: "Add backend integration tests for missing-data, unsupported-geography, and post-match alignment-failure flows in tests/integration/test_weather_overlay_non_visible_flow.py"
Task: "Add backend integration tests for failed-to-render render-event persistence and logged failure context in tests/integration/test_weather_overlay_render_event_failure.py"
```

## Parallel Example: User Story 3

```bash
Task: "Add backend integration tests for disabled and superseded overlay requests in tests/integration/test_weather_overlay_supersession_flow.py"
Task: "Add frontend interaction tests for toggle and filter synchronization in frontend/tests/weather-overlay/WeatherOverlaySync.test.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. Validate the US1 independent test before moving on

### Incremental Delivery

1. Complete Setup and Foundational work
2. Deliver US1 for the first visible weather-overlay increment
3. Deliver US2 to make non-visible states explicit and safe
4. Deliver US3 to make disable and supersession behavior robust
5. Finish with cross-cutting polish and verification

### Parallel Team Strategy

1. One engineer completes Phase 1 and coordinates Phase 2 interfaces
2. After Phase 2, backend and frontend work inside each user story can proceed in parallel where tasks are marked `[P]`
3. Keep story-level merges in P1 → P2 → P3 order to reduce conflicts in shared overlay files

---

## Notes

- All tasks use the strict checklist format with IDs, optional `[P]` markers, story labels only in user-story phases, and exact file paths
- The recommended MVP scope is **User Story 1** after Setup and Foundational work
- `disabled` remains a `GET` read-model state only, while `failed-to-render` is implemented through both render-event reporting and later `GET` reads
- The task list now includes explicit auth/authz, schema-validation, render-event, unsupported-geography, latency, and usability coverage required by the analysis recommendations
