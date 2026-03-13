# Quickstart: Compare Demand and Forecasts Across Categories and Geographies

## Purpose

Use this guide to implement and verify UC-08 as a typed planner-facing comparison experience that reuses approved historical lineage from UC-02 plus active forecast lineage from UC-03 and UC-04, while keeping missing-data, retrieval-failure, alignment-failure, and render-failure behavior explicitly distinguishable.

## Implementation Outline

1. Reuse upstream lineage entities:
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
2. Add only the UC-08 comparison-specific persistence:
   - `DemandComparisonRequest`
   - `DemandComparisonResult`
   - `DemandComparisonSeriesPoint`
   - `ComparisonMissingCombination`
   - `DemandComparisonOutcomeRecord`
3. Build one backend comparison path that:
   - resolves the approved cleaned dataset lineage from UC-02
   - resolves the active daily or weekly forecast lineage from UC-03 or UC-04
   - accepts service category, geography, and time-range filters
   - warns before running exceptionally large requests
   - retrieves historical and forecast demand, aligns them on common dimensions, and assembles a normalized comparison response
   - records success, historical-only, forecast-only, clarified mixed-availability, retrieval-failure, alignment-failure, and render-failure outcomes
4. Preserve UC-08 behavior boundaries:
   - treat no matching historical data as forecast-only
   - treat no matching forecast data as historical-only
   - treat historical retrieval failure and forecast retrieval failure as explicit error states
   - treat alignment failure as an explicit error state for the whole request
   - keep mixed missing forecast combinations marked as a clarified extension to UC-08 and UC-08-AT
5. Keep route handlers thin:
   - `GET` comparison context if needed
   - `POST` comparison request
   - `POST` render-outcome report
   - all business decisions in services
   - all persistence in repositories
6. Implement a typed frontend comparison interface that:
   - consumes only the normalized backend contract
   - renders charts, tables, warnings, partial-result messages, and error states from typed domain models
   - reports render failures back to the backend for outcome logging

## Acceptance Alignment

Map implementation and tests directly to [UC-08](/root/311-forecast-system/docs/UC-08.md) and [UC-08-AT](/root/311-forecast-system/docs/UC-08-AT.md):

- Main Success: Comparison interface opens, filters are shown, matching historical and forecast data are retrieved, aligned, displayed, and logged
- Extension 3a / AT-04: High-volume request warns before retrieval and proceeds only after planner acknowledgment
- Extension 4a / AT-05: No historical data shows forecast-only with clear messaging and logging
- Extension 5a / AT-06: No forecast data shows historical-only with clear messaging and logging
- AT-10: Historical retrieval failure or forecast retrieval failure shows an error state and logs the failed retrieval
- Extension 6a / AT-08: Alignment failure shows an error state and no comparison output
- Extension 8a / AT-09: Rendering failure shows an error state and logs the failure
- Clarified extension: Mixed forecast availability across selected combinations shows partial comparisons plus explicit missing-combination identification

## Suggested Test Layers

- Unit tests for filter normalization, high-volume warning detection, outcome selection, and alignment guards
- Integration tests across approved-dataset lookup, active-forecast lookup, comparison assembly, partial-result handling, and terminal outcome recording
- Contract tests for [demand-comparison-api.yaml](/root/311-forecast-system/specs/008-compare-demand-forecasts/contracts/demand-comparison-api.yaml)
- Frontend component and interaction tests for multi-select filters, warning acknowledgment, comparison rendering, explicit partial-result states, and error-state presentation

## Exit Conditions

Implementation is ready for task breakdown when:

- UC-08 reads historical demand from UC-02 lineage and forecast demand from active UC-03 or UC-04 lineage without creating new upstream lifecycle records
- High-volume requests warn before retrieval begins
- Forecast-only, historical-only, retrieval-failure, alignment-failure, and render-failure paths are distinct and acceptance-testable
- Mixed missing forecast combinations remain clearly marked as a clarified extension rather than a written UC-08 alternative flow
- Comparison responses are normalized for typed frontend consumption and never expose raw source rows directly
- The frontend consumes backend contracts only and reports render failure outcomes explicitly
