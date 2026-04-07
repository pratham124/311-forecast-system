# Tasks: Access User Guide

**Input**: Design documents from `/specs/018-uc-18-user-guide/`
**Prerequisites**: [plan.md](/Users/sahmed/Documents/311-forecast-system/specs/018-uc-18-user-guide/plan.md), [spec.md](/Users/sahmed/Documents/311-forecast-system/specs/018-uc-18-user-guide/spec.md), [research.md](/Users/sahmed/Documents/311-forecast-system/specs/018-uc-18-user-guide/research.md), [data-model.md](/Users/sahmed/Documents/311-forecast-system/specs/018-uc-18-user-guide/data-model.md), [contracts/user-guide-api.yaml](/Users/sahmed/Documents/311-forecast-system/specs/018-uc-18-user-guide/contracts/user-guide-api.yaml)

**Tests**: Include contract, integration, and frontend interaction coverage because the plan and quickstart explicitly require them.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g. `US1`, `US2`, `US3`)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the feature scaffolding required by all user stories.

- [X] T001 Create or validate the backend application structure in `backend/app/`
- [X] T002 [P] Create or validate the frontend application structure in `frontend/src/`
- [X] T003 [P] Create the user-guide API route module in `backend/app/api/routes/user_guide.py`
- [X] T004 [P] Create backend schemas for user-guide contracts in `backend/app/schemas/user_guide.py`
- [X] T005 [P] Create frontend API client scaffolding for guide requests in `frontend/src/api/userGuide.ts`
- [X] T006 [P] Create the frontend feature barrel for the user guide in `frontend/src/features/user-guide/index.ts`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before any user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T007 Create guide access and render-outcome persistence models in `backend/app/models/user_guide.py`
- [X] T008 [P] Create repository methods for current guide lookup and guide event persistence in `backend/app/repositories/user_guide_repository.py`
- [X] T009 [P] Create backend service scaffolding for guide retrieval and outcome recording in `backend/app/services/user_guide_service.py`
- [X] T010 [P] Add structured logging and failure-category helpers for UC-18 in `backend/app/core/logging.py`
- [X] T011 [P] Add shared frontend types for guide payloads and render outcomes in `frontend/src/types/userGuide.ts`
- [X] T012 [P] Register authenticated user-guide routes in `backend/app/api/routes/__init__.py`
- [X] T013 [P] Add request/response and persistence-schema validation coverage for UC-18 models and contracts in `backend/tests/unit/test_user_guide_schema_validation.py`

**Checkpoint**: Foundation ready. User story work can begin.

---

## Phase 3: User Story 1 - Open the user guide (Priority: P1) 🎯 MVP

**Goal**: Let any signed-in user open the current published guide from the single MVP host surface and see readable guide content.

**Independent Test**: From the single MVP host surface, a signed-in user opens the guide and receives the current published content with the guide title, ordered section labels, and legible body content plus a successful access record.

### Tests for User Story 1

- [X] T014 [P] [US1] Add contract tests for `GET /api/v1/help/user-guide` success and auth failures in `backend/tests/contract/test_user_guide_api.py`
- [X] T015 [P] [US1] Add backend integration tests for guide retrieval, loading-state transition, and successful access-event logging in `backend/tests/integration/test_user_guide_open.py`
- [X] T016 [P] [US1] Add frontend interaction tests for opening, loading, and displaying the guide in `frontend/tests/user-guide-open.test.tsx`
- [X] T017 [P] [US1] Review and update UC-18 acceptance-test alignment in `docs/UC-18-AT.md`

### Implementation for User Story 1

- [X] T018 [US1] Implement current published guide retrieval and successful access-event creation in `backend/app/services/user_guide_service.py`
- [X] T019 [US1] Implement `GET /api/v1/help/user-guide` with signed-in access enforcement and normalized `UserGuideView` responses in `backend/app/api/routes/user_guide.py` (depends on T018, T012)
- [X] T020 [P] [US1] Implement frontend query and response mapping for guide open requests in `frontend/src/api/userGuide.ts` (depends on T019)
- [X] T021 [P] [US1] Implement guide viewer UI for title, ordered section labels, readable body content, and metadata display in `frontend/src/features/user-guide/UserGuidePanel.tsx`
- [X] T022 [P] [US1] Implement the guide loading-state UI in `frontend/src/features/user-guide/UserGuideLoadingState.tsx`
- [X] T023 [US1] Integrate the single MVP help-entry host surface with the guide panel in `frontend/src/pages/UserGuideHostPage.tsx` (depends on T020, T021, T022)

**Checkpoint**: User Story 1 is independently functional and testable.

---

## Phase 4: User Story 2 - Navigate guide sections (Priority: P2)

**Goal**: Let users move between available sections or pages without reopening the guide and preserve readability during navigation.

**Independent Test**: With the guide already open, a user can move to another section or page and back again using the provided navigation controls without reopening the guide or losing readability.

### Tests for User Story 2

- [X] T024 [P] [US2] Extend backend integration coverage for ordered section metadata, repeat navigation stability, and section-transition timing in `backend/tests/integration/test_user_guide_navigation.py`
- [X] T025 [P] [US2] Add frontend interaction tests for section and page navigation in `frontend/tests/user-guide-navigation.test.tsx`
- [X] T029 [P] [US2] Add backend and frontend timing verification for guide open and section navigation latency in `backend/tests/integration/test_user_guide_performance.py` (depends on T026, T028)

### Implementation for User Story 2

- [X] T026 [US2] Implement ordered section and page normalization, including anchors and labels, in `backend/app/services/user_guide_service.py`
- [X] T027 [P] [US2] Implement section navigation UI and current-section state management in `frontend/src/features/user-guide/UserGuideNavigation.tsx`
- [X] T028 [US2] Connect navigation state to the guide viewer so section changes preserve readability and availability in `frontend/src/features/user-guide/UserGuidePanel.tsx` (depends on T021, T027, T026)

**Checkpoint**: User Stories 1 and 2 are both independently functional and testable.

---

## Phase 5: User Story 3 - Receive a clear failure state (Priority: P3)

**Goal**: Show explicit unavailable or render-error states and record retrieval and rendering failures without exposing blank, stale, partial, or corrupted guide content.

**Independent Test**: When retrieval fails or the client cannot render returned guide content, the user sees a clear error state and the appropriate failure outcome is recorded.

### Tests for User Story 3

- [X] T030 [P] [US3] Extend contract tests for unavailable, render-event, and not-found flows in `backend/tests/contract/test_user_guide_api.py`
- [X] T031 [P] [US3] Add backend integration tests for retrieval-failure and render-failure event recording in `backend/tests/integration/test_user_guide_failures.py`
- [X] T032 [P] [US3] Add frontend interaction tests for unavailable and render-error states in `frontend/tests/user-guide-error-states.test.tsx`

### Implementation for User Story 3

- [X] T033 [US3] Implement retrieval-failure and render-failure outcome handling in `backend/app/services/user_guide_service.py`
- [X] T034 [US3] Implement `POST /api/v1/help/user-guide/{guideAccessEventId}/render-events` in `backend/app/api/routes/user_guide.py` (depends on T033, T018, T019)
- [X] T035 [P] [US3] Implement frontend render-outcome reporting and failure-message mapping in `frontend/src/api/userGuide.ts` (depends on T034)
- [X] T036 [P] [US3] Implement explicit unavailable and error-state UI that withholds blank, stale, partial, and corrupted content in `frontend/src/features/user-guide/UserGuideErrorState.tsx`
- [X] T037 [US3] Integrate failure-state handling and render reporting into the guide panel flow in `frontend/src/features/user-guide/UserGuidePanel.tsx` (depends on T035, T036, T021)

**Checkpoint**: All user stories are independently functional and testable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories.

- [X] T038 [P] Update the quickstart verification steps and implementation notes for delivered behavior in `specs/018-uc-18-user-guide/quickstart.md`
- [X] T039 [P] Add unit coverage for guide outcome vocabulary, failure-message normalization, and section ordering helpers in `backend/tests/unit/test_user_guide_service.py`
- [X] T040 [P] Add frontend feature-level smoke coverage for full guide lifecycle states in `frontend/tests/user-guide-lifecycle.test.tsx` (depends on T023, T028, T037)
- [X] T041 [P] Add post-release measurement instrumentation for support-request trend tracking in `backend/app/core/metrics.py`
- [X] T042 Run the UC-18 quickstart validation after completed shipped-story work and relevant validation tasks, then document any follow-up findings in `specs/018-uc-18-user-guide/tasks.md`

## Validation Notes

- 2026-04-06: Ran `backend/.venv/bin/python -m pytest backend/tests/unit/test_user_guide_schema_validation.py backend/tests/unit/test_user_guide_service.py backend/tests/contract/test_user_guide_api.py backend/tests/integration/test_user_guide_open.py backend/tests/integration/test_user_guide_navigation.py backend/tests/integration/test_user_guide_performance.py backend/tests/integration/test_user_guide_failures.py` and all 14 tests passed.
- 2026-04-06: Ran `npm test -- --run tests/user-guide-open.test.tsx tests/user-guide-navigation.test.tsx tests/user-guide-error-states.test.tsx tests/user-guide-lifecycle.test.tsx` from `frontend/` and all 5 tests passed.
- Follow-up note: the backend currently uses a normalized in-repo current-guide source with persistent access and render-outcome records. If the product later adds external documentation storage, `UserGuideRepository.get_current_guide()` is the seam to replace.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1: Setup**: No dependencies.
- **Phase 2: Foundational**: Depends on Phase 1 and blocks all user stories.
- **Phase 3: User Story 1**: Depends on Phase 2 only and is the MVP slice.
- **Phase 4: User Story 2**: Depends on Phase 2 and reuses the guide payload delivered in US1.
- **Phase 5: User Story 3**: Depends on Phase 2 and extends the same backend and frontend surfaces with failure semantics.
- **Phase 6: Polish**: Depends on the user stories you choose to ship.

### User Story Dependencies

- **US1 (P1)**: No dependency on other user stories.
- **US2 (P2)**: Depends on the guide-open path from US1 being available, but remains independently testable once that shared surface exists.
- **US3 (P3)**: Depends on the guide-open path from US1 for retrieval and on the shared viewer surface for render-failure reporting, but remains independently testable with forced failure inputs.

### Within Each User Story

- Contract, integration, and frontend interaction tests should be written before or alongside implementation.
- Backend service changes precede route completion.
- Backend response mapping precedes frontend integration.
- Story-specific UI integration comes after data and API surfaces are stable.
- Explicit task dependency notes override generic sequencing when present.

### Parallel Opportunities

- `T002` through `T006` can run in parallel after `T001`.
- `T008` through `T013` can run in parallel after `T007`.
- In **US1**, `T014`, `T015`, `T016`, and `T017` can run in parallel; `T021` and `T022` can run in parallel after `T019`; `T020` must wait for `T019`; `T023` must wait for `T020`, `T021`, and `T022`.
- In **US2**, `T024` and `T025` can run in parallel; `T027` can run in parallel with backend work in `T026`; `T028` must wait for `T021`, `T027`, and `T026`; `T029` must wait for `T026` and `T028`.
- In **US3**, `T030`, `T031`, and `T032` can run in parallel; `T034` must wait for `T033`, `T018`, and `T019`; `T035` and `T036` can run in parallel after `T034`; `T037` must wait for `T035`, `T036`, and `T021`.
- In **Polish**, `T038`, `T039`, `T040`, and `T041` can run in parallel before `T042`.

---

## Parallel Example: User Story 1

```bash
# Launch US1 test authoring in parallel:
Task: "Add contract tests for GET /api/v1/help/user-guide success and auth failures in backend/tests/contract/test_user_guide_api.py"
Task: "Add backend integration tests for guide retrieval, loading-state transition, and successful access-event logging in backend/tests/integration/test_user_guide_open.py"
Task: "Add frontend interaction tests for opening, loading, and displaying the guide in frontend/tests/user-guide-open.test.tsx"

# Launch US1 implementation tasks that touch different files in parallel:
Task: "Implement frontend query and response mapping for guide open requests in frontend/src/api/userGuide.ts"
Task: "Implement guide viewer UI for title, ordered section labels, readable body content, and metadata display in frontend/src/features/user-guide/UserGuidePanel.tsx"
Task: "Implement the guide loading-state UI in frontend/src/features/user-guide/UserGuideLoadingState.tsx"
```

## Parallel Example: User Story 2

```bash
# Launch US2 validation work in parallel:
Task: "Extend backend integration coverage for ordered section metadata and repeat navigation stability in backend/tests/integration/test_user_guide_navigation.py"
Task: "Add frontend interaction tests for section and page navigation in frontend/tests/user-guide-navigation.test.tsx"

# Launch US2 implementation tasks that touch different files in parallel:
Task: "Implement ordered section and page normalization, including anchors and labels, in backend/app/services/user_guide_service.py"
Task: "Implement section navigation UI and current-section state management in frontend/src/features/user-guide/UserGuideNavigation.tsx"
Task: "Add backend and frontend timing verification for guide open and section navigation latency in backend/tests/integration/test_user_guide_performance.py"
```

## Parallel Example: User Story 3

```bash
# Launch US3 test authoring in parallel:
Task: "Extend contract tests for unavailable, render-event, and not-found flows in backend/tests/contract/test_user_guide_api.py"
Task: "Add backend integration tests for retrieval-failure and render-failure event recording in backend/tests/integration/test_user_guide_failures.py"
Task: "Add frontend interaction tests for unavailable and render-error states in frontend/tests/user-guide-error-states.test.tsx"

# Launch US3 implementation tasks that touch different files in parallel:
Task: "Implement frontend render-outcome reporting and failure-message mapping in frontend/src/api/userGuide.ts"
Task: "Implement explicit unavailable and error-state UI that withholds blank, stale, partial, and corrupted content in frontend/src/features/user-guide/UserGuideErrorState.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. Validate that a signed-in user can open the current published guide from the MVP host surface, see the loading state, and then see readable content with a successful access event.
5. Stop here for an MVP demo if needed.

### Incremental Delivery

1. Deliver **US1** for basic guide access.
2. Add **US2** for section and page navigation without reopening the guide.
3. Add **US3** for retrieval and render failure handling plus observability.
4. Finish with cross-cutting test and quickstart validation tasks.

### Parallel Team Strategy

1. One engineer completes Setup and Foundational tasks.
2. After Phase 2:
   - Engineer A focuses on backend user-guide service and routes.
   - Engineer B focuses on frontend guide panel and navigation UI.
   - Engineer C focuses on contract, integration, and frontend interaction tests.
3. Converge in each story phase at the route-to-UI integration tasks.

---

## Notes

- All tasks follow the required checklist format with checkbox, task ID, optional `[P]`, required `[US#]` labels for story phases, and exact file paths.
- The suggested MVP scope is **User Story 1** only.
- Story phases are ordered by priority and remain independently testable.
