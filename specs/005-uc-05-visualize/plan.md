# Implementation Plan: Visualize Forecast Curves with Uncertainty Bands

**Branch**: `005-uc-05-visualize` | **Date**: 2026-03-13 | **Spec**: [spec.md](/Users/sahmed/Documents/311-forecast-system/specs/005-uc-05-visualize/spec.md)
**Input**: Feature specification from `/specs/005-uc-05-visualize/spec.md`

## Summary

Implement UC-05 as a forecast-visualization feature that reuses approved upstream lineage from UC-01 and UC-02 and the persisted forecast products from UC-03 and UC-04 rather than redefining them. The feature should deliver a typed dashboard view for operational managers that can load the current forecast product, show `P10`, `P50`, and `P90` uncertainty bands over the previous 7 days of historical demand, expose category filtering plus forecast-status metadata required by the constitution, and preserve last-known-good behavior through a 24-hour fallback visualization snapshot when current forecast data is unavailable or rendering cannot complete.

## Technical Context

**Language/Version**: Python 3.11 for backend services and TypeScript for the React frontend  
**Primary Dependencies**: FastAPI, Pydantic-style typed schemas, SQLAlchemy-compatible PostgreSQL access layer, structured logging, React, TypeScript, Tailwind CSS, shared typed API/domain models, and a reusable chart-rendering layer for forecast curves and bands  
**Storage**: PostgreSQL for reused UC-01 through UC-04 lineage plus visualization load records, fallback visualization snapshots, and migration-managed schema history  
**Testing**: pytest for backend unit, integration, and contract coverage plus frontend component and interaction tests aligned to `docs/UC-05-AT.md`  
**Target Platform**: Linux-hosted backend API with a browser-based React dashboard for operational managers  
**Project Type**: web application with backend API and typed frontend dashboard  
**Performance Goals**: Deliver a complete visualization within 10 seconds for at least 95% of dashboard loads when forecast, history, and uncertainty data are available; record a terminal load outcome for 100% of dashboard opens; show only fallback snapshots produced within the previous 24 hours  
**Constraints**: Must satisfy `docs/UC-05.md` and `docs/UC-05-AT.md`; must reuse rather than duplicate lineage from UC-01 through UC-04; must standardize on `P10`, `P50`, and `P90`; must use the previous 7 days as the historical context window; must expose category filtering, alerts/status metadata, and last-updated visibility for the forecast view per constitution; must keep FastAPI routes thin, business logic in services, visualization assembly in dedicated backend modules, persistence in repositories, and frontend rendering in typed feature modules; must never let the frontend read databases or third-party APIs directly; must never activate or show a fallback snapshot older than 24 hours; must not expose raw source payloads, feature matrices, secrets, or model internals  
**Scale/Scope**: One forecast-visualization dashboard surface, one typed visualization API, support for the existing current 1-day and 7-day forecast products through a normalized view model, retained visualization load history, retained fallback visualization snapshots, and acceptance coverage for success, degraded, fallback, and render-failure outcomes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Use-case traceability**: PASS. The plan remains anchored to [UC-05](/Users/sahmed/Documents/311-forecast-system/docs/UC-05.md) and [UC-05-AT](/Users/sahmed/Documents/311-forecast-system/docs/UC-05-AT.md), and it reuses UC-01 through UC-04 lineage only to fulfill the governed visualization behavior.
- **Canonical data-source usage**: PASS. Historical context is derived from the approved Edmonton 311 cleaned-data lineage, and forecast curves and uncertainty bands are read from the persisted forecast products already defined by UC-03 and UC-04.
- **Layered backend architecture**: PASS. Forecast view assembly stays in backend services and dedicated visualization modules, persistence stays in repositories, and route handlers remain limited to request parsing, auth, and response shaping.
- **Typed frontend modularity and secure access**: PASS. UC-05 is implemented as a typed React frontend consuming only normalized backend contracts, with backend-enforced authentication and role-aware access to dashboard data.
- **Operational safety / last-known-good activation**: PASS. The view may use only a fallback snapshot produced within the previous 24 hours, and missing or failed current data paths never masquerade as a fresh successful visualization.
- **Forecast view obligations**: PASS. The plan explicitly includes uncertainty bands, category filtering, an alerts/status panel, last-updated metadata, and pipeline/data status visibility as constitution-required parts of the forecast view.

**Post-Design Check**: PASS. The research, data model, quickstart, and visualization contract preserve use-case traceability, continue to rely on canonical Edmonton lineage and previously defined forecast entities, keep frontend/backend layering explicit, and enforce the same fallback-age and status-visibility rules after design.

## Project Structure

### Documentation (this feature)

```text
specs/005-uc-05-visualize/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── forecast-visualization-api.yaml
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

**Structure Decision**: Use the repository’s backend/frontend split because UC-05 includes both a normalized backend visualization contract and a typed frontend dashboard. Reuse existing forecast and lineage persistence in `backend/`, and confine UI composition to `frontend/` without introducing direct storage or third-party access from the client.

## Phase 0 Research Summary

- Confirmed UC-05 should reuse existing persisted forecast entities from UC-03 and UC-04 as source-of-truth inputs rather than duplicating forecast runs, forecast versions, or forecast buckets under visualization-specific names.
- Confirmed the historical overlay should be assembled from the approved cleaned dataset lineage defined in UC-02 so the visualization remains consistent with the same canonical Edmonton 311 demand source used by forecasting.
- Confirmed `P10`, `P50`, and `P90` should be the only standard uncertainty labels exposed by the dashboard and its contracts.
- Confirmed the dashboard should use the previous 7 days of historical demand as the standard context window.
- Confirmed fallback behavior should rely on a persisted visualization snapshot that expires after 24 hours rather than on stale current-forecast pointers.
- Confirmed the constitution requires category filtering, alerts/status visibility, and last-updated metadata on the forecast view, so those elements must be included in the normalized visualization contract even though UC-05’s primary acceptance focus is the chart.
- Confirmed a single normalized visualization response should support both the current daily and current weekly forecast products, with the frontend rendering whichever product the manager selects or the application designates as default.

## Phase 1 Design Summary

- Reuse UC-01 and UC-02 lineage entities and UC-03/UC-04 forecast entities as immutable inputs, and add only visualization-specific records for dashboard load outcomes and fallback snapshots.
- Normalize the current daily and weekly forecast products into one backend visualization response that includes forecast metadata, historical series, `P10`/`P50`/`P90` bands, category filter state, alerts/status summaries, and fallback metadata.
- Persist visualization load outcomes separately from forecast runs so dashboard rendering success, degraded modes, fallback use, and render failures remain queryable without mutating forecast lineage.
- Persist fallback visualization snapshots as bounded last-known-good display artifacts that reference the exact forecast version and historical window used to produce them.
- Keep frontend rendering in typed forecast-visualization modules that consume only the normalized backend contract and report final render outcomes back to the backend for observability.

## Implementation Steps

1. **Resolve shared forecast and history lineage**
   - Read the approved cleaned dataset marker from UC-02 to assemble the previous 7 days of historical demand.
   - Read the current forecast markers and stored forecast versions from UC-03 and UC-04 rather than creating new forecast persistence for UC-05.
   - Normalize both forecast products into one internal visualization source model with explicit granularity and horizon metadata.

2. **Gate dashboard access through backend-authenticated contracts**
   - Require authenticated access for visualization data and render-outcome reporting.
   - Keep all role checks in backend dependencies and services.
   - Prevent the frontend from directly querying persistence or third-party data sources.

3. **Assemble the visualization payload in dedicated backend services**
   - Build one visualization-response service that joins current forecast data, historical demand context, uncertainty bands, last-updated metadata, alerts/status summaries, and product metadata.
   - Keep FastAPI routes transport-only and move all business decisions about fallback use, partial rendering modes, and status selection into service modules.
   - Normalize all response shapes into stable Pydantic-style schemas before they reach the frontend.

4. **Preserve standardized uncertainty and context rules**
   - Expose only `P10`, `P50`, and `P90` as uncertainty-band labels.
   - Use the previous 7 days as the standard historical context window.
   - Make the forecast boundary explicit in the returned visualization data so the frontend can distinguish history from forecast without inferring it.

5. **Implement bounded degraded and fallback behavior**
   - If historical demand is unavailable, return a valid forecast visualization without the historical overlay and record the degraded outcome.
   - If uncertainty metrics are unavailable, return a valid visualization without uncertainty bands and record the degraded outcome.
   - If current forecast data is unavailable, return the most recent fallback visualization snapshot only when it was produced within the previous 24 hours; otherwise return an explicit unavailable state.
   - If the frontend cannot render the returned payload, record the render failure without mutating any current forecast markers.

6. **Persist visualization-specific operational records**
   - Record one visualization load outcome per dashboard open, including source product, source forecast version, selected category filter, degraded status, fallback use, and render result.
   - Store fallback visualization snapshots only after a complete successful dashboard data assembly and renderable response exists.
   - Keep visualization history distinct from forecast-run and forecast-version history.

7. **Deliver typed frontend modules for the dashboard**
   - Implement a forecast-visualization page and feature modules that consume the normalized backend contract.
   - Reuse shared API utilities and auth hooks for all dashboard requests.
   - Render category filters, chart data, alerts/status summaries, and last-updated indicators from typed domain models only.

8. **Expose bounded observability and contracts**
   - Provide a current-visualization endpoint that returns the full dashboard payload and a render-event endpoint that records final client render success or failure.
   - Limit responses to operationally necessary identifiers, timestamps, filter values, series points, quantiles, fallback metadata, and status summaries.
   - Never expose raw source rows, feature matrices, training artifacts, or secrets.

9. **Verify acceptance behavior**
   - Validate success rendering with history and uncertainty bands.
   - Validate historical-missing and uncertainty-missing degraded paths.
   - Validate forecast-missing fallback vs unavailable-state behavior.
   - Validate rendering-failure logging and overlay alignment behavior for both supported forecast products.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution violations or justified exceptions were required for this feature.
