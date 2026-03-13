# Quickstart: Visualize Forecast Curves with Uncertainty Bands

## Purpose

Use this guide to implement and verify UC-05 as a typed forecast-visualization experience that reuses the approved dataset lineage from UC-02 and the current forecast products from UC-03 and UC-04, while adding only the visualization-specific persistence required for fallback snapshots and load observability.

## Implementation Outline

1. Reuse upstream lineage and forecast entities:
   - `IngestionRun`
   - `DatasetVersion`
   - `ValidationRun`
   - `CleanedDatasetVersion`
   - `CurrentDatasetMarker`
   - `ForecastRun`
   - `ForecastVersion`
   - `ForecastBucket`
   - `CurrentForecastMarker`
   - `WeeklyForecastRun`
   - `WeeklyForecastVersion`
   - `WeeklyForecastBucket`
   - `CurrentWeeklyForecastMarker`
2. Add only the UC-05 visualization-specific persistence:
   - `VisualizationLoadRecord`
   - `VisualizationSnapshot`
3. Build one backend visualization assembly path that:
   - resolves the approved cleaned dataset for the previous 7 days of historical context
   - resolves either the current daily or current weekly forecast product
   - normalizes the selected forecast product into one visualization response shape
   - exposes only `P10`, `P50`, and `P90` as uncertainty bands
   - includes category filtering, alerts/status data, and last-updated metadata
4. Implement bounded degraded behavior:
   - missing history returns a forecast-only visualization and records a degraded outcome
   - missing uncertainty returns a no-band visualization and records a degraded outcome
   - missing current forecast uses a stored fallback snapshot only when it is no more than 24 hours old
   - missing current forecast with no eligible fallback returns an explicit unavailable state
5. Keep route handlers thin:
   - `GET` current visualization payload
   - `POST` render outcome event
   - all business decisions in services
   - all persistence in repositories
6. Implement a typed frontend dashboard that:
   - consumes only the normalized backend contract
   - renders one shared time axis for history and forecast
   - distinguishes history, forecast, and uncertainty visually
   - reports final render success or failure back to the backend

## Acceptance Alignment

Map implementation and tests directly to [UC-05-AT](/Users/sahmed/Documents/311-forecast-system/docs/UC-05-AT.md):

- `AT-01`: Dashboard shows forecast, uncertainty bands, and historical context together
- `AT-02`: Missing forecast data returns fallback or unavailable state
- `AT-03`: Missing historical data still shows forecast and uncertainty
- `AT-04`: Missing uncertainty metrics still shows history and forecast
- `AT-05`: Rendering error records a failure and shows an explicit error state
- `AT-06`: Overlay order and interpretability remain intact
- `AT-07`: Forecast boundary and shared time-axis alignment remain correct
- `AT-08`: Every dashboard load records a clear terminal outcome

## Suggested Test Layers

- Unit tests for visualization assembly, 7-day history window selection, `P10`/`P50`/`P90` normalization, fallback-age enforcement, and degraded-state selection
- Integration tests across approved-dataset lookup, current daily/weekly forecast lookup, visualization snapshot persistence, and load-outcome recording
- Contract tests for [forecast-visualization-api.yaml](/Users/sahmed/Documents/311-forecast-system/specs/005-uc-05-visualize/contracts/forecast-visualization-api.yaml)
- Frontend component and interaction tests for chart rendering, filter changes, status visibility, and render-failure reporting
- Acceptance-style tests mirroring `docs/UC-05-AT.md`

## Exit Conditions

Implementation is ready for task breakdown when:

- UC-05 reads forecast lineage from UC-03 and UC-04 without redefining forecast entities
- Historical context is assembled from the approved cleaned dataset lineage from UC-02
- The normalized dashboard contract always includes status metadata, category filter state, and last-updated visibility
- Fallback snapshots are eligible only for 24 hours and never replace current forecast markers
- Dashboard load outcomes remain queryable for success, degraded, fallback, unavailable, and render-failure states
- The frontend consumes typed backend contracts only and reports render outcomes without touching storage or third-party APIs directly
