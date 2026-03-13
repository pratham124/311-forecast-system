# Data Model: Add Weather Overlay

## Overview

UC-09 extends the existing forecast explorer by adding a weather overlay workflow that reuses approved demand and forecast context while introducing normalized overlay request, response, and render-event models. The feature does not require a separate activation lifecycle; instead, it relies on stable read models plus structured observability for retrieval, alignment, supersession, disable, and render outcomes.

## Canonical Overlay State Vocabulary

Use the same vocabulary across the spec, data model, and API contract:

- `disabled`
- `loading`
- `visible`
- `unavailable`
- `retrieval-failed`
- `misaligned`
- `superseded`
- `failed-to-render`

### State Semantics

- `visible` is the only state in which a weather layer is present on the forecast explorer.
- `disabled`, `loading`, `unavailable`, `retrieval-failed`, `misaligned`, `superseded`, and `failed-to-render` are non-visible states; in all of them the base forecast explorer remains present without a weather layer.
- `disabled` is an explicit user-visible off state in the overlay read model, not a render-event state.
- `failed-to-render` is a render-event-derived state that is also exposed through the stable overlay read model after the failure is recorded.

## Reused Context From Previous Specs

### Entity: CleanedDatasetVersion

**Purpose**: Represents the approved Edmonton 311 cleaned dataset lineage used by the existing forecast explorer for historical demand context.

**Reuse in UC-09**

- Preserves traceability for the historical demand series shown underneath the weather overlay.
- Remains upstream-only and is not duplicated by UC-09.

### Entity: ForecastVersion / WeeklyForecastVersion

**Purpose**: Represent the stored daily and weekly forecast products already visualized by the forecast explorer.

**Reuse in UC-09**

- Provide the base forecast context that the weather overlay augments.
- Remain the source of truth for forecast values and are not modified by overlay behavior.

### Entity: ForecastVisualization

**Purpose**: Represents the normalized forecast explorer view defined by the prior visualization feature.

**Reuse in UC-09**

- Supplies the active geography, time range, forecast series, historical series, and status metadata that the weather overlay must align to.
- Remains authoritative even when weather retrieval, alignment, or rendering fails.

## New Derived Entity: WeatherOverlaySelection

**Purpose**: Captures the operational manager’s current overlay intent for the active forecast explorer view and defines whether a request is eligible to become a supported selection.

| Field | Type | Required | Rules |
|--------|------|----------|-------|
| `overlay_request_id` | Identifier | Yes | Unique per overlay retrieval attempt or explicit disable state snapshot |
| `overlay_enabled` | Boolean | Yes | `true` when the overlay is requested; `false` when it is disabled |
| `selected_weather_measure` | Enum | No | `temperature` or `snowfall`; required when `overlay_enabled = true` |
| `geography_id` | String | Yes | Canonical identifier for the current forecast explorer geography |
| `time_range_start` | Timestamp | Yes | Start of the active explorer time range |
| `time_range_end` | Timestamp | Yes | End of the active explorer time range |
| `supersedes_overlay_request_id` | Identifier | No | Present when a new selection replaces an in-flight request |
| `requested_at` | Timestamp | Yes | Set when the selection is submitted |
| `supported_selection` | Boolean | Yes | `true` only when the request is the latest non-superseded enabled request and its geography, time range, and measure are supported under approved alignment rules |

**Validation rules**

- Exactly one supported weather measure may be selected for any enabled overlay request.
- `selected_weather_measure` must be empty when `overlay_enabled = false`.
- `time_range_end` must be greater than `time_range_start`.
- A request that supersedes a prior request may only reference one earlier `overlay_request_id`.
- `supported_selection = true` requires `overlay_enabled = true`.

## New Derived Entity: WeatherObservationSet

**Purpose**: Represents the normalized weather observations retrieved for one selected measure before or after alignment to the forecast explorer context.

| Field | Type | Required | Rules |
|--------|------|----------|-------|
| `overlay_request_id` | Identifier | Yes | Links the observations to one overlay request |
| `weather_measure` | Enum | Yes | `temperature` or `snowfall` |
| `weather_source` | Enum | Yes | `msc_geomet` only |
| `matched_geography_id` | String | No | Present only when the selected geography matches an approved geography-alignment rule |
| `source_station_id` | String | No | Present only when the approved Edmonton-area station selection is applied |
| `observation_time_granularity` | Enum | Yes | `hourly` or `daily` |
| `observation_points` | Collection | No | Ordered weather values for the selected measure |
| `measurement_unit` | String | No | Unit associated with the selected measure |
| `retrieval_status` | Enum | Yes | `retrieved`, `missing`, `retrieval-failed`, or `superseded` |
| `alignment_status` | Enum | Yes | `pending`, `aligned`, `misaligned`, or `not_applicable` |

**Validation rules**

- `weather_source` must always be `msc_geomet`.
- A supported geography exists only when approved alignment rules define a direct mapping from the forecast-explorer geography to an approved Edmonton-area station selection and to the active demand-view time buckets.
- `matched_geography_id` and `source_station_id` must be empty when `alignment_status = misaligned`.
- `observation_points` must be empty when `retrieval_status = missing`, `retrieval-failed`, or `superseded`.
- `retrieval_status = missing` means the provider request completed successfully but returned no matching weather records.
- `retrieval_status = retrieval-failed` means the provider request failed before records could be returned.
- `alignment_status = aligned` requires both `matched_geography_id` and `source_station_id`.

## New Derived Entity: OverlayDisplayState

**Purpose**: Represents the stable read-model result of the overlay workflow for one explorer view and one overlay request.

| Field | Type | Required | Rules |
|--------|------|----------|-------|
| `overlay_request_id` | Identifier | Yes | Unique link back to the overlay request |
| `display_status` | Enum | Yes | `disabled`, `loading`, `visible`, `unavailable`, `retrieval-failed`, `misaligned`, `superseded`, or `failed-to-render` |
| `status_message` | String | No | User-facing explanation when the overlay is not visible |
| `base_forecast_preserved` | Boolean | Yes | Must always be `true` |
| `rendered_at` | Timestamp | No | Present only when the overlay is rendered successfully |
| `failure_category` | Enum | No | `weather-missing`, `retrieval-failed`, `misaligned`, `failed-to-render`, or `superseded` |
| `user_visible` | Boolean | Yes | `true` for all states returned by `GET`, including `disabled` |
| `state_source` | Enum | Yes | `selection-read-model`, `overlay-assembly`, or `render-event` |

**Validation rules**

- `base_forecast_preserved` must always remain `true`.
- `display_status = visible` requires `rendered_at` and no `failure_category`.
- `display_status = visible` is the only state that permits weather observations to be shown on the forecast explorer.
- `display_status = disabled` is user-visible in `GET` responses and must have `state_source = selection-read-model`.
- `display_status = unavailable`, `retrieval-failed`, `misaligned`, `superseded`, or `failed-to-render` requires `status_message`.
- `display_status = failed-to-render` must have `state_source = render-event`.
- `display_status = disabled` means no weather observations may remain attached to the current explorer view.

**State transitions**

`disabled` → `loading`  
`loading` → `visible`  
`loading` → `unavailable`  
`loading` → `retrieval-failed`  
`loading` → `misaligned`  
`loading` → `superseded`  
`visible` → `disabled`  
`visible` → `loading`  
`visible` → `failed-to-render`

No other transitions are valid.

## New Contract Event: WeatherOverlayRenderEvent

**Purpose**: Records the final frontend render outcome for one overlay request so retrieval success, alignment success, and render success remain distinct observable events.

| Field | Type | Required | Rules |
|--------|------|----------|-------|
| `overlay_request_id` | Identifier | Yes | References one overlay request |
| `render_status` | Enum | Yes | `rendered` or `failed-to-render` |
| `reported_at` | Timestamp | Yes | Time the client reports the render result |
| `failure_reason` | String | No | Required when `render_status = failed-to-render` |

**Validation rules**

- `failure_reason` is required only when `render_status = failed-to-render`.
- A render event may be accepted only for a request that has not already been superseded or disabled.
- `disabled` is not emitted as a render event; it is represented only in the current overlay read model returned by `GET`.
