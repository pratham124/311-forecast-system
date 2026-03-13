# Feature Specification: Generate 1-Day Demand Forecast

**Feature Branch**: `[003-daily-demand-forecast]`  
**Created**: 2026-03-12  
**Status**: Draft  
**Input**: User description: "docs/UC-03.md and docs/UC-03-AT.md"

**Governing Use Case**: `UC-03` in `docs/UC-03.md`  
**Governing Acceptance Test**: `UC-03-AT` in `docs/UC-03-AT.md`

## Clarifications

### Session 2026-03-12

- Q: What time granularity should the 1-day forecast use? → A: Hourly buckets across the next 24 hours.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate a current daily forecast (Priority: P1)

An operational manager requests a demand forecast for the next 24 hours and receives a current forecast in hourly buckets, broken down by service category, with geography included when the available data supports it.

**Why this priority**: This is the core business outcome. Without a current forecast, staffing and dispatch planning for the next day cannot be performed reliably.

**Independent Test**: Can be fully tested by triggering forecast generation when current source data is available and confirming a new forecast is produced, stored, and made available for planning.

**Acceptance Scenarios**:

1. **Given** validated operational data is available and no current forecast exists for the upcoming 24-hour window, **When** an operational manager requests a forecast, **Then** the system provides a newly generated forecast in hourly buckets for the next 24 hours segmented by service category.
2. **Given** validated operational data includes usable geographic information, **When** a new forecast is generated, **Then** the forecast also includes a geographic breakdown for each hourly bucket in the same 24-hour window.
3. **Given** forecast generation succeeds, **When** the forecast is stored, **Then** it becomes the current forecast available for operational use.
4. **Given** an authorized operational manager requests a forecast, **When** no current forecast already covers the requested next 24-hour window, **Then** the system accepts the request as a forecast-generation attempt rather than treating it as a current-forecast read.

---

### User Story 2 - Reuse an already current forecast (Priority: P2)

An operational manager requests a forecast and receives the already current forecast for the next 24 hours instead of waiting for an unnecessary new run.

**Why this priority**: Reusing a valid current forecast avoids redundant processing and gives operations staff immediate access to planning data.

**Independent Test**: Can be fully tested by placing a current forecast in the system, requesting a forecast, and confirming the same forecast is served without creating a replacement.

**Acceptance Scenarios**:

1. **Given** a forecast already exists and is current for the upcoming 24-hour window, **When** an operational manager requests a forecast, **Then** the system serves the existing current forecast.
2. **Given** a current forecast is served instead of regenerated, **When** the request completes, **Then** the system records that the current forecast was reused.
3. **Given** a current forecast exists but does not cover the full requested next 24-hour window of 24 consecutive hourly buckets, **When** an operational manager requests a forecast, **Then** the system does not reuse that forecast as the current result for the request.

---

### User Story 3 - Protect operations from failed or incomplete updates (Priority: P3)

An operational manager continues to have access to the most recent valid forecast when new forecast generation fails or when only a partial breakdown can be produced.

**Why this priority**: Operational planning must remain dependable even when data is missing, forecast generation fails, or only category-level results can be produced.

**Independent Test**: Can be fully tested by simulating missing data, forecast generation failure, incomplete geography, and storage failure, then confirming the current valid forecast remains available and no incomplete update becomes current.

**Acceptance Scenarios**:

1. **Given** the latest required operational data is unavailable, **When** forecast generation is triggered, **Then** the attempt fails and the most recent valid forecast remains available.
2. **Given** geographic data is incomplete but category-level data is sufficient, **When** forecast generation succeeds, **Then** the system publishes a category-only forecast and records that geography was omitted.
3. **Given** a new forecast cannot be stored successfully, **When** generation completes, **Then** the new forecast does not become current and the previously valid forecast remains current.
4. **Given** a requester is not allowed to use a forecast trigger or read surface, **When** the request is received, **Then** the system returns an access denial without recording that denial as a forecast-generation failure outcome.

### Edge Cases

- If the reuse conditions defined for the current forecast are already satisfied for the next 24-hour window, the system should return the existing forecast instead of replacing it.
- If a forecast can be produced only at the service-category level, the system should still make that forecast available in hourly buckets and clearly treat geography as unavailable rather than as zero demand.
- If a failure occurs after forecast calculation but before the forecast is safely stored, no incomplete or unverified forecast should ever become the current forecast.
- If no previous valid forecast exists and a generation attempt fails, the system should report that no current forecast is available rather than presenting partial or stale output as current.
- If an unauthorized or forbidden request is made to a forecast trigger or read surface, the system should deny access without creating or altering a forecast run.
- If a request references a forecast run or current forecast resource that does not exist, the system should return a missing-resource response rather than classifying the condition as a forecast-generation failure.
- If a request or parameter is invalid, the system should return an invalid-request response rather than starting or changing a forecast run.

## Forecast Scope & External Integrations

- This feature is the UC-03 feature-specific 1-day hourly operational forecast and does not replace the constitution's broader default direction of daily next-7-day service-category forecasting.
- Forecast input lineage for UC-03 MUST begin from the approved cleaned dataset produced by UC-02, which itself is derived from the City of Edmonton official 311 Requests dataset.
- If weather enrichment is used for UC-03, it MUST come from Government of Canada MSC GeoMet data through dedicated client, ingestion, or pipeline modules.
- If holiday enrichment is used for UC-03, it MUST come from the Nager.Date Canada API through dedicated client, ingestion, or pipeline modules.
- UC-03 forecasting MUST use a single global LightGBM model with service category encoded as a feature, retain a baseline comparator, and produce predictive quantiles `P10`, `P50`, and `P90`.
- UC-03 training, validation, and inference inputs MUST remain chronologically safe and leakage-free.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST allow forecast generation to be initiated by an operational manager request and by a scheduled event.
- **FR-002**: The system MUST provide a forecast trigger surface whose responsibility is to accept a request for forecast generation for the upcoming 24-hour planning window.
- **FR-003**: The system MUST provide a forecast-run status surface whose responsibility is to report the recorded state and outcome of a forecast run.
- **FR-004**: The system MUST provide a current-forecast read surface whose responsibility is to return the forecast currently designated for operational planning.
- **FR-005**: Operational managers MUST be able to use both the forecast trigger surface and the forecast read surfaces for operational planning.
- **FR-006**: The system MUST require authentication for all forecast trigger and read surfaces.
- **FR-007**: The system MUST return an unauthorized response when a requester is not authenticated for a forecast trigger or read surface.
- **FR-008**: The system MUST return a forbidden response when a requester is authenticated but not permitted to use a forecast trigger or read surface.
- **FR-009**: The system MUST determine whether a current forecast already exists for the exact upcoming 24-hour planning window before generating a replacement.
- **FR-010**: The system MUST return the existing forecast instead of generating a replacement when the current forecast already covers the full requested planning window of 24 consecutive hourly buckets.
- **FR-011**: The system MUST generate a new forecast in hourly buckets covering the next 24 hours when no current forecast exists for that full window and required input data is available.
- **FR-012**: The system MUST treat business conditions such as missing input data, weather or holiday enrichment failure, forecast-processing failure, model-execution failure, and storage failure as forecast-run outcomes rather than as authentication or authorization errors.
- **FR-013**: The system MUST return a missing-resource response when a requested forecast run record or current forecast resource does not exist.
- **FR-014**: The system MUST return an invalid-request response when a forecast request or its parameters are invalid.
- **FR-015**: The system MUST provide forecast results as 24 consecutive hourly buckets that together cover the full next 24-hour planning window without gaps or overlaps.
- **FR-016**: The system MUST provide forecast results for each hourly bucket segmented by service category.
- **FR-017**: The system MUST provide forecast results for each hourly bucket segmented by geography when sufficient geographic data is available.
- **FR-018**: The system MUST publish a category-only forecast when geographic detail is insufficient but the remaining input data is adequate for forecast generation.
- **FR-019**: The system MUST store each successfully generated forecast together with the time window it covers and the dimensions included in the output.
- **FR-020**: The system MUST mark a newly generated forecast as current only after it has been stored successfully.
- **FR-021**: The system MUST retain the most recent valid forecast as the current forecast whenever a new generation attempt fails.
- **FR-022**: The system MUST fail the generation attempt when required operational data for the forecast window is unavailable.
- **FR-023**: The system MUST fail the generation attempt when enrichment or model processing cannot complete successfully.
- **FR-024**: The system MUST fail the generation attempt when the new forecast cannot be stored successfully.
- **FR-025**: The system MUST record the outcome of each forecast request or run, including whether a current forecast was reused, a new forecast was generated, geography was omitted, or the attempt failed.
- **FR-026**: The system MUST retain stored forecast versions and failed forecast-run records as operational history for this feature.
- **FR-027**: The system MUST keep the approved cleaned dataset marker from UC-02 distinct from the current forecast marker used by UC-03.
- **FR-028**: The system MUST use the approved cleaned dataset marker only to identify the active cleaned input dataset and MUST use the current forecast marker only to identify the active forecast result.
- **FR-029**: The system MUST NOT expose raw source payloads, feature matrices, secrets, or model internals in forecast API responses, logs, or operational summaries.
- **FR-030**: The system MUST use the approved cleaned dataset lineage derived from the City of Edmonton official 311 Requests dataset as the primary demand input for UC-03.
- **FR-031**: The system MUST use Government of Canada MSC GeoMet data for any weather enrichment included in UC-03.
- **FR-032**: The system MUST use the Nager.Date Canada API for any holiday enrichment included in UC-03.
- **FR-033**: The system MUST use a single global LightGBM model with service category represented as an input feature and MUST retain a baseline comparator for forecast evaluation.
- **FR-034**: The system MUST persist predictive quantiles `P10`, `P50`, and `P90` for the forecast output alongside the operational forecast values.
- **FR-035**: The system MUST use chronologically safe, leakage-free training, validation, and inference inputs for UC-03 forecasting.

### Key Entities *(include if feature involves data)*

- **Forecast Request**: A manager-initiated or scheduled request to obtain a forecast for the next 24-hour planning window, including the trigger type, request time, and whether the request is for generation, run-status reading, or current-forecast reading.
- **Demand Forecast**: The forecasted demand output for a defined 24-hour window, including 24 consecutive hourly buckets, service-category totals, optional geographic breakdowns, creation time, and current-status designation.
- **Operational Data Snapshot**: The validated source data used to support forecast generation for a request, including service activity history and geographic completeness status.
- **Forecast Run Outcome**: The recorded result of a forecast attempt, including success, reuse of an existing forecast, partial geography handling, or failure reason, and excluding access-denial or invalid-request responses that occur before forecast processing begins.
- **Approved Cleaned Dataset Marker**: The UC-02 marker that identifies the cleaned dataset currently approved for downstream use as forecast input.
- **Current Forecast Marker**: The UC-03 marker that identifies the forecast currently active for operational planning.

### Assumptions

- A "current forecast" means the forecast designated for the next upcoming 24-hour planning window at the time of the request or scheduled run.
- Operational managers need the same forecast outcome whether the request is triggered manually or by schedule.
- Service category segmentation is mandatory for a usable forecast, while geography is optional when source data quality does not support it.
- The forecast is expressed as 24 consecutive hourly demand buckets for the upcoming planning window.
- Security and access-denial responses are separate from forecast-generation outcomes and do not represent a forecast run failure.
- Business failure outcomes for accepted forecast-generation attempts include missing input data, enrichment failure, model-execution failure, and storage failure.
- If a forecast run record or current forecast does not exist, the expected result is a missing-resource response rather than a generation failure outcome.
- If a request or parameter is invalid, the expected result is an invalid-request response rather than a generation failure outcome.
- Detailed coordination of overlapping scheduled and on-demand requests for the same planning window is outside the scope of this feature, except that no incomplete or failed run may replace the current forecast.
- The system may keep historical forecasts, but only one forecast is treated as current for a given planning window.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In at least 95% of successful on-demand generation requests where no current forecast already covers the requested planning window, operational managers can access the newly current next-24-hour forecast within 2 minutes of initiating the request.
- **SC-002**: 100% of successful forecasts include 24 consecutive hourly demand buckets with service-category segmentation for the covered planning window.
- **SC-003**: In at least 95% of requests made while a valid current forecast already exists for the requested planning window, operational managers can access that current forecast within 30 seconds without triggering replacement generation.
- **SC-004**: 100% of failed generation attempts leave the previously valid forecast unchanged as the current forecast.
- **SC-005**: When geographic data is insufficient but category-level forecasting is still possible, 100% of successful runs provide a category-only forecast, clearly indicate that geography is unavailable, and meet the same 2-minute access target as other successful generation requests.
- **SC-006**: 100% of unauthorized, forbidden, missing-resource, and invalid-request responses are reported as access or request errors rather than as forecast-generation failure outcomes.
