# Feature Specification: View Forecast Accuracy and Compare Predictions to Actuals

**Feature Branch**: `014-uc-14-forecast-accuracy`  
**Created**: 2026-03-13  
**Status**: Draft  
**Input**: User description: "docs/UC-14.md, docs/UC-14-AT.md"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Review forecast accuracy for a selected scope (Priority: P1)

As a city planner, I want to open the forecast performance analysis interface and see recent predictions compared to actual demand with clear accuracy metrics so that I can evaluate forecast quality and build trust in the system.

**Why this priority**: This is the primary business outcome of the feature. Without a successful comparison view that combines forecast values, actual values, and accuracy metrics, UC-14 does not deliver operational value.

**Independent Test**: Can be fully tested by opening the forecast performance analysis interface for a scope with seeded historical forecasts, actual demand, and evaluation metrics, then verifying that the system retrieves the required data, aligns it correctly, and renders comparison visuals with interpretable metrics.

**Acceptance Scenarios**:

1. **Given** an authenticated and authorized city planner opens the forecast performance analysis interface, **When** the interface loads, **Then** the system shows the performance analysis view for the last 30 completed days by default without an error state and exposes any supported scope controls such as time range, category, or geography filters.
2. **Given** historical forecasts and actual demand exist for the selected scope, **When** the city planner requests forecast performance data, **Then** the system retrieves the stored historical forecasts and the corresponding actual demand for the same periods and scope.
3. **Given** forecasts and actual demand are retrieved successfully, **When** the system processes the request, **Then** it retrieves or computes the required forecast accuracy metrics of MAE, RMSE, and MAPE for the same scope and time windows.
4. **Given** forecasts, actuals, and metrics are available, **When** the system prepares the comparison view, **Then** it aligns forecasts and actuals to the same time buckets and prepares visualization-ready data without off-by-one period mismatches.
5. **Given** the visualization-ready comparison data is available and visualization services are operational, **When** the system renders the performance view, **Then** it displays clear prediction-versus-actual comparisons and the interpretable accuracy metrics MAE, RMSE, and MAPE for the selected scope.
6. **Given** a forecast performance view renders successfully, **When** operational logs are reviewed, **Then** they show successful retrieval, alignment, preparation, and visualization outcomes for the same request using a request id or correlation id where available.

---

### User Story 2 - Continue analysis when metrics are unavailable (Priority: P2)

As a city planner, I want the system to show prediction-versus-actual comparisons even when summary metrics are missing, so that I can still assess forecast behavior without being misled about metric availability.

**Why this priority**: Missing metrics should not block useful analysis when the underlying forecast and actual data are available, but this depends on the core comparison workflow already existing.

**Independent Test**: Can be fully tested by triggering forecast performance analysis for a scope where historical forecasts and actual demand exist but evaluation metrics are missing, then verifying that the system logs the condition and renders comparisons without metrics when supported.

**Acceptance Scenarios**:

1. **Given** historical forecasts and actual demand are available for the selected scope but precomputed evaluation metrics are missing, **When** the city planner requests forecast performance data, **Then** the system first logs the missing precomputed metrics condition and attempts on-demand computation for the same scope and time window.
2. **Given** forecasts and actuals are available but both precomputed metrics retrieval and on-demand metric computation fail, **When** the system prepares the performance view, **Then** it displays prediction-versus-actual comparisons without summary metrics and clearly indicates that metrics are unavailable.
3. **Given** forecasts and actuals are unavailable for safe comparison, **When** the request is processed, **Then** the system shows a clear error or unavailable state rather than presenting incomplete or misleading performance information.

---

### User Story 3 - See a clear failure state when required data or visualization is unavailable (Priority: P3)

As a city planner, I want a clear error state when historical forecasts, actual demand, or rendering fails so that I know the analysis is unavailable and operations staff can trace the failure.

**Why this priority**: Failure handling protects trust and observability, but it depends on the main retrieval and visualization flow already existing.

**Independent Test**: Can be fully tested by forcing missing historical forecasts, missing actual demand, and a visualization rendering failure, then verifying that the system logs each condition and shows an error state without displaying misleading comparison output.

**Acceptance Scenarios**:

1. **Given** historical forecast data is unavailable for the selected scope, **When** the city planner requests forecast performance data, **Then** the system logs the missing forecast condition and shows an error state without comparison visuals.
2. **Given** historical forecasts are available but actual demand data is unavailable for the selected scope, **When** the city planner requests forecast performance data, **Then** the system logs the missing actual-data condition and shows an error state without valid comparisons.
3. **Given** forecasts and actuals are available and the system begins rendering the performance view, **When** the visualization module fails during chart or table rendering, **Then** the system logs the rendering failure and shows an error state instead of partial or corrupted visuals.

### Edge Cases

- The user opens the forecast performance analysis interface with default scope settings, and the system must load the view for the last 30 completed days without showing an error before any optional filter changes are made.
- Forecast and actual datasets overlap only partially across time buckets, and the system must align only matching periods rather than comparing mismatched intervals.
- A known comparison bucket is spot-checked, and the system must present forecast and actual values for the same interval without an off-by-one shift.
- Precomputed evaluation metrics are missing while forecasts and actuals are available, and the system must attempt on-demand metric computation before falling back to comparison output with explicit messaging that metrics are unavailable.
- Historical forecast data is missing for the selected scope, and the system must not present any performance insight derived from incomplete forecast history.
- Actual demand data is missing for the selected scope, and the system must not show any comparison that implies forecast accuracy has been evaluated.
- Visualization rendering fails after successful retrieval and preparation, and the system must avoid showing a partial or corrupted chart or table.
- Logs are reviewed after either a successful request or a failure, and the relevant entries must be traceable by request id or correlation id where available.
- An unauthenticated user or an authenticated user without forecast-performance access attempts to load the analysis view, and the system must reject the request without exposing performance data.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST allow an authenticated and authorized city planner to access the forecast performance analysis interface.
- **FR-001a**: The system MUST reject unauthenticated or unauthorized forecast-performance requests without exposing historical forecasts, actual demand data, or accuracy metrics.
- **FR-001b**: The system MUST accept forecast-performance render-outcome reports only from an authenticated and authorized caller for the prepared request being reported and MUST reject mismatched or unauthorized render-event submissions.
- **FR-002**: When the forecast performance analysis interface loads, the system MUST display the analysis view for the default scope of the last 30 completed days, or for a user-selected scope, without immediately showing an error state when required services are available.
- **FR-003**: The system MUST support retrieving stored historical forecasts for the requested time range and scope.
- **FR-004**: The system MUST retrieve actual demand data corresponding to the same periods and scope as the requested historical forecasts.
- **FR-005**: The system MUST retrieve the required precomputed forecast accuracy metrics of MAE, RMSE, and MAPE for the requested scope when those metrics are available.
- **FR-006**: If precomputed metrics are not available, the system MUST attempt on-demand computation of MAE, RMSE, and MAPE for the same scope and time windows as the retrieved forecasts and actuals.
- **FR-007**: The system MUST align historical forecasts and actual demand to matching time buckets before presenting any comparison output.
- **FR-008**: The system MUST prepare aligned forecasts, actuals, and any available metrics into a visualization-ready representation for the requested scope.
- **FR-009**: When aligned comparison data is available and rendering succeeds, the system MUST display prediction-versus-actual comparisons and the available forecast accuracy metrics, including MAE, RMSE, and MAPE when available, in charts, tables, or both.
- **FR-010**: The system MUST present the comparison output in a way that allows the city planner to interpret forecast performance over time for the selected scope.
- **FR-011**: The system MUST log successful forecast retrieval, actual-data retrieval, metric retrieval or computation, alignment, preparation, and visualization outcomes for each forecast-performance request.
- **FR-012**: If historical forecast data is unavailable for the selected scope, the system MUST log the missing forecast-data condition and MUST display an error state instead of comparison visuals.
- **FR-013**: If actual demand data is unavailable for the selected scope, the system MUST log the missing actual-data condition and MUST display an error state instead of comparison visuals.
- **FR-014**: If precomputed evaluation metrics are missing, the system MUST log the missing-metrics condition and MUST attempt on-demand metric computation.
- **FR-015**: If forecasts and actuals are available and on-demand metric computation also fails, the system MUST display prediction-versus-actual comparisons without summary metrics and MUST clearly indicate that metrics are unavailable.
- **FR-016**: If forecasts and actuals are missing or cannot be aligned for safe comparison, the system MUST display a clear error or unavailable state rather than incomplete or misleading performance information.
- **FR-017**: If the visualization module fails while rendering the performance view, the system MUST log the rendering failure and MUST display an error state instead of partial or corrupted visuals.
- **FR-018**: The system MUST preserve enough request context in operational logs to correlate interface access, data retrieval, alignment, preparation, and rendering outcomes for the same forecast-performance request.
- **FR-019**: The system MUST ensure that forecast values and actual values shown for any comparison bucket refer to the same aligned interval and scope.

### Key Entities *(include if feature involves data)*

- **Forecast Performance Request**: A user-initiated request to load forecast accuracy analysis for a selected time range and scope, defaulting to the last 30 completed days when the user does not override it, including any category or geography filters and the request or correlation identifier used for tracing outcomes.
- **Historical Forecast Snapshot**: A retained forecast output from earlier forecast runs that is eligible for comparison against realized demand for the same period and scope.
- **Actual Demand Observation**: The realized 311 demand record or aggregated demand value corresponding to the same comparison period and scope as a historical forecast snapshot.
- **Forecast Accuracy Metric**: A retained or computed evaluation result, specifically MAE, RMSE, or MAPE for this feature, associated with a specific forecast-performance request scope and time window.
- **Aligned Performance Series**: The comparison-ready pairing of historical forecast values and actual demand values across matched time buckets for a selected scope.
- **Performance Visualization State**: The user-visible outcome of a forecast-performance request, represented as loading, rendered with metrics, rendered without metrics, unavailable, or error.
- **Forecast Accuracy Render Event**: An authenticated client report that records whether a prepared forecast-performance result rendered successfully or failed for the same request context.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In stakeholder acceptance testing, 100% of authorized requests to the forecast performance analysis interface for scopes with available data load the analysis view without an initial error state.
- **SC-002**: In stakeholder acceptance testing, 100% of forecast-performance requests with available historical forecasts, actual demand, and metrics render prediction-versus-actual comparisons and interpretable metrics for the same scope and time windows.
- **SC-003**: In stakeholder acceptance testing, 100% of spot-checked comparison buckets show forecast and actual values aligned to the same interval without an off-by-one mismatch.
- **SC-004**: In stakeholder acceptance testing, 100% of requests where precomputed metrics are missing but forecasts and actuals are available first attempt on-demand metric computation and, if that computation also fails, still render prediction-versus-actual comparisons with a clear metrics-unavailable message without misleading users.
- **SC-005**: In stakeholder acceptance testing, 100% of missing-forecast, missing-actual, and visualization-rendering failure cases produce a visible error or unavailable state and a traceable log entry for the same request.

## Assumptions

- The active platform already retains historical forecast outputs and realized actual-demand data in forms that can be queried for the same comparison periods and scopes.
- The default analysis window is the last 30 completed days unless the user selects a different supported time range.
- Evaluation metrics may be stored ahead of time or computed on demand, but any metrics shown by this feature correspond to the same scope and time window as the displayed comparisons.
- The required accuracy metrics for this feature are MAE, RMSE, and MAPE.
- Supported scopes may include time range, service category, and optional geography filters when those dimensions are available from earlier forecasting and evaluation use cases.
- The feature is concerned with viewing forecast accuracy and comparisons; it does not change the underlying forecasting, evaluation, or visualization-generation logic established in earlier use cases.
