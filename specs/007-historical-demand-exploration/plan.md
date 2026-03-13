# Implementation Plan: Explore Historical 311 Demand Data

**Branch**: `007-historical-demand-exploration` | **Date**: 2026-03-13 | **Spec**: [spec.md](/home/asiad/ece493/311-forecast-system/specs/007-historical-demand-exploration/spec.md)
**Input**: Feature specification from `/specs/007-historical-demand-exploration/spec.md`

## Summary

Implement UC-07 as a historical-demand exploration feature that lets City Planners retrieve and review historical 311 demand patterns by service category, time range, and supported reliable geography levels. The feature must satisfy `docs/UC-07.md` and `docs/UC-07-AT.md`, reuse the approved historical dataset lineage from UC-02, provide a typed exploration contract for filtered retrieval and display, warn before exceptionally large requests, preserve filters when a warned request is declined, record no-data and failure outcomes, and avoid presenting incomplete or misleading historical information when retrieval or rendering cannot complete.

## Technical Context

**Language/Version**: Python 3.11 for backend services and TypeScript for the React frontend  
**Primary Dependencies**: FastAPI, Pydantic-style typed schemas, SQLAlchemy-compatible PostgreSQL access layer, structured logging, React, TypeScript, Tailwind CSS, shared typed API/domain models, and a reusable historical-data visualization layer for charts and tables  
**Storage**: PostgreSQL for reused UC-01 and UC-02 lineage plus historical analysis outcome records, saved filter context, and migration-managed schema history  
**Testing**: pytest for backend unit, integration, and contract coverage plus frontend component and interaction tests aligned to UC-07 acceptance behavior  
**Target Platform**: Linux-hosted backend API with a browser-based React analysis interface for City Planners  
**Project Type**: web application with backend API and typed frontend analysis interface  
**Performance Goals**: Deliver matching historical demand results within 10 seconds for at least 95% of valid requests with available data; show a warning before 100% of exceptionally large requests are executed; record terminal no-data, success, and error outcomes for 100% of requests  
**Constraints**: Must satisfy `docs/UC-07.md`; must reuse approved historical lineage from UC-02 rather than introducing a separate historical store; must keep FastAPI routes thin, business logic in services, persistence in repositories, and frontend rendering in typed feature modules; must support only geography levels that are already available and consistently reliable in stored historical data; must preserve filter context in warning, no-data, and error states; must never display misleading or partial historical results; must not expose raw source rows, secrets, or unstable third-party formats directly to the frontend  
**Scale/Scope**: One historical-demand exploration interface, one typed filtered-analysis API, support for service category, time range, and reliable geography filters, retained analysis outcome history, and acceptance coverage for success, high-volume warning, no-data, retrieval-failure, and render-failure outcomes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Use-case traceability**: PASS. The plan remains anchored to [UC-07](/home/asiad/ece493/311-forecast-system/docs/UC-07.md), and the feature behavior stays within the historical-demand exploration scope defined there.
- **Acceptance traceability**: PASS. The design remains aligned to [UC-07-AT](/home/asiad/ece493/311-forecast-system/docs/UC-07-AT.md), including warned large-request handling, no-data behavior, and failure visibility.
- **Canonical data-source usage**: PASS. UC-07 reuses approved Edmonton 311 cleaned-data lineage from UC-02 as the historical source of truth rather than introducing alternate demand sources.
- **Layered backend architecture**: PASS. Historical query handling, aggregation, warning logic, and outcome recording remain in services and repositories, while route handlers stay limited to transport and auth concerns.
- **Typed frontend modularity and secure access**: PASS. UC-07 is implemented as a typed React frontend consuming only normalized backend contracts, with backend-enforced access control for historical analysis retrieval.
- **Operational safety / last-known-good and clarity guarantees**: PASS. No-data and error states prevent misleading partial output, and request outcomes are recorded for diagnosis and monitoring.
- **Historical-view obligations**: PASS. The plan provides filter selection, result visualization, warning behavior, error/no-data states, and recorded analysis outcomes consistent with the governing use case.

**Post-Design Check**: PASS. The research, data model, quickstart, and analysis contract preserve UC-07 traceability, reuse canonical historical-data lineage, keep backend/frontend layering explicit, and retain clear no-data and error-state behavior after design.

## Project Structure

### Documentation (this feature)

```text
specs/007-historical-demand-exploration/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── historical-demand-api.yaml
└── tasks.md
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

**Structure Decision**: Use the repository’s backend/frontend split because UC-07 includes both a typed backend filtered-analysis contract and a planner-facing frontend exploration interface. Reuse existing historical lineage in `backend/`, and confine visualization and filter interaction to `frontend/` without direct storage access from the client.

## Phase 0 Research Summary

- Confirmed UC-07 should reuse the approved cleaned dataset lineage from UC-02 as the canonical historical source rather than introducing a separate historical-analysis dataset lifecycle.
- Confirmed geography filtering should be limited to the levels already available and consistently reliable in stored historical data.
- Confirmed high-volume handling should warn before retrieval instead of silently degrading or executing immediately.
- Confirmed the analysis interface should preserve selected filter context when showing warnings, no-data messages, and error states.
- Confirmed no-data, retrieval-failure, and rendering-failure outcomes require explicit recorded analysis outcomes rather than only frontend messaging.
- Confirmed a single normalized historical-analysis response can support either chart, table, or combined views without exposing raw source rows directly to frontend consumers.

## Phase 1 Design Summary

- Reuse UC-01 and UC-02 lineage entities as immutable historical-data inputs and add only UC-07-specific records for analysis requests and their outcomes.
- Build one normalized historical-demand response that includes filter metadata, aggregation granularity, result series or table rows, warning metadata, and terminal status information.
- Persist historical-analysis outcomes separately from dataset lineage so planner exploration success, warning acknowledgments, no-data cases, and failures remain queryable without mutating upstream data state.
- Restrict geography filters to supported reliable geography levels and represent unsupported geography requests as unavailable filter options rather than zero-demand results.
- Keep frontend rendering in typed historical-analysis modules that consume only the normalized backend contract and surface clear no-data or error states when required.

## Implementation Steps

1. **Resolve approved historical lineage**
   - Read the approved cleaned dataset marker from UC-02 as the authoritative source for historical analysis.
   - Build filterable historical query inputs from approved historical records only.
   - Keep approved dataset lineage distinct from analysis-outcome persistence.

2. **Gate analysis access through backend-authenticated contracts**
   - Require authenticated access for historical-analysis retrieval.
   - Keep authorization checks in backend dependencies and services.
   - Prevent the frontend from directly querying persistence or third-party sources.

3. **Assemble normalized historical-analysis responses in backend services**
   - Build one analysis service that accepts selected filters, resolves matching historical data, aggregates it, and returns a stable response shape.
   - Keep FastAPI routes transport-only and move warning, no-data, and error-state decisions into service modules.
   - Normalize response shapes into stable typed schemas before they reach the frontend.

4. **Preserve supported filter and warning rules**
   - Expose service category, time range, and only reliable stored geography levels as filter options.
   - Detect exceptionally large requests before retrieval begins.
   - Allow the planner to revise or proceed after a warning while preserving selected filter context.
   - If the planner declines to proceed, keep the selected filters visible and do not execute retrieval.

5. **Implement clear success, no-data, and error behavior**
   - Return valid historical summaries when matching data exists.
   - Return explicit no-data states when valid filters have no matches.
   - Return explicit error states when retrieval or rendering cannot complete.
   - Never display incomplete or misleading partial historical results.

6. **Persist analysis-specific operational records**
   - Record one analysis outcome per executed request, including selected filters, warning status, success, no-data, retrieval failure, and rendering failure.
   - Keep analysis history distinct from dataset-version and validation-run history.

7. **Deliver typed frontend modules for planner exploration**
   - Implement a historical-demand analysis page and feature modules that consume the normalized backend contract.
   - Reuse shared API utilities and auth hooks for analysis requests.
   - Render filters, warning states, charts or tables, and no-data or error states from typed domain models only.

8. **Expose bounded observability and contracts**
   - Provide a filter-options or analysis-context surface if needed and a historical-analysis retrieval endpoint for executed requests.
   - Limit responses to operationally necessary filter metadata, aggregated demand values, warning state, and outcome summaries.
   - Never expose raw source rows, secrets, or unstable external data formats.

9. **Verify acceptance behavior**
   - Validate successful filtered historical demand retrieval and display against `docs/UC-07-AT.md`.
   - Validate high-volume warnings, decline-or-proceed behavior, and preserved filter context against `docs/UC-07-AT.md`.
   - Validate no-data, retrieval-failure, and rendering-failure outcomes.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution violations or justified exceptions were required for this feature.
