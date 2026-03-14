# Implementation Plan: Access User Guide

**Branch**: `013-access-user-guide` | **Date**: 2026-03-13 | **Spec**: [spec.md](/root/311-forecast-system/specs/013-access-user-guide/spec.md)
**Input**: Feature specification from `/specs/013-access-user-guide/spec.md`

## Summary

Implement UC-18 as an authenticated help flow that lets any signed-in user open the current published user guide from one MVP host surface in the product interface, navigate available sections or pages in a readable instructional format, and receive explicit unavailable or render-error states when the guide cannot be shown. The design keeps guide retrieval, navigation-state preparation, loading-state semantics, and access-event recording in dedicated backend services and repositories, exposes one stable typed contract for loading guide content plus one render-outcome contract for observability, and preserves clear distinction between retrieval failures and client-side display failures.

## Technical Context

**Language/Version**: Python 3.11 backend services and TypeScript React frontend  
**Primary Dependencies**: FastAPI, Pydantic-style typed schemas, SQLAlchemy-compatible PostgreSQL access layer, structured logging, React, TypeScript, Tailwind CSS, shared typed API/domain models, JWT authentication, role-based authorization dependencies  
**Storage**: PostgreSQL for guide access and failure observability records plus references to the current published user guide content; guide body content may be sourced from the platform’s documentation storage rather than duplicated into separate per-access snapshots  
**Testing**: pytest for backend unit, integration, and contract coverage; frontend interaction tests for guide load, section navigation, unavailable, and render-error states; acceptance tests aligned to [UC-18-AT.md](/root/311-forecast-system/docs/UC-18-AT.md)  
**Target Platform**: Linux-hosted web application with FastAPI backend and React frontend  
**Project Type**: Web application with backend API plus typed frontend  
**Performance Goals**: Reach readable guide content within 10 seconds for at least 95% of successful guide opens, complete section-to-section navigation within 2 seconds without reopening the guide, and record a terminal outcome for 100% of guide access attempts  
**Constraints**: Must satisfy [UC-18.md](/root/311-forecast-system/docs/UC-18.md) and [UC-18-AT.md](/root/311-forecast-system/docs/UC-18-AT.md); must allow any signed-in user to access the guide; must provide a help or user guide entry point on one MVP host surface; must retrieve only the current published guide content; must show a loading state before either guide content or an explicit error state appears; must preserve readability and availability while users navigate sections or pages; must show clear unavailable states instead of blank, stale, partial, or corrupted guide content; must log successful access, retrieval failures, and rendering failures; must keep FastAPI routes thin, guide retrieval and event recording in services, persistence in repositories, and frontend rendering in typed feature modules; must not expose raw documentation storage internals or bypass backend authentication  
**Scale/Scope**: One user-guide experience on one authenticated MVP host surface, one normalized guide-read contract, one render-outcome contract for observability, and access-event history sufficient for operational review and support analysis

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- `PASS`: Use-case traceability is preserved. The plan remains bounded to [UC-18.md](/root/311-forecast-system/docs/UC-18.md), [UC-18-AT.md](/root/311-forecast-system/docs/UC-18-AT.md), and the accepted clarification captured in the feature spec.
- `PASS`: Canonical Edmonton forecasting constraints are not impacted. UC-18 is a product-help feature and does not alter governed 311, weather, holiday, or forecast lineage.
- `PASS`: Layered backend architecture is preserved. Route handlers remain transport-only; guide retrieval, navigation payload preparation, and observability recording stay in dedicated services and repositories.
- `PASS`: Typed frontend modularity and secure access are preserved. The guide is delivered through authenticated backend APIs and consumed by typed frontend modules rather than direct storage access.
- `PASS`: Operational safety and observability are preserved. Retrieval failures, display failures, and successful guide access remain explicit logged outcomes; unavailable content is never misrepresented as successfully loaded content.
- `PASS`: No constitution waiver is required. The design stays within the required Python/FastAPI/PostgreSQL backend and React TypeScript frontend architecture.

## Phase 0 Research Decisions

- Restrict guide access to signed-in users only; no anonymous or public guide surface is required for UC-18.
- Retrieve the current published guide at request time rather than exposing version selection or historical-guide browsing.
- Normalize guide content, section navigation metadata, and outcome status into one backend response so the frontend does not interpret raw documentation source formats.
- Distinguish retrieval failure from client render failure through separate observable outcomes rather than merging them into one generic error.
- Record one guide-access event per open attempt and allow a separate render-outcome report when the content was retrieved but could not be displayed.
- Reuse the platform’s existing authenticated web-application structure with backend API routes, service modules, repositories, and typed frontend feature modules.
- Treat minimum required logging fields as specification-level obligations, and leave additional observability fields as implementation-level choices.

## Project Structure

### Documentation (this feature)

```text
specs/013-access-user-guide/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── user-guide-api.yaml
└── spec.md
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── api/
│   │   └── routes/
│   ├── core/
│   ├── repositories/
│   ├── schemas/
│   └── services/
└── tests/
    ├── contract/
    ├── integration/
    └── unit/

frontend/
└── src/
    ├── api/
    ├── components/
    ├── features/
    ├── hooks/
    ├── pages/
    ├── types/
    └── utils/
```

**Structure Decision**: Use the constitution-mandated backend/frontend split. Guide retrieval, access-event persistence, and failure logging belong in backend services and repositories, while guide presentation and navigation remain in typed frontend feature modules consuming normalized backend contracts.
If the repository does not yet contain those directories, create or validate the target structure as part of setup before story implementation begins.

## Phase 1 Design Summary

- Reuse one current published `UserGuideContent` source of truth and add only UC-18-specific access and failure observability records rather than duplicating the guide body per request.
- Normalize guide title, instructional body, section metadata, status messaging, and availability metadata into one backend read model that can support success and error states without exposing source-storage details.
- Persist one guide-access event for each attempt, capturing actor, entry point, request time, outcome, and failure category when relevant.
- Use a dedicated render-outcome reporting path so the system can distinguish retrieval success from client rendering failure.
- Keep section or page navigation within one loaded guide session and ensure the contract exposes enough ordered navigation metadata for the frontend to preserve readability during movement between sections.
- Treat loading-state behavior and latency measurement as first-class parts of the guide-open and navigation experience.

## Implementation Steps

1. **Define the canonical guide source and access scope**
   - Treat the current published guide as the only content source for UC-18.
   - Require authenticated access for every guide retrieval and render-outcome reporting path.
   - Support guide entry from one MVP host surface where the help or user guide option is exposed.

2. **Assemble the guide payload in dedicated backend services**
   - Build one guide-loading service that resolves the current published guide, prepares readable content and section metadata, records the initial access attempt, and returns a loading state before terminal success or failure.
   - Normalize source content into stable typed response shapes before returning it to the frontend.
   - Keep all route handlers limited to auth, request parsing, and response shaping.

3. **Persist observability separately from guide content**
   - Record one guide-access event per open attempt with timestamp, actor, entry point, and terminal outcome.
   - Record retrieval failures and display failures with explicit failure categories and user-visible status messaging.
   - Avoid duplicating full guide content in per-access records unless future retention requirements demand it.

4. **Preserve truthful success and failure semantics**
   - Return readable instructional content and section navigation metadata only when guide retrieval succeeds.
   - Return a clear unavailable state instead of blank, stale, or partial guide content when retrieval fails.
   - If the frontend cannot render the retrieved guide, report the render failure and treat the user-visible outcome as an error.

5. **Keep navigation bounded to available guide sections or pages**
   - Expose ordered section or page identifiers, labels, and anchor metadata required for consistent navigation.
   - Preserve guide context while the user moves between sections without forcing a second retrieval for basic in-session movement.
   - Ensure unreadable, corrupted, or incomplete content never appears during navigation transitions.

6. **Deliver typed contracts and frontend integration**
   - Provide one authenticated `GET` endpoint that returns the current guide payload.
   - Provide one authenticated `POST` endpoint that records final render success or render failure for the retrieved guide session.
   - Keep frontend work limited to opening the guide, rendering normalized sections, handling loading and explicit error states, and reporting render outcomes.

7. **Verify acceptance behavior**
   - Validate successful guide retrieval, readable display, and section navigation.
   - Validate loading-state behavior and timing expectations for guide open and section navigation.
   - Validate logging for successful access, documentation-unavailable failures, and rendering failures.
   - Validate that blank, stale, partial, and corrupted content are never shown as successful guide loads.

## Post-Design Constitution Check

- `PASS`: Design artifacts preserve UC-18 and UC-18-AT traceability and keep the accepted signed-in-user access scope explicit.
- `PASS`: The feature remains isolated from canonical Edmonton data and forecasting pipelines, so no data-lineage or time-safety obligations are violated.
- `PASS`: Route handlers are limited to typed API concerns; guide retrieval, normalization, and observability remain isolated in service and repository layers.
- `PASS`: The design covers authenticated access, stable typed contracts, and explicit failure observability required by the constitution.
- `PASS`: Operational safety is preserved because retrieval failures and render failures remain distinguishable, and unavailable or corrupted guide content is never presented as successful output.

## Complexity Tracking

No constitution violations or complexity exemptions are required.
