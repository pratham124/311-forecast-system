# Implementation Plan: View Public Forecast of 311 Demand by Category

**Branch**: `017-uc-17-public-demand-forecast` | **Date**: 2026-03-13 | **Spec**: [spec.md](/Users/sahmed/Documents/311-forecast-system/specs/017-uc-17-public-forecast-view/spec.md)
**Input**: Feature specification from `/specs/017-uc-17-public-forecast-view/spec.md`

## Summary

Implement UC-17 as an anonymous public forecast portal that reads only the current approved public-safe forecast version from existing forecast lineage, prepares a normalized category-level public view, removes or summarizes any restricted details before response delivery, renders understandable public charts or summaries, and records one correlated trail for retrieval, sanitization, display success, missing-data outcomes, and render failures.

## Technical Context

**Language/Version**: Python 3.11 backend services and TypeScript React frontend  
**Primary Dependencies**: FastAPI, Pydantic-style typed schemas, SQLAlchemy-compatible PostgreSQL access layer, structured logging, React, TypeScript, Tailwind CSS, shared typed API or domain models  
**Storage**: PostgreSQL for reused UC-01 through UC-16 lineage plus UC-17 portal-request observability, sanitization outcomes, normalized public payload records, and final display-event reporting  
**Testing**: pytest for backend unit, integration, and contract coverage; frontend interaction tests for public load, sanitized-success, incomplete-coverage, missing-data, and render-failure states; acceptance tests aligned to [UC-17-AT.md](/Users/sahmed/Documents/311-forecast-system/docs/UC-17-AT.md)  
**Target Platform**: Linux-hosted web application with FastAPI backend and React frontend  
**Project Type**: Web application with backend API plus typed frontend  
**Performance Goals**: Return one normalized public forecast payload fast enough for an interactive public page load, preserve one terminal observable outcome for 100% of successful, sanitized, missing-data, and render-failure flows, and avoid serving contradictory forecast versions within the same request  
**Constraints**: The portal must be accessible without authentication; UC-17 must read only an already approved public-safe forecast version from shared lineage; the response may expose only public-safe category-level fields; incomplete category coverage must be shown explicitly rather than implied as zero demand; missing-data and render-failure paths must show clear error states instead of blank, partial, corrupted, or unsanitized visuals; shared forecast, approval, visualization, and observability entities from UC-01 through UC-16 must be reused rather than redefined  
**Scale/Scope**: One public portal experience for the currently approved public-safe forecast view, one normalized read contract for anonymous clients, and one request-scoped observability flow for retrieval, sanitization, and final display outcomes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- `PASS`: Use-case traceability is preserved. The plan remains bounded to [UC-17.md](/Users/sahmed/Documents/311-forecast-system/docs/UC-17.md), [UC-17-AT.md](/Users/sahmed/Documents/311-forecast-system/docs/UC-17-AT.md), and the accepted clarifications captured in the UC-17 spec.
- `PASS`: Canonical lineage reuse is preserved. UC-17 consumes existing approved forecast lineage and public-safe release context from earlier use cases instead of introducing a second forecast source or duplicating shared entities.
- `PASS`: Layered backend architecture is preserved. Route handlers remain transport-only; forecast selection, sanitization, response preparation, and event recording stay in dedicated services and repositories.
- `PASS`: Typed public contract coverage is preserved. The API exposes one stable public-safe vocabulary for availability status, category coverage, sanitization outcome, and display outcome.
- `PASS`: Security and disclosure constraints are preserved. The portal is anonymous by design, but the backend remains the only component allowed to enforce public-safety filtering before any forecast content is returned.
- `PASS`: Operational safety is preserved. Missing approved data, sanitization actions, incomplete coverage, and render failures remain explicit persisted outcomes rather than UI-only behavior.
- `PASS`: No constitution waiver is required. The design stays within the required Python/FastAPI/PostgreSQL backend and React TypeScript frontend architecture.

## Phase 0 Research Decisions

- Read only the current approved public-safe forecast version rather than generating, approving, or selecting alternate forecast versions inside the portal request.
- Persist one request-scoped public portal record per page-load attempt so retrieval, sanitization, payload preparation, and display reporting share one correlation anchor.
- Normalize one public response shape that can represent successful content, incomplete coverage, unavailable data, and backend-preparation failure without exposing internal forecast metadata.
- Apply public-safety filtering in the backend before any visualization payload is returned, and replace restricted details with sanitized summaries rather than trusting the frontend to hide fields.
- Treat incomplete category coverage as explicit public metadata so omitted categories are never implied to have zero demand.
- Report final client display outcomes separately from backend payload preparation so rendering failures remain traceable after the response is delivered.

## Project Structure

### Documentation (this feature)

```text
specs/017-uc-17-public-forecast-view/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── public-forecast-api.yaml
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

**Structure Decision**: Use the existing FastAPI backend and React frontend split expected by the repository conventions. Public forecast selection, sanitization, and event persistence belong in backend services and repositories, while the frontend remains a typed anonymous consumer of the normalized public-safe contract and reports final display outcomes through a request-scoped endpoint.
If the repository does not yet contain these directories, create them as part of implementation setup rather than changing the architectural split.

## Phase 1 Design Summary

- Reuse the retained forecast lineage and approved-marker concepts from UC-03 and UC-04, plus visualization and observability conventions established through UC-05 and UC-12 through UC-16, without redefining those shared entities.
- Persist one `PublicForecastPortalRequest` per anonymous page-load attempt and one `PublicForecastSanitizationOutcome` capturing whether the retrieved forecast passed as-is, required sanitization, or could not safely be rendered.
- Prepare one `PublicForecastVisualizationPayload` containing only public-safe category-level content, forecast-window labeling, publication timestamp, and explicit coverage status.
- Expose a stable `PublicForecastView` read model that distinguishes `available`, `unavailable`, and `error` states while keeping category summaries and sanitization context normalized.
- Record final display outcomes through a separate `PublicForecastDisplayEvent` path so successful retrieval can be distinguished from client rendering failure.

## Implementation Steps

1. **Define the shared source-of-truth boundary**
   - Treat the current approved public-safe forecast version as the only source for UC-17.
   - Reuse shared forecast lineage and current-marker semantics from earlier use cases rather than introducing a portal-owned forecast store.
   - Keep the portal anonymous and avoid authentication dependencies on the public page-load path.

2. **Assemble the public-safe payload in backend services**
   - Build one service that resolves the currently approved public-safe forecast version, captures the portal request, and loads category-level forecast content for the relevant public window.
   - Normalize retained forecast data into a public response model containing only allowed fields.
   - Ensure one request returns one coherent approved forecast version even if an upstream version changes during processing.

3. **Apply backend sanitization and coverage checks**
   - Evaluate retrieved forecast content against public-safety filtering rules before any response is returned.
   - Remove restricted details and prepare sanitized summaries when needed.
   - Detect partial category availability and mark the response as incomplete rather than implying omitted categories have zero demand.

4. **Persist observability separately from public content**
   - Record one request row per portal load attempt with retrieval and terminal status.
   - Record one sanitization outcome per request, including whether details were removed.
   - Record final display success or render failure after the frontend attempts to show the payload.

5. **Preserve truthful success and failure semantics**
   - Return public forecast content only when a current approved public-safe version is available and successfully sanitized.
   - Return a clear `unavailable` or `error` state instead of blank, partial, corrupted, or unsanitized content when retrieval or preparation fails.
   - If the frontend cannot render the retrieved public payload, report the render failure and treat the visible result as an error state.

6. **Deliver typed contracts and frontend integration**
   - Provide one anonymous `GET` endpoint that returns the current public forecast view.
   - Provide one anonymous request-scoped `POST` endpoint that records final display success or render failure.
   - Keep frontend work limited to loading the public view, rendering normalized category summaries, showing incomplete-coverage and error messaging, and posting display outcomes.

7. **Verify acceptance behavior**
   - Validate successful retrieval, public-safe preparation, understandable category display, and display-success logging.
   - Validate sanitization behavior when restricted details are present upstream.
   - Validate missing-data handling, incomplete-coverage messaging, and render-failure handling.
   - Validate that no unsanitized, partial, empty, or corrupted public visuals are ever shown as successful output.

## Post-Design Constitution Check

- `PASS`: Design artifacts preserve UC-17 and UC-17-AT traceability and keep the anonymous public-access scope explicit.
- `PASS`: The feature remains downstream of canonical forecast lineage and approval state from UC-01 through UC-16 and does not redefine shared source-of-truth entities in `data-model.md`.
- `PASS`: Route handlers stay limited to typed API concerns; source resolution, sanitization, payload normalization, and observability remain isolated in services and repositories.
- `PASS`: The design covers anonymous access, stable typed public contracts, additive persistence, and explicit display-failure observability required by the constitution and the spec.
- `PASS`: Operational safety is preserved because unavailable data, incomplete coverage, sanitization, and render failure remain distinguishable and unsanitized output is never returned.

## Complexity Tracking

No constitution violations or complexity exemptions are required.
