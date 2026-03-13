# Implementation Plan: Add Weather Overlay

**Branch**: `009-add-weather-overlay` | **Date**: 2026-03-13 | **Spec**: [spec.md](/root/311-forecast-system/specs/009-add-weather-overlay/spec.md)
**Input**: Feature specification from `/specs/009-add-weather-overlay/spec.md`

## Summary

Implement UC-09 as an optional weather overlay on the existing forecast explorer by reusing the active explorer geography and time range, retrieving one selected weather measure at a time from normalized MSC GeoMet integrations, applying only approved geography-to-Edmonton-station and time-bucket alignment rules, and returning a stable overlay state contract that preserves the base explorer for every non-visible outcome. The design keeps `disabled`, `loading`, `visible`, `unavailable`, `retrieval-failed`, `misaligned`, `superseded`, and `failed-to-render` as the canonical overlay state vocabulary, exposes the stable read states through `GET`, records final client render outcomes through `POST` render-events, and requires authenticated, schema-validated API access so backend observability remains distinct from retrieval and alignment.

## Technical Context

**Language/Version**: Python 3.11 backend services and TypeScript React frontend  
**Primary Dependencies**: FastAPI, Pydantic-style typed schemas, SQLAlchemy-compatible PostgreSQL access layer, structured logging, React, TypeScript, Tailwind CSS, Government of Canada MSC GeoMet client modules  
**Storage**: PostgreSQL for forecast explorer lineage reuse and structured overlay operational logs; no separate overlay activation store  
**Testing**: pytest for backend unit/integration/contract coverage, frontend component/integration tests, and acceptance tests aligned to `docs/UC-09-AT.md`  
**Target Platform**: Linux-hosted web application with FastAPI backend and React frontend  
**Project Type**: Web application with backend API plus typed frontend  
**Performance Goals**: Meet `SC-001` by returning a visible overlay within 5 seconds for at least 95% of supported selections  
**Constraints**: Overlay remains optional, shows one measure at a time, never replaces the base forecast explorer, suppresses output instead of using fallback geography/station mappings, differentiates missing weather records from provider retrieval failure, and enforces authenticated, validated API requests  
**Scale/Scope**: Forecast explorer overlay for approved Edmonton-area supported geographies and selected time ranges already served by the forecast explorer

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- `PASS`: Use-case traceability is preserved. The plan stays bounded to [UC-09.md](/root/311-forecast-system/docs/UC-09.md) and [UC-09-AT.md](/root/311-forecast-system/docs/UC-09-AT.md), especially AT-06 through AT-10 for non-visible states and observability.
- `PASS`: Canonical data-source usage is preserved. Weather data remains sourced through Government of Canada MSC GeoMet, with approved Edmonton-area station selection encoded as a business rule rather than ad hoc fallback logic.
- `PASS`: Layered backend structure is preserved. Route handlers expose typed `GET` and `POST` contracts only; overlay assembly, geography/station matching, state selection, and observability remain in services and repositories.
- `PASS`: Typed contract coverage is preserved. Spec, data model, and OpenAPI contract share one overlay-state vocabulary, explicitly separate empty successful retrieval from provider retrieval failure, and require schema-validated request handling.
- `PASS`: Security coverage is preserved. Weather-overlay endpoints remain backend-authenticated and authorization-aware, consistent with the constitution.
- `PASS`: Operational safety is preserved. All non-visible outcomes keep `baseForecastPreserved = true`, prevent misleading partial overlays, and retain enough context for logging and diagnosis.
- `PASS`: No constitution waiver is required. The feature remains an optional explorer overlay with no expansion into separate activation lifecycles or fallback weather geographies.

## Phase 0 Research Decisions

- Use the current spec as the source of truth for the canonical overlay-state vocabulary: `disabled`, `loading`, `visible`, `unavailable`, `retrieval-failed`, `misaligned`, `superseded`, `failed-to-render`.
- Represent `disabled` in the `GET` response because it is a user-visible off state of the overlay control and part of the stable read model for the current explorer view.
- Represent `failed-to-render` in both the `GET` response and the `POST` render-event flow: `POST` captures the frontend render outcome as the source event, and `GET` exposes the resulting stable non-visible overlay state for subsequent reads.
- Distinguish weather-provider outcomes as:
  - `unavailable`: provider request succeeded but returned no matching weather records for an otherwise supported selection
  - `retrieval-failed`: provider request timed out, errored, or otherwise failed before records could be returned
- Carry the approved geography-alignment rule into design as a direct mapping from forecast-explorer geography to an approved Edmonton-area station selection plus demand-view time buckets; if no approved mapping exists, the selection is unsupported and the overlay is suppressed without fallback substitution.
- Distinguish unsupported geography matching from post-match time-bucket alignment failure in service logic, logging, and user-facing status messaging even when both produce a non-visible overlay outcome.

## Project Structure

### Documentation (this feature)

```text
specs/009-add-weather-overlay/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── weather-overlay-api.yaml
└── tasks.md
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   ├── services/
│   ├── repositories/
│   ├── clients/
│   └── models/
└── tests/

frontend/
├── src/
│   ├── api/
│   ├── components/
│   ├── features/
│   ├── hooks/
│   ├── pages/
│   ├── types/
│   └── utils/
└── tests/

tests/
├── contract/
├── integration/
└── unit/
```

**Structure Decision**: Use the existing FastAPI backend and React frontend split. Weather overlay retrieval and state assembly live in backend services and repository/client layers; the frontend exposes a real page entrypoint under `frontend/src/pages/` that composes reusable feature modules, shared UI components, typed API utilities, hooks, and helper utilities.

## Phase 1 Design

### Data Model Direction

- `WeatherOverlaySelection` remains the request-intent model for one enabled measure at a time or an explicit disabled read state for the current explorer view.
- `WeatherObservationSet` distinguishes successful empty retrieval (`unavailable`) from provider failure (`retrieval-failed`) and records the approved matched geography and Edmonton-area station only when alignment is valid.
- `OverlayDisplayState` becomes the canonical stable read model and includes all visible and non-visible states required by the spec, with `disabled` and `failed-to-render` explicitly represented.
- `WeatherOverlayRenderEvent` remains the client-reported render outcome event and is the write path that can transition a previously retrievable overlay into `failed-to-render`.

### API Contract Direction

- `GET /api/v1/forecast-explorer/weather-overlay` returns the stable overlay read model for the current selection and can explicitly return `disabled`, `loading`, `visible`, `unavailable`, `retrieval-failed`, `misaligned`, `superseded`, and `failed-to-render`.
- `POST /api/v1/forecast-explorer/weather-overlay/{overlayRequestId}/render-events` records frontend render outcomes and is the only write path for final render success/failure observability.
- `disabled` is part of the `GET` response only; it is not posted as a render event because it is driven by user selection rather than a rendering attempt.
- `failed-to-render` is represented in both places: it is reported by `POST` and then becomes observable in subsequent `GET` responses as a stable non-visible overlay state.
- Both endpoints require authenticated access, authorization checks appropriate to the forecast explorer, and schema validation for query parameters and request bodies.

### Implementation Notes

- The overlay must never substitute a nearby or broader geography or station when approved geography/station mapping is absent.
- The implementation must emit distinct operational diagnostics and distinct user-facing status messages for unsupported geography matching versus post-match time-bucket alignment failure.
- The base forecast explorer remains authoritative and preserved for all non-visible overlay states.
- Superseded requests remain non-terminal for the explorer as a whole but terminal for the specific overlay request they replace.

## Post-Design Constitution Check

- `PASS`: Design artifacts preserve UC-09 and UC-09-AT traceability.
- `PASS`: GeoMet normalization and approved Edmonton-area station mapping remain explicit and isolated in backend services/clients.
- `PASS`: Stable typed contracts separate retrieval/alignment state from frontend render-event reporting.
- `PASS`: The design now covers auth/authz, schema validation, and explicit render-event verification obligations required by the constitution and UC-09 acceptance contract.
- `PASS`: No non-visible overlay state compromises the base forecast explorer or introduces silent failure.

## Complexity Tracking

No constitution violations or complexity exemptions are required.
