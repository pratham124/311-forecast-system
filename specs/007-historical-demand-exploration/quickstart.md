# Quickstart: Explore Historical 311 Demand Data

## Purpose

Use this guide to implement and verify UC-07 as a typed historical-demand exploration experience that reuses the approved dataset lineage from UC-02 and adds only the analysis-specific persistence needed for warnings, no-data handling, and outcome observability.

## Implementation Outline

1. Reuse upstream lineage entities:
   - `IngestionRun`
   - `DatasetVersion`
   - `ValidationRun`
   - `CleanedDatasetVersion`
   - `CurrentDatasetMarker`
2. Add only the UC-07 analysis-specific persistence:
   - `HistoricalDemandAnalysisRequest`
   - `HistoricalDemandAnalysisResult`
   - `HistoricalDemandSummaryPoint`
   - `HistoricalAnalysisOutcomeRecord`
3. Build one backend historical-analysis path that:
   - resolves the approved cleaned dataset lineage from UC-02
   - accepts service category, time range, and supported reliable geography filters
   - retrieves matching historical demand data
   - aggregates it into a normalized summary suitable for chart, table, or combined display
   - records success, warning, no-data, and failure outcomes
4. Preserve supported-filter and warning rules:
   - only expose geography levels already available and consistently reliable in stored historical data
   - warn before running exceptionally large requests
   - preserve selected filter context when warning, no-data, or error states are shown
5. Keep route handlers thin:
   - `GET` available analysis context or filters if needed
   - `POST` historical analysis request
   - `POST` render-event reporting when the client finishes rendering or fails to render
   - all business decisions in services
   - all persistence in repositories
6. Implement a typed frontend analysis interface that:
   - consumes only the normalized backend contract
   - renders historical demand patterns as charts, tables, or both
   - shows clear warning, no-data, and error states without partial misleading output

## Acceptance Alignment

Map implementation and tests directly to [UC-07](/home/asiad/ece493/311-forecast-system/docs/UC-07.md):

- Main Success: Historical demand interface opens, filters are shown, matching results are retrieved, aggregated, displayed, and logged
- Extension 3a: High-volume request warns before retrieval and proceeds only after planner acknowledgment
- Extension 4a: No matching data shows a clear no-data message
- Extension 4b: Data retrieval failure shows an error state
- Extension 6a: Visualization rendering failure shows an error state

## Suggested Test Layers

- Unit tests for filter normalization, supported-geography enforcement, aggregation selection, and high-volume warning detection
- Integration tests across approved-dataset lookup, historical query execution, summary persistence, and terminal outcome recording
- Contract tests for [historical-demand-api.yaml](/home/asiad/ece493/311-forecast-system/specs/007-historical-demand-exploration/contracts/historical-demand-api.yaml)
- Frontend component and interaction tests for filter selection, warning acknowledgement, chart/table rendering, and no-data or error-state presentation

## Exit Conditions

Implementation is ready for task breakdown when:

- UC-07 reads historical demand lineage from UC-02 without redefining upstream dataset entities
- Geography filter options are limited to supported reliable levels only
- High-volume requests warn before retrieval and preserve selected filters
- Successful results are returned as normalized historical summaries rather than raw source rows
- No-data and failure outcomes remain queryable and clearly visible to planners
- The frontend consumes typed backend contracts only and never reads storage directly
