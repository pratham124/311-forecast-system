# Quickstart: Add Weather Overlay

## Purpose

Use this guide to implement and verify UC-09 as an optional weather-overlay capability on the existing forecast explorer. The implementation should reuse the current explorer context, normalize weather observations from MSC GeoMet, keep the overlay limited to one selected measure at a time, preserve the base forecast explorer across all overlay failure modes, and keep the overlay-state vocabulary consistent across the spec, data model, and API contract.

## Canonical Overlay States

Use one vocabulary everywhere: `disabled`, `loading`, `visible`, `unavailable`, `retrieval-failed`, `misaligned`, `superseded`, `failed-to-render`.

- `disabled`: user has the overlay turned off; returned by `GET`, not posted as a render event
- `loading`: latest supported selection is still being assembled
- `visible`: weather overlay is rendered and aligned
- `unavailable`: provider call succeeded but returned no matching weather records
- `retrieval-failed`: provider call failed before records could be returned
- `misaligned`: approved geography or time-bucket alignment could not be achieved
- `superseded`: a newer selection replaced the in-flight request
- `failed-to-render`: client reported render failure; posted through render-events and returned by later `GET` reads

## Implementation Outline

1. Reuse the existing forecast explorer context:
   - active geography
   - active time range
   - forecast series
   - historical demand series
   - existing status and metadata already required by the forecast explorer
2. Add one overlay selection flow:
   - enable or disable the weather overlay
   - choose one supported measure at a time: `temperature` or `snowfall`
3. Build one backend overlay assembly path that:
   - validates the selected geography, time range, and weather measure
   - treats a geography as supported only when approved rules map it directly to the approved Edmonton-area weather-station selection and to the demand-view time buckets
   - retrieves weather observations only through dedicated MSC GeoMet modules
   - distinguishes empty successful retrieval from provider retrieval failure
   - suppresses the overlay when matching or alignment is not safe
4. Preserve correct interaction behavior:
   - disabling the overlay removes the weather layer while preserving the base explorer
   - changing filters or the selected measure supersedes any in-flight overlay request
   - only the latest supported selection may produce a visible overlay
5. Keep route handlers thin:
   - `GET` current weather overlay state, including explicit non-visible states
   - `POST` render outcome event for final render success/failure observability
   - all business behavior in services
   - all persistence access in repositories
6. Implement typed frontend modules that:
   - render the overlay distinctly from forecast and historical demand
   - remove stale overlay visuals immediately after disable or supersession
   - report final render success or failure to the backend

## Acceptance Alignment

Map implementation and tests directly to [UC-09-AT.md](/root/311-forecast-system/docs/UC-09-AT.md):

- `AT-01`: Forecast explorer loads and weather overlay control is visible
- `AT-02`: Enabling overlay retrieves weather data for the selected time range and geography
- `AT-03`: Weather observations align to the explorer timeline and geography
- `AT-04`: Overlay renders alongside forecast and historical demand without obscuring the base view
- `AT-05`: Successful overlay rendering is logged
- `AT-06`: Missing weather data keeps the forecast explorer usable without the overlay
- `AT-07`: Weather retrieval failure keeps the forecast explorer usable without the overlay
- `AT-08`: Alignment failure suppresses the overlay and logs the issue
- `AT-09`: Rendering failure is logged, becomes a stable `failed-to-render` state, and does not show a misleading partial overlay
- `AT-10`: Toggle and filter changes remove stale overlay state and refresh only for the latest selection

## Suggested Test Layers

- Unit tests for supported-measure validation, geography/station-match enforcement, retrieval-status classification, alignment decisions, disable behavior, and superseded-request handling
- Integration tests across forecast explorer context lookup, GeoMet normalization, overlay assembly, state selection, and render-event ingestion
- Contract tests for [weather-overlay-api.yaml](/root/311-forecast-system/specs/009-add-weather-overlay/contracts/weather-overlay-api.yaml)
- Frontend component and interaction tests for measure selection, toggle removal, filter-change supersession, explicit non-visible states, and render-failure reporting
- Acceptance-style tests mirroring `docs/UC-09-AT.md`

## Exit Conditions

Implementation is ready for task breakdown when:

- the overlay is optional and limited to one selected weather measure at a time
- weather observations are sourced only through normalized MSC GeoMet modules
- supported geography is enforced through approved Edmonton-area station and time-bucket mapping rules
- missing records and provider retrieval failures are separate observable outcomes
- `GET` returns the stable overlay state, including `disabled` and `failed-to-render`
- `POST` render-events records final render success/failure, including `failed-to-render`
- disabling the overlay removes the weather layer without affecting the base explorer
- superseded in-flight requests cannot produce visible stale overlay results
