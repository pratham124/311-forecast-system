# Feature Specification: Generate 7-Day Demand Forecast

**Feature Branch**: `004-weekly-demand-forecast`  
**Created**: 2026-03-13  
**Status**: Draft  
**Input**: User description: "Create the specification for use case 4 based on the UC-04.md file in the docs/ directory. Do this in a new branch that is prefixed with 004."

## Governing References & External Dependencies

- Governing use case: `docs/UC-04.md`
- Governing acceptance suite: `docs/UC-04-AT.md`
- Primary demand source dependency: City of Edmonton 311 Socrata dataset (`https://data.edmonton.ca/resource/q7ua-agfg.json`) plus archived Edmonton yearly datasets when longer history is required.
- Weather enrichment dependency: Government of Canada MSC GeoMet (Edmonton-area station selection).
- Holiday enrichment dependency: Nager.Date Canada API.

## Clarifications

### Session 2026-03-13

- Q: How should "current forecast" be defined for reuse logic? → A: Calendar week: one forecast per operational week.
- Q: Which week boundary defines the operational calendar week? → A: Week starts Monday 00:00 in local operational timezone.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate Weekly Forecast (Priority: P1)

As an Operational Manager, I can request a 7-day demand forecast so I can plan crew and equipment allocation for the upcoming week.

**Why this priority**: This is the core business outcome of UC-04 and directly supports weekly operational planning decisions.

**Independent Test**: Can be fully tested by triggering a forecast request when valid data is available and confirming that a new 7-day forecast is produced, stored, and marked current.

**Acceptance Scenarios**:

1. **Given** validated operational data is available and no current weekly forecast exists, **When** the Operational Manager requests a weekly forecast, **Then** the system generates a forecast for each of the next 7 days and marks it as current.
2. **Given** the scheduled weekly forecast event occurs and required data is available, **When** the event triggers, **Then** the system generates and stores a new 7-day forecast and logs successful completion.
3. **Given** the automated daily regeneration event occurs and required data is available, **When** the event triggers, **Then** the system executes the same weekly forecast workflow and records the run outcome.

---

### User Story 2 - Reuse Current Forecast (Priority: P2)

As an Operational Manager, I receive the existing current 7-day forecast when one is already available so I can avoid waiting for an unnecessary regeneration.

**Why this priority**: Preventing unnecessary reruns improves responsiveness and operational continuity while preserving trust in the current forecast.

**Independent Test**: Can be tested by creating a current weekly forecast, requesting a new forecast, and confirming the existing forecast is returned without creating a replacement.

**Acceptance Scenarios**:

1. **Given** a forecast is already marked current for the same operational calendar week, **When** the Operational Manager requests a weekly forecast, **Then** the system returns the current forecast and logs that an existing forecast was served.

---

### User Story 3 - Maintain Continuity on Failures (Priority: P3)

As an Operational Manager, I can rely on the last valid weekly forecast when forecast generation fails so planning can continue without interruption.

**Why this priority**: This protects planning operations from disruption during data, forecasting, or storage failures.

**Independent Test**: Can be tested by forcing each failure condition (missing data, forecasting error, storage failure) and confirming no invalid forecast is promoted while the previous valid forecast remains available.

**Acceptance Scenarios**:

1. **Given** required data is missing or unusable, **When** forecast generation is triggered, **Then** the system records a failed run and keeps the prior valid forecast as current.
2. **Given** the forecasting process encounters an execution error, **When** generation fails, **Then** the system logs the failure reason and does not publish a new forecast.
3. **Given** a forecast is generated but cannot be saved, **When** storage fails, **Then** the system marks the run failed and retains the previously current forecast.

### Edge Cases

- Geographic information is incomplete: the system publishes category-level forecasts only and records that geographic segmentation was unavailable.
- Multiple requests occur while a same-week generation run is in progress: the system prevents duplicate same-week runs and returns the in-progress run context.
- Forecast output contains missing or invalid values for one or more categories: the system marks the run failed and keeps the previous valid forecast active.
- There is no previous valid forecast and generation fails: the system reports that no current forecast is available and logs the failure with cause.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST allow an Operational Manager to request generation of a 7-day demand forecast on demand.
- **FR-002**: The system MUST support scheduled weekly forecast generation without manual initiation.
- **FR-003**: The system MUST retrieve the latest validated operational dataset before starting forecast generation.
- **FR-004**: The system MUST generate demand forecasts for each day in the next 7-day horizon.
- **FR-005**: The system MUST provide forecast output segmented by service category.
- **FR-006**: The system MUST provide geographic segmentation when geographic data is available and complete enough for segmentation.
- **FR-007**: The system MUST persist each successful forecast run and designate exactly one forecast as current for operational use.
- **FR-008**: If a current forecast already exists for the same operational calendar week, the system MUST return that forecast instead of rerunning generation.
- **FR-014**: The system MUST define each operational calendar week as Monday 00:00 through Sunday 23:59 in the local operational timezone.
- **FR-009**: If required data is unavailable, the system MUST stop generation, mark the run as failed, and keep the prior valid forecast unchanged.
- **FR-010**: If forecasting execution fails, the system MUST mark the run as failed and keep the prior valid forecast unchanged.
- **FR-011**: If forecast storage fails, the system MUST mark the run as failed and keep the prior valid forecast unchanged.
- **FR-012**: The system MUST log all forecast run outcomes, including success, failure reason, trigger type (scheduled or on-demand), and completion timestamp.
- **FR-013**: The system MUST make the current forecast retrievable for operational planning immediately after it is marked current.
- **FR-015**: The system MUST source forecast demand inputs from the City of Edmonton 311 Socrata dataset and include archived Edmonton yearly datasets when additional historical depth is required.
- **FR-016**: The system MUST source weather enrichment from Government of Canada MSC GeoMet using an Edmonton-area station selection policy.
- **FR-017**: The system MUST source holiday enrichment from the Nager.Date Canada API.
- **FR-018**: The system MUST produce and persist predictive quantiles `P10`, `P50`, and `P90` for each forecast bucket.
- **FR-019**: The system MUST produce and persist a baseline comparator value for each forecast bucket.
- **FR-020**: The system MUST perform automated daily regeneration attempts for the active weekly forecast product in addition to supporting weekly scheduled generation and on-demand requests.
- **FR-021**: If a forecast generation run for the same operational calendar week is already in progress, the system MUST prevent starting a duplicate run and return the in-progress run context instead.
- **FR-022**: Only the Operational Manager role MUST be able to trigger forecast generation; read access to current forecast and run status MUST be limited to authorized operations roles, and unauthorized roles MUST be denied.

### Key Entities *(include if feature involves data)*

- **Forecast Run**: A single execution attempt with trigger type, start/end time, status, and failure reason when applicable.
- **Forecast Version**: A produced 7-day forecast dataset associated with one successful run and marked as current or historical.
- **Forecast Bucket**: One forecasted demand value tied to a specific day, service category, and optional geography.
- **Current Forecast Marker**: The designation that identifies which forecast version is the active one for planning.
- **Validated Operational Dataset**: The approved input dataset used to generate forecasts.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of successful forecast runs produce 7 daily demand values per included service category for the full upcoming week.
- **SC-002**: At least 95% of on-demand forecast requests return either a newly generated current forecast or an existing current forecast within 2 minutes.
- **SC-003**: In 100% of failed generation attempts, the previously valid forecast remains available for operational use.
- **SC-004**: At least 98% of scheduled weekly forecast events complete with a recorded outcome (success or explicit failure) within 15 minutes of trigger time.
- **SC-005**: For periods with complete geographic data, 100% of published forecasts include geographic segmentation for all eligible categories.
- **SC-006**: 100% of successful forecast versions persist `P10`, `P50`, `P90`, and baseline comparator values for each forecast bucket.
- **SC-007**: 100% of overlapping trigger requests for the same operational week while a run is in progress are deduplicated to a single active run.

## Assumptions & Dependencies

- Operational Manager can trigger and view weekly forecasts; additional authorized operations roles may have read-only access.
- A "current" forecast refers to the active forecast version for one operational calendar week.
- The operational calendar week starts Monday at 00:00 and ends Sunday at 23:59 in local operational timezone.
- Validated operational data from earlier pipeline stages is available before forecast generation starts.
- Forecast accuracy thresholds are out of scope for this use case and will be defined in a separate model-governance specification.


## Post-Implementation Alignment Notes

- Weekly trigger, run-status, and current-weekly retrieval are implemented as backend-only FastAPI routes under `/api/v1`.
- Weekly week boundaries are enforced as Monday 00:00 through Sunday 23:59:59 in the configured operational timezone.
- Same-week reuse records `served_current`, and concurrent same-week trigger attempts deduplicate to the active run.
- Category-only output remains valid when geography is incomplete; missing approved input, engine failure, and storage failure do not replace the active weekly forecast.
