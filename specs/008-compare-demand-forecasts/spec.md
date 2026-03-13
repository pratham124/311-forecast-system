# Feature Specification: Compare Demand and Forecasts Across Categories and Geographies

**Feature Branch**: `008-compare-demand-forecasts`  
**Created**: 2026-03-13  
**Status**: Draft  
**Input**: User description: "docs/UC-08.md and docs/UC-08-AT.md"

## Clarifications

### Session 2026-03-13

- Q: When a selected comparison includes some category or geography combinations with missing forecast data, should the system fail the whole request or show partial results? → A: Show partial comparison results for available combinations and explicitly identify the missing combinations.
- Q: If some selected historical and forecast data cannot be aligned to the same category or geographic definitions, should the system show a partial comparison or block the comparison entirely? → A: Show an error state and do not display the comparison if any selected historical and forecast data cannot be aligned to common definitions.
- Q: To stay congruent with `docs/UC-08.md`, should retrieval failure be made explicit in the spec, should partial missing-forecast behavior remain as a clarified extension, and should stronger-than-use-case requirement wording be softened? → A: Yes. Make retrieval failure explicit as a requirement derived from the failed end condition, keep partial missing-forecast behavior as a clarified extension, and soften stronger-than-use-case wording.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Compare selected categories and regions (Priority: P1)

A city planner compares historical demand and forecast demand for selected service categories, optional geographic areas, and a single continuous time period so they can identify where future demand is likely to differ from past patterns.

**Why this priority**: This is the core planning workflow and the main reason the feature exists.

**Independent Test**: Can be fully tested by selecting one or more service categories, optionally selecting one or more geographic areas, choosing a continuous time range, and confirming the system returns a single comparison view that matches the requested scope.

**Acceptance Scenarios**:

1. **Given** historical and forecast data exist for the selected categories, geographies, and time period, **When** the city planner submits the comparison request, **Then** the system displays a comparative view that includes both historical demand and forecast demand for only the selected scope.
2. **Given** multiple categories and geographies are selected, **When** the comparison results load, **Then** the system presents the results in a format that allows the planner to distinguish differences across categories, regions, and time periods.
3. **Given** a comparison is already displayed, **When** the city planner changes any filter and submits a new comparison request, **Then** the prior comparison is replaced by the new request’s in-progress state and only the new request’s outcome may remain visible.

---

### User Story 2 - Continue with large comparison requests (Priority: P2)

A city planner is warned before running a very large comparison request so they can choose whether to continue, rather than being surprised by a long-running analysis.

**Why this priority**: Large comparative requests are likely during city-wide planning and budgeting, but the warning is secondary to the base comparison capability.

**Independent Test**: Can be tested by submitting a request that exceeds the large-request threshold and confirming the planner sees a warning and can choose to proceed.

**Acceptance Scenarios**:

1. **Given** the selected categories, geographies, and time range create an unusually large comparison request, **When** the city planner applies the filters, **Then** the system warns about the expected delay before starting the comparison.
2. **Given** a high-volume warning is shown, **When** the city planner chooses to continue, **Then** the system proceeds with the request and shows that processing is still underway until a result or failure state is available.

---

### User Story 3 - Understand incomplete or failed comparisons (Priority: P3)

A city planner receives clear partial-result or error states when comparison data is missing, incompatible, or cannot be displayed, so they do not make decisions from misleading information.

**Why this priority**: Reliable planning depends on understanding when a comparison is incomplete or invalid.

**Independent Test**: Can be tested by triggering missing historical data, missing forecast data, historical retrieval failure, forecast retrieval failure, alignment failure, and display failure conditions, then confirming the system shows the correct partial or error outcome for each case.

**Acceptance Scenarios**:

1. **Given** only forecast data is available for the selected scope, **When** the city planner runs the comparison, **Then** the system shows forecast-only results with a message explaining that historical data is unavailable.
2. **Given** only historical data is available for the selected scope, **When** the city planner runs the comparison, **Then** the system shows historical-only results with a message explaining that forecast data is unavailable.
3. **Given** historical demand retrieval fails for the selected scope, **When** the comparison request is processed, **Then** the system logs the historical retrieval failure and shows an error state instead of a comparison.
4. **Given** forecast demand retrieval fails for the selected scope, **When** the comparison request is processed, **Then** the system logs the forecast retrieval failure and shows an error state instead of a comparison.
5. **Given** any selected historical and forecast data cannot be aligned to the same category or geographic definitions, **When** processing reaches that failure point, **Then** the system shows an error state and does not display any comparison for that request.
6. **Given** some selected category or geography combinations have forecast data while others do not, **When** the city planner runs the comparison, **Then** the system shows the available comparisons and explicitly identifies which selected combinations are missing forecast data as a clarified extension beyond the explicit UC-08 alternative flows.
7. **Given** historical data exists for only part of the selected time range, **When** the comparison request is completed, **Then** the system shows forecast data for the full selected range, historical data only for the covered portion, and a message identifying the uncovered historical interval.

### Edge Cases

- A comparison request includes enough categories, regions, or time coverage to create a long-running analysis.
- Historical data exists for only part of the selected period while forecast data exists for the full period.
- Forecast data exists for only some of the selected categories or geographies.
- Forecast data or historical data is missing for only part of a multi-category or multi-geography selection.
- Historical data exists for only part of the selected time range.
- Historical data retrieval fails for the selected comparison request.
- Forecast data retrieval fails for the selected comparison request.
- Historical and forecast data use incompatible time intervals, category labels, or geographic boundaries.
- Any selected data subset fails alignment against the defined category or geographic definitions.
- A planner changes filters after a prior comparison is already shown and expects the new results to fully replace the old scope.
- The system cannot render a comparison after data retrieval and preparation succeed.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a comparison interface where a city planner can select one or more service categories, optionally select zero or more geographic areas at one supported geography level, and select one continuous time range for analysis.
- **FR-001a**: The system MUST treat service category selection as multi-select, geographic-area selection as optional multi-select, and time-range selection as a single continuous range per request.
- **FR-001b**: The system MUST require authenticated access for comparison context retrieval, comparison execution, and render-outcome reporting.
- **FR-001c**: The system MUST accept a render-outcome report only when it is submitted by the authenticated session associated with the executed comparison request or by an equivalently authorized backend component acting for that request.
- **FR-002**: The system MUST retrieve historical demand data that matches the selected categories, geographic areas, and time range.
- **FR-003**: The system MUST retrieve forecast demand data that matches the selected categories, geographic areas, and time range.
- **FR-003a**: The system MUST retrieve historical data only from the approved historical lineage currently available for downstream use and MUST retrieve forecast data only from the active forecast lineage currently available for downstream use.
- **FR-004**: The system MUST align historical demand and forecast demand using a common comparison basis for time, category, and geography before presenting a combined comparison.
- **FR-004a**: The system MUST use hourly normalization only when the selected range is fully covered by an active hourly forecast source and matching historical data can be aligned to hourly buckets, daily normalization when both sources can align to calendar-day buckets, and weekly normalization only when both sources can align to calendar-week buckets for the selected range.
- **FR-005**: The system MUST present comparison results in a format that allows planners to evaluate differences across selected categories, geographies, and time periods.
- **FR-006**: The system MUST ensure displayed results reflect only the categories, geographies, and time range selected by the planner.
- **FR-006a**: When a planner submits a new comparison request, the system MUST replace any previously displayed comparison with the new request’s in-progress state and MUST show only the new request’s final outcome.
- **FR-007**: The system MUST warn the planner before starting a comparison request that exceeds the large-request threshold.
- **FR-007a**: A request exceeds the large-request threshold when it spans more than 366 calendar days or requests more than 10 selected service-category and geographic-area combinations, where a request with no geography selection counts as one geography scope for each selected category.
- **FR-007b**: The high-volume warning MUST identify the selected request scope, state that retrieval has not started yet, and explain that the selected scope is expected to cause a long-running comparison because it exceeds the large-request threshold.
- **FR-008**: The system MUST allow the planner to proceed after acknowledging a high-volume warning.
- **FR-009**: The system MUST show an in-progress state while a comparison request is being retrieved, aligned, or prepared.
- **FR-010**: The system MUST display forecast-only results when no matching historical data is available and MUST identify that historical data is unavailable.
- **FR-010a**: When historical data exists for only part of the selected time range, the system MUST display forecast data for the full selected range, historical data only for the covered interval, and a message that identifies the portion of the selected range with no historical coverage.
- **FR-011**: The system MUST display historical-only results when no matching forecast data is available and MUST identify that forecast data is unavailable.
- **FR-011a**: As a clarified extension to UC-08 and UC-08-AT, the system MUST display partial comparison results when forecast data is available for only some selected categories or geographic areas, and MUST explicitly identify each selected combination whose forecast data is unavailable.
- **FR-011b**: The system MUST log the failure and show an error state when historical demand data required for the selected comparison cannot be retrieved.
- **FR-011c**: The system MUST log the failure and show an error state when forecast demand data required for the selected comparison cannot be retrieved.
- **FR-012**: The system MUST prevent any comparison results from being shown when any selected historical and forecast data cannot be aligned to common time, category, and geographic definitions.
- **FR-013**: The system MUST show an error state when a comparison cannot be completed because of data alignment or result display failures.
- **FR-014**: The system MUST log successful retrieval and visualization outcomes, missing-data conditions, and failure conditions for each comparison request.
- **FR-015**: The system MUST use only defined category and geographic classifications when preparing and presenting results.
- **FR-015a**: A category or geographic classification is defined only when it is part of the approved historical lineage, is recognized by the active forecast lineage used for the request, and can be matched through one canonical identifier or label set across both sources.

### Key Entities *(include if feature involves data)*

- **Comparison Request**: The planner’s selected categories, geographic areas, time range, and request outcome.
- **Comparison Filter Set**: The selected multi-category scope, optional multi-geography scope, and single continuous time range used to define one comparison request.
- **Historical Demand Series**: Time-based demand counts representing observed service demand for a category and geography.
- **Forecast Demand Series**: Time-based projected demand counts representing expected future service demand for a category and geography.
- **Comparison View**: The presented result set that combines historical and forecast demand in a way that supports side-by-side or overlaid analysis.
- **Category Classification**: The defined service-category grouping used to compare demand.
- **Geographic Classification**: The defined geographic-area grouping used to compare demand.

### Assumptions

- City planners already have access to the comparative analysis area as part of the existing analytics product.
- Historical and forecast demand are already available from upstream workflows before this feature is used.
- Defined category and geographic classifications exist and are stable enough to support comparison.
- A request that includes any unalignable selected data is less safe than returning a partial comparison and therefore should fail as a whole.
- When only one data source is available, partial results are more valuable than blocking the planner entirely, provided the limitation is stated clearly.
- When some selected combinations are missing forecast data, the system should still show valid comparisons for the combinations that do have forecast data and clearly identify the missing combinations, even though this behavior is a clarified extension rather than an explicit extension in `docs/UC-08.md`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In usability testing, at least 90% of city planners can complete a comparison across at least two categories and two geographic areas without assistance.
- **SC-002**: For comparison requests within the normal request size threshold, 95% of requests show either results or a clear partial-result or error outcome within 10 seconds, measured from the moment the planner submits the request to the moment the system first displays the terminal outcome for that request.
- **SC-003**: For 100% of requests that span more than 366 calendar days or request more than 10 selected service-category and geographic-area combinations, the system presents a warning before retrieval begins.
- **SC-004**: In validation against seeded reference cases, 100% of comparison outputs match the selected categories, geographies, and time range with no out-of-scope data shown.
- **SC-005**: In failure-path testing, 100% of missing-data, alignment-failure, and display-failure scenarios show a clear non-misleading state instead of an invalid comparison.
- **SC-006**: In mixed-availability test cases, 100% of selected category and geography combinations without forecast data are explicitly identified in the comparison results.
- **SC-007**: In alignment-failure test cases, 100% of requests with any unalignable selected data show an error state and display no comparison results.
- **SC-008**: In historical-retrieval-failure test cases, 100% of failures are logged and show an error state instead of comparison results.
- **SC-009**: In forecast-retrieval-failure test cases, 100% of failures are logged and show an error state instead of comparison results.
