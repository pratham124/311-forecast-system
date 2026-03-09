---

description: "Task list template for Proactive311 feature implementation"

---

# Tasks: [FEATURE NAME]

**Input**: Design documents from `/specs/[###-feature-name]/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Include the tests needed to prove the changed use cases and
acceptance contracts. Do not treat testing as optional when behavior changes.

**Organization**: Tasks are grouped by user story so each story remains
independently implementable and testable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions
- Include `UC-XX` references for tasks that change documented behavior

## Path Conventions

- **Backend**: `backend/app/` and `backend/tests/`
- **Frontend**: `frontend/src/` and `frontend/tests/`
- **Docs**: `docs/UC-XX.md`, `docs/UC-XX-AT.md`, `specs/[###-feature-name]/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize feature scaffolding and traceability before implementation

- [ ] T001 Identify governing `UC-XX.md` and `UC-XX-AT.md` files and update the
      spec references
- [ ] T002 Create or update feature folders and contracts per implementation plan
- [ ] T003 [P] Define or update typed backend/frontend schemas for the feature
- [ ] T004 [P] Add or update configuration keys, environment handling, and
      feature flags if needed

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Complete cross-cutting work that all user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Implement or extend backend route, service, repository, client, and
      pipeline boundaries required by the feature
- [ ] T006 [P] Add authentication/authorization updates for protected behavior
      if applicable
- [ ] T007 [P] Add validation, normalization, and error-handling paths for all
      changed inputs and external integrations
- [ ] T008 [P] Add logging, status reporting, and last-known-good activation
      safeguards for changed workflows
- [ ] T009 Add contract and integration test scaffolding for changed use cases

**Checkpoint**: Architecture, safety controls, and test scaffolding are ready

---

## Phase 3: User Story 1 - [Title] (Priority: P1) 🎯 MVP

**Goal**: [Brief description of what this story delivers]

**Independent Test**: [How to verify this story works on its own]

### Tests for User Story 1

- [ ] T010 [P] [US1] Update `docs/UC-XX.md` and `docs/UC-XX-AT.md` for the
      changed behavior
- [ ] T011 [P] [US1] Add or update backend contract test in
      `backend/tests/contract/`
- [ ] T012 [P] [US1] Add or update backend integration test in
      `backend/tests/integration/`
- [ ] T013 [P] [US1] Add or update frontend integration/component test in
      `frontend/tests/`

### Implementation for User Story 1

- [ ] T014 [P] [US1] Implement backend schemas, services, repositories, clients,
      or pipelines in the planned files
- [ ] T015 [P] [US1] Implement frontend API clients, hooks, feature modules, and
      presentational components in the planned files
- [ ] T016 [US1] Wire thin API routes and typed UI flows without violating
      layering or auth rules
- [ ] T017 [US1] Add observability, failure handling, and last-known-good
      activation logic for this story

**Checkpoint**: User Story 1 is functional and independently testable

---

## Phase 4: User Story 2 - [Title] (Priority: P2)

**Goal**: [Brief description of what this story delivers]

**Independent Test**: [How to verify this story works on its own]

### Tests for User Story 2

- [ ] T018 [P] [US2] Update affected `UC-XX.md` and `UC-XX-AT.md` files
- [ ] T019 [P] [US2] Add or update backend contract/integration tests
- [ ] T020 [P] [US2] Add or update frontend tests where applicable

### Implementation for User Story 2

- [ ] T021 [P] [US2] Implement backend changes in routes, services,
      repositories, clients, or pipelines
- [ ] T022 [P] [US2] Implement frontend feature, API, hook, and component
      changes
- [ ] T023 [US2] Add validation, auth, observability, and activation safeguards

**Checkpoint**: User Stories 1 and 2 both work independently

---

## Phase 5: User Story 3 - [Title] (Priority: P3)

**Goal**: [Brief description of what this story delivers]

**Independent Test**: [How to verify this story works on its own]

### Tests for User Story 3

- [ ] T024 [P] [US3] Update affected `UC-XX.md` and `UC-XX-AT.md` files
- [ ] T025 [P] [US3] Add or update backend and frontend tests required for the
      story

### Implementation for User Story 3

- [ ] T026 [P] [US3] Implement planned backend changes
- [ ] T027 [P] [US3] Implement planned frontend changes
- [ ] T028 [US3] Add cross-cutting safeguards, logging, and rollout validation

**Checkpoint**: All selected user stories are independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improve quality across multiple stories without breaking contracts

- [ ] TXXX [P] Update docs, quickstart, and operational notes
- [ ] TXXX Verify schema compatibility and API contract stability
- [ ] TXXX Verify chronological evaluation, baseline comparison, and quantile
      outputs for forecasting changes
- [ ] TXXX Verify dashboard status visibility, alerts behavior, and last-updated
      metadata where applicable
- [ ] TXXX Run full relevant test suite and record results

---

## Dependencies & Execution Order

### Phase Dependencies

- Setup starts immediately
- Foundational work depends on Setup and blocks all user stories
- User stories begin only after Foundational work is complete
- Polish depends on all selected user stories being complete

### Within Each User Story

- Use-case and acceptance-test updates happen before or with implementation
- Schemas and contracts precede route/component wiring
- Services, repositories, clients, and pipelines precede thin route handlers
- API clients and hooks precede page composition
- Observability and last-known-good safeguards complete before story sign-off

### Parallel Opportunities

- Tasks marked `[P]` may run in parallel when they affect different files
- Backend and frontend work may proceed in parallel after contracts are stable
- Independent user stories may proceed in parallel after Foundational work

## Notes

- Do not generate tasks that place business logic in route handlers or
  presentational components
- Do not omit testing, logging, validation, or rollback/last-known-good work
  when behavior changes
- Prefer small, file-specific tasks that preserve architectural boundaries
