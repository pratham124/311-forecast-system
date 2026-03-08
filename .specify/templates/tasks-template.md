---

description: "Task list template for feature implementation"
---

# Tasks: [FEATURE NAME]

**Input**: Design documents from `/specs/[###-feature-name]/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Include tests whenever the spec or constitution requires proof of
chronological safety, API contracts, degraded-mode behavior, or regression
protection. Forecasting and alerting changes normally require tests.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app (default)**: `backend/src/`, `frontend/src/`
- **Backend tests**: `backend/tests/unit/`, `backend/tests/integration/`, `backend/tests/contract/`
- **Frontend tests**: `frontend/tests/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume the web app structure - adjust only if the plan explicitly
  approves a different layout

<!-- 
  ============================================================================
  IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.
  
  The /speckit.tasks command MUST replace these with actual tasks based on:
  - User stories from spec.md (with their priorities P1, P2, P3...)
  - Feature requirements from plan.md
  - Entities from data-model.md
  - Endpoints from contracts/
  
  Tasks MUST be organized by user story so each story can be:
  - Implemented independently
  - Tested independently
  - Delivered as an MVP increment
  
  DO NOT keep these sample tasks in the generated tasks.md file.
  ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan
- [ ] T002 Initialize backend and frontend dependencies per constitution
- [ ] T003 [P] Configure linting, formatting, and type-checking tools
- [ ] T004 [P] Establish structured logging and error-reporting foundations

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [ ] T005 Setup PostgreSQL schema and migrations framework
- [ ] T006 [P] Implement FastAPI routing, Pydantic schemas, and middleware structure
- [ ] T007 [P] Establish backend layered modules: core, services, repositories,
  clients, and pipelines
- [ ] T008 [P] Create React API client and shared hooks layer; no direct database
  access allowed
- [ ] T009 Define authoritative ingestion contracts for Edmonton 311, GeoMet, and
  Nager.Date sources used by the feature
- [ ] T010 Create base models/entities, shared frontend types, and artifact
  versioning structures
- [ ] T011 Configure failure handling, logging, and last-known-good promotion rules
- [ ] T012 Setup environment and secrets configuration management
- [ ] T013 [P] Establish token auth, password hashing, and RBAC foundations

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - [Title] (Priority: P1) 🎯 MVP

**Goal**: [Brief description of what this story delivers]

**Independent Test**: [How to verify this story works on its own]

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T014 [P] [US1] Contract test for [endpoint] in backend/tests/contract/test_[name].py
- [ ] T015 [P] [US1] Integration test for [user journey] in backend/tests/integration/test_[name].py
- [ ] T016 [P] [US1] Degraded-mode or fallback-path test covering logging and
  last-known-good behavior
- [ ] T017 [P] [US1] Time-safe evaluation or chronology test when forecasting logic changes
- [ ] T018 [P] [US1] Auth or RBAC test when protected functionality is involved

### Implementation for User Story 1

- [ ] T019 [P] [US1] Create or update backend models/entities in backend/src/models/
- [ ] T020 [P] [US1] Implement repositories or data-access modules in
  backend/src/repositories/
- [ ] T021 [P] [US1] Implement external clients or ingestion modules in
  backend/src/clients/
- [ ] T022 [P] [US1] Implement domain services or pipelines in
  backend/src/services/ or backend/src/pipelines/
- [ ] T023 [US1] Implement or update FastAPI endpoint in backend/src/api/
- [ ] T024 [P] [US1] Implement or update typed frontend API client in
  frontend/src/api/
- [ ] T025 [P] [US1] Implement shared hooks or auth utilities in frontend/src/hooks/
- [ ] T026 [US1] Implement UI flow in frontend/src/features/, frontend/src/components/,
  and frontend/src/pages/ as appropriate
- [ ] T027 [US1] Add validation, failure surfacing, and error handling
- [ ] T028 [US1] Add logging, metrics, and artifact-promotion safeguards

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - [Title] (Priority: P2)

**Goal**: [Brief description of what this story delivers]

**Independent Test**: [How to verify this story works on its own]

### Tests for User Story 2 ⚠️

- [ ] T029 [P] [US2] Contract test for [endpoint] in backend/tests/contract/test_[name].py
- [ ] T030 [P] [US2] Integration test for [user journey] in backend/tests/integration/test_[name].py
- [ ] T031 [P] [US2] Fallback, observability, chronology, or auth test as required
  by the spec

### Implementation for User Story 2

- [ ] T032 [P] [US2] Create or update backend entities in backend/src/models/
- [ ] T033 [P] [US2] Implement repository or client changes in backend/src/repositories/
  or backend/src/clients/
- [ ] T034 [US2] Implement backend service or pipeline logic in backend/src/services/
  or backend/src/pipelines/
- [ ] T035 [US2] Implement FastAPI endpoint or background job in backend/src/api/
  or backend/src/features/
- [ ] T036 [US2] Integrate typed frontend API, hooks, and UI changes in frontend/src/

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - [Title] (Priority: P3)

**Goal**: [Brief description of what this story delivers]

**Independent Test**: [How to verify this story works on its own]

### Tests for User Story 3 ⚠️

- [ ] T037 [P] [US3] Contract test for [endpoint] in backend/tests/contract/test_[name].py
- [ ] T038 [P] [US3] Integration test for [user journey] in backend/tests/integration/test_[name].py
- [ ] T039 [P] [US3] Fallback, observability, chronology, or auth test as required
  by the spec

### Implementation for User Story 3

- [ ] T040 [P] [US3] Create or update backend entities in backend/src/models/
- [ ] T041 [P] [US3] Implement repository or client changes in backend/src/repositories/
  or backend/src/clients/
- [ ] T042 [US3] Implement backend service or pipeline logic in backend/src/services/
  or backend/src/pipelines/
- [ ] T043 [US3] Implement FastAPI endpoint or background job in backend/src/api/
  or backend/src/features/
- [ ] T044 [US3] Integrate typed frontend API, hooks, and UI changes in frontend/src/

**Checkpoint**: All user stories should now be independently functional

---

[Add more user story phases as needed, following the same pattern]

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] TXXX [P] Documentation updates in docs/
- [ ] TXXX Code cleanup and refactoring
- [ ] TXXX Performance optimization across all stories
- [ ] TXXX [P] Additional backend unit tests in backend/tests/unit/
- [ ] TXXX [P] Additional frontend component or integration tests in frontend/tests/
- [ ] TXXX Security hardening
- [ ] TXXX Validate auth flows, token handling, and RBAC behavior
- [ ] TXXX Validate observability dashboards, alerts, and artifact rollback behavior
- [ ] TXXX Run quickstart.md validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Required tests MUST be written and FAIL before implementation
- Models before repositories and services
- Repositories and clients before services and pipelines
- Services and pipelines before endpoints
- Backend API changes before frontend integration
- Shared frontend types and API modules before presentational component wiring
- Core implementation before artifact promotion
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for [endpoint] in backend/tests/contract/test_[name].py"
Task: "Integration test for [user journey] in backend/tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in backend/src/models/[entity1].py"
Task: "Create [Entity2] model in backend/src/models/[entity2].py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Preserve and verify last-known-good behavior before activating new artifacts
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
