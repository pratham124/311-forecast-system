# Feature Specification: Evaluate Forecasting Engine Against Baselines

**Feature Branch**: `006-evaluate-forecast-baselines`  
**Created**: 2026-03-13  
**Status**: Draft  
**Input**: User description: "Create the specification for use case 6 using UC-06.md in docs/. Make this in a new branch prefixed with 006 like we have for the previous 5 use cases."

## Governing References & Dependencies

- Governing use case: `docs/UC-06.md`
- Governing acceptance suite: `docs/UC-06-AT.md`
- Actuals lineage dependency: the approved cleaned dataset lineage produced by UC-02
- Forecast lineage dependency: the current persisted daily forecast product from UC-03 and the current persisted weekly forecast product from UC-04

## Clarifications

### Session 2026-03-13

- Q: How should UC-06 define the evaluation scope across forecast products? → A: Evaluate daily and weekly forecast products separately.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Review Whether the Forecasting Engine Beats Baselines (Priority: P1)

As a City Planner, I can run or receive a completed evaluation that compares the forecasting engine against agreed baseline methods so I can decide whether the forecasting engine is delivering meaningful predictive improvement.

**Why this priority**: This is the core purpose of UC-06. Without a trustworthy comparison to baseline methods, the organization cannot judge whether the forecasting engine is worth using as the primary planning input.

**Independent Test**: Can be fully tested by starting an evaluation when historical demand, recent forecast outputs, and baseline methods are available and confirming that the system produces stored comparison results for planner review.

**Acceptance Scenarios**:

1. **Given** historical demand, recent forecast outputs, and configured baseline methods are available, **When** the City Planner starts an evaluation, **Then** the system compares the forecasting engine with the baseline methods against actual outcomes and stores the results.
2. **Given** a scheduled evaluation cycle begins with all required inputs available, **When** the evaluation runs, **Then** the system completes the comparison and makes the resulting performance summary available for review.
3. **Given** an evaluation completes successfully, **When** the City Planner reviews the results, **Then** the system presents performance metrics for both the forecasting engine and each included baseline method for the evaluated daily or weekly forecast product.
4. **Given** an authenticated and authorized City Planner retrieves the latest successful evaluation, **When** the result is displayed, **Then** the system includes a comparison summary stating whether the forecasting engine outperformed, matched, or underperformed the included baselines for that evaluated product.

---

### User Story 2 - Understand Performance by Category and Time Window (Priority: P2)

As a City Planner, I can review aggregated evaluation results by service category and time period so I can identify where the forecasting engine performs better, similarly, or worse than the baselines.

**Why this priority**: A single overall score is not sufficient for operational decision-making. Planners need segmented results to understand whether the model is reliable across the parts of the business that matter most.

**Independent Test**: Can be fully tested by completing an evaluation on data that spans multiple service categories and time windows, then confirming the results show both overall and segmented comparisons.

**Acceptance Scenarios**:

1. **Given** evaluation data includes multiple service categories, **When** the evaluation completes, **Then** the system aggregates and stores comparison results for each included category.
2. **Given** evaluation data spans multiple time periods, **When** the City Planner reviews the evaluation, **Then** the system provides results that distinguish performance across those time periods.
3. **Given** a metric cannot be computed for one category or time period, **When** the evaluation completes, **Then** the system excludes the invalid metric from that segment and identifies that the segment was only partially evaluated.

---

### User Story 3 - Preserve the Last Reliable Evaluation When Failures Occur (Priority: P3)

As a City Planner, I can rely on the last valid evaluation remaining available when a new evaluation fails so I do not lose trusted evidence about forecasting performance.

**Why this priority**: Evaluation failures should not replace dependable results with incomplete or misleading information. Preserving the last trusted evaluation protects continuity and auditability.

**Independent Test**: Can be fully tested by forcing missing-data, baseline-failure, missing-forecast, and storage-failure conditions and confirming that no invalid new evaluation replaces the prior valid results.

**Acceptance Scenarios**:

1. **Given** required historical demand data or forecast outputs are unavailable, **When** evaluation is triggered, **Then** the system records the run as failed and keeps the previous valid evaluation available.
2. **Given** one or more baseline methods fail before comparison can complete, **When** the evaluation run stops, **Then** the system logs the failure reason and does not publish a new official evaluation.
3. **Given** evaluation metrics are computed but the results cannot be stored, **When** the save attempt fails, **Then** the system marks the run as failed and preserves the previous valid evaluation as the current official result.

### Edge Cases

- Historical demand is available for only part of the requested evaluation window: the system should fail the run if the missing portion prevents a valid comparison, rather than comparing mismatched periods.
- One baseline method is configured but produces invalid outputs while others succeed: the system should record the failure and avoid publishing a new official evaluation unless the resulting comparison still meets the defined evaluation criteria.
- A metric cannot be computed for a category because actual values make the calculation invalid: the system should exclude that metric for the affected segment, continue with valid metrics, and note the omission in the results.
- Forecast outputs cover a different time window than the available actual outcomes: the system should treat the affected comparison scope as invalid and avoid presenting it as a completed evaluation.
- Daily and weekly forecast products are both available for review at the same time: the system should keep their evaluation results separate rather than merging them into a single combined comparison.
- An unauthenticated or unauthorized actor attempts to trigger or retrieve an evaluation result: the system should reject the request without exposing protected evaluation data or changing official evaluation state.
- No prior valid evaluation exists and a new evaluation fails: the system should show that no current evaluation is available and clearly report the failure reason.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST allow a City Planner to initiate an evaluation of the forecasting engine against configured baseline methods.
- **FR-002**: The system MUST support scheduled evaluation runs without manual initiation.
- **FR-003**: The system MUST retrieve the historical demand data, recent forecast outputs, and actual outcomes required to evaluate the forecasting engine and baseline methods over the same comparison scope for a single forecast product at a time.
- **FR-004**: The system MUST generate comparison forecasts using the agreed baseline methods for the same scope used to evaluate the forecasting engine.
- **FR-005**: The system MUST compare forecasting engine predictions and baseline predictions against actual outcomes before producing evaluation results.
- **FR-006**: The system MUST calculate and store performance metrics for the forecasting engine and for each included baseline method.
- **FR-007**: The system MUST include `seasonal_naive` and `moving_average` as the initial named baseline methods in published UC-06 results.
- **FR-008**: The system MUST support at least the following evaluation metrics in the published results: mean absolute error, root mean square error, and mean absolute percentage error.
- **FR-009**: The system MUST aggregate evaluation results across the service categories included in the evaluated scope.
- **FR-010**: The system MUST aggregate evaluation results across the time periods included in the evaluated scope.
- **FR-011**: The system MUST keep evaluation runs, stored results, and published summaries separate for the daily forecast product and the weekly forecast product.
- **FR-012**: The system MUST make the latest successful evaluation results available for planner review after storage completes successfully.
- **FR-013**: The system MUST record each evaluation run with its trigger type, evaluated scope, forecast product, completion status, timestamps, and failure reason when applicable.
- **FR-014**: If required historical data is unavailable, the system MUST mark the evaluation as failed and MUST NOT replace the previous valid evaluation results.
- **FR-015**: If required forecast outputs are unavailable, the system MUST mark the evaluation as failed and MUST NOT replace the previous valid evaluation results.
- **FR-016**: If a baseline method fails before valid comparison results are produced, the system MUST mark the evaluation as failed and MUST NOT replace the previous valid evaluation results.
- **FR-017**: If one or more metrics cannot be computed for a subset of categories or time periods, the system MUST exclude only the invalid metric results for the affected subsets, continue the evaluation for valid subsets, and identify the exclusions in the stored results.
- **FR-018**: If evaluation results cannot be stored successfully, the system MUST mark the evaluation as failed and MUST NOT designate the new run as the official evaluation result.
- **FR-019**: The system MUST preserve the most recent valid evaluation results as the official reference until a newer evaluation run is fully completed and stored successfully.
- **FR-020**: The system MUST make it clear in the published results which baseline methods were included in the comparison and which metrics or segments were excluded.
- **FR-021**: The system MUST ensure that comparisons are only published when the forecasting engine, baseline forecasts, and actual outcomes refer to the same evaluation scope.
- **FR-022**: The system MUST log successful and failed evaluation completions for operational monitoring and later review.
- **FR-023**: The system MUST require authenticated access for evaluation triggering and evaluation-result retrieval, and it MUST enforce authorization in the backend so only permitted City Planner or authorized analytics roles can access UC-06 functions.
- **FR-024**: The system MUST include a published comparison summary for each stored evaluation result that states whether the forecasting engine outperformed, matched, or underperformed the included baselines for that forecast product and evaluation scope.

### Key Entities *(include if feature involves data)*

- **Evaluation Run**: A single attempt to compare the forecasting engine with one or more baseline methods for one forecast product, including trigger source, evaluated scope, timestamps, status, and failure details.
- **Baseline Method**: A predefined reference forecasting approach used to judge whether the forecasting engine provides better predictive performance.
- **Evaluation Result**: The stored outcome of a completed run, including metric values, compared methods, segmented summaries, and any excluded portions.
- **Evaluation Segment**: A distinct service-category or time-period slice within the overall evaluation scope for which results may be aggregated and reviewed separately.
- **Official Evaluation Snapshot**: The most recent successfully stored evaluation result that is considered the authoritative reference for planner review.

### Assumptions

- The City Planner is the primary business actor who can review evaluation outcomes and initiate an evaluation when needed.
- Scheduled evaluations occur on a regular operational cadence, but the exact weekly or monthly schedule is defined outside this specification.
- Daily and weekly forecast products are evaluated as separate products, each with its own runs, stored results, and official reference outcome.
- `seasonal_naive` and `moving_average` are the initial required baseline methods for UC-06, and any future additional baseline method must appear in published results under a stable explicit method label.
- Published evaluation results may contain partial metric coverage for specific segments only when the omitted metrics are clearly identified and the remaining results are still valid.
- A new evaluation becomes the official reference only after the full result set has been stored successfully.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: At least 95% of scheduled or planner-initiated evaluation runs with all required inputs available complete and publish reviewable results within 30 minutes of the trigger time.
- **SC-002**: In 100% of successful evaluation runs, the published results include metric values for the forecasting engine and every included baseline method across the evaluated scope.
- **SC-003**: In 100% of successful evaluation runs that span multiple service categories or time periods, the stored results include both an overall comparison summary and segmented results for each included category or time period.
- **SC-004**: In 100% of runs where a metric is invalid for only part of the scope, the published results identify the excluded metric segments and still provide valid results for the remaining scope.
- **SC-005**: In 100% of failed evaluation runs caused by missing data, baseline failures, missing forecast outputs, or storage failures, the previous official evaluation remains available for review and is not replaced by incomplete results.
- **SC-006**: In at least 90% of completed evaluations reviewed by City Planners, the planner can determine from the published results whether the forecasting engine outperformed the included baselines without consulting raw underlying data.
- **SC-006**: In at least 90% of completed evaluations reviewed by City Planners, the published results include an explicit comparison summary that lets the planner determine whether the forecasting engine outperformed, matched, or underperformed the included baselines without consulting raw underlying data.
