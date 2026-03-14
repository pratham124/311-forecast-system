# Feature Specification: View Public Forecast of 311 Demand by Category

**Feature Branch**: `017-uc-17-public-demand-forecast`  
**Created**: 2026-03-13  
**Status**: Draft  
**Input**: User description: "docs/UC-17.md, docs/UC-17-AT.md"

## Governing References

- Governing use case: `docs/UC-17.md`
- Governing acceptance suite: `docs/UC-17-AT.md`

## Clarifications

### Session 2026-03-13

- Q: Does the public forecast portal require authentication? → A: No. UC-17 is an anonymous public-facing portal and must not require sign-in to view approved public-safe forecast content.
- Q: What source should the portal use for forecast data? → A: The portal reads only the current approved public-safe forecast version published by upstream forecasting and approval workflows; UC-17 does not generate or approve forecasts itself.
- Q: What minimum information may appear in the public response? → A: Only public-safe category-level forecast content may be shown: service category, the forecast demand value or demand-level summary for that category, the covered forecast window label, and the published/last-updated timestamp for the approved public view.
- Q: How should partial category coverage be represented? → A: The portal shows only categories present in the approved public-safe forecast version and must indicate when category coverage is incomplete rather than implying omitted categories have zero demand.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View approved public demand forecasts by category (Priority: P1)

As a public resident, I want to view approved forecasts of 311 demand by service category so that I can understand expected service load before choosing how to access services.

**Why this priority**: This is the core outcome of UC-17. Without a public-facing forecast view by category, the feature does not provide value to residents.

**Independent Test**: Can be fully tested by loading the public forecast portal when approved public-safe forecast data is available and verifying retrieval, preparation, rendering, and successful display logging.

**Acceptance Scenarios**:

1. **Given** a public resident opens the public forecast portal and approved public-safe forecast data is available, **When** the page request is processed, **Then** the system retrieves approved forecast demand data by service category.
2. **Given** approved public-safe forecast data has been retrieved, **When** the system prepares the public response, **Then** it transforms the data into a public visualization format without exposing internal operational details.
3. **Given** public visualization data has been prepared successfully and the visualization module is operating normally, **When** the portal renders the forecast page, **Then** it displays charts or summaries showing expected demand levels by service category in an understandable format.
4. **Given** a public resident views the successfully rendered forecast page, **When** the information is displayed, **Then** the resident can review the category-level demand outlook and interpret expected service load.
5. **Given** a public forecast page renders successfully, **When** operational logs are reviewed, **Then** they show successful forecast retrieval and display outcomes for that portal request or equivalent correlation context where available.

---

### User Story 2 - Show only public-safe forecast information (Priority: P2)

As a public resident, I want the forecast page to show only public-safe information so that I can benefit from the forecast without seeing restricted operational details.

**Why this priority**: Public availability depends on safe disclosure. If filtering is not enforced, the feature creates privacy and operational exposure risk.

**Independent Test**: Can be fully tested by loading the public forecast portal with forecast data that either already satisfies public-release rules or contains details that must be sanitized before display.

**Acceptance Scenarios**:

1. **Given** forecast data is retrieved for public display, **When** the system evaluates it against public-safety filtering rules, **Then** it allows already approved public-safe data to continue to visualization preparation.
2. **Given** retrieved forecast data contains details that do not meet public-release rules, **When** the public-safety filtering step runs, **Then** the system removes the restricted details and prepares a sanitized summary for display.
3. **Given** a sanitized summary is displayed after filtering, **When** a public resident reviews the page, **Then** no restricted details are visible in the UI.

---

### User Story 3 - Handle missing data or rendering failures with a clear public error state (Priority: P3)

As a public resident, I want the portal to fail clearly when forecasts cannot be shown so that I am not misled by missing or broken visualizations.

**Why this priority**: Failure handling protects user trust, but it depends on the main public-display workflow already existing.

**Independent Test**: Can be fully tested by forcing missing forecast data and visualization rendering failures, then verifying that the system logs the failures and shows a clear error state instead of misleading forecast content.

**Acceptance Scenarios**:

1. **Given** a public resident opens the public forecast portal and approved forecast data cannot be retrieved, **When** the request is processed, **Then** the system logs the missing forecast-data condition and displays a clear error message instead of forecast information.
2. **Given** forecast data has been retrieved and prepared for public display, **When** the visualization module fails while rendering charts or summaries, **Then** the system logs the rendering failure and displays an error state instead of the forecast visualization.
3. **Given** a missing-data or rendering-failure path occurs, **When** the resident views the page, **Then** the UI does not show misleading empty, partial, or corrupted forecast visuals.

### Edge Cases

- Public-safe forecast data is available for some service categories but not all, and the system must avoid implying that omitted categories have zero expected demand unless that is the actual forecasted value.
- Retrieved forecast data contains internal metadata or restricted detail fields, and the system must remove them before anything is shown publicly.
- Forecast data retrieval returns no approved public dataset for the requested view, and the system must show a clear error state rather than an empty chart.
- Visualization rendering fails after public-safe data preparation succeeds, and the system must avoid displaying broken or partially rendered charts.
- A public resident refreshes or revisits the page while the underlying forecast version changes, and the system must still display one coherent approved forecast result per response.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a public forecast portal that a public resident can access to view 311 demand forecasts by service category.
- **FR-001a**: The public forecast portal MUST be accessible without user authentication.
- **FR-002**: When the public forecast portal is opened, the system MUST retrieve approved forecast demand data by service category from the current approved public-safe forecast source.
- **FR-002a**: UC-17 MUST read an already approved public-safe forecast version from upstream forecast lineage and MUST NOT generate, re-score, or approve a forecast within the public portal request.
- **FR-003**: The system MUST prepare retrieved forecast data for public visualization in a format that is understandable to a public resident.
- **FR-004**: The system MUST render charts, summaries, indicators, or equivalent public-facing visual elements that show expected demand levels by service category.
- **FR-005**: The public forecast view MUST present category-level demand information without exposing internal operational metadata or restricted details.
- **FR-006**: The system MUST apply public-safety filtering rules to forecast data before rendering it in the public portal.
- **FR-007**: If retrieved forecast data contains restricted details, the system MUST remove those details before display and MUST present a sanitized summary instead of the unsanitized data.
- **FR-007a**: The public visualization payload MUST be limited to public-safe category-level fields: service category, forecast demand value or demand-level summary, covered forecast window label, and published or last-updated timestamp.
- **FR-008**: The system MUST log successful forecast retrieval and successful public display outcomes for each public forecast request.
- **FR-009**: If approved forecast data is unavailable for the public portal request, the system MUST log the missing forecast-data condition and MUST display a clear error message instead of forecast information.
- **FR-010**: If the visualization module fails while rendering the public forecast view, the system MUST log the rendering failure and MUST display an error state instead of charts or summaries.
- **FR-011**: The system MUST NOT display misleading empty, partial, corrupted, or unsanitized forecast visuals in missing-data, filtering, or rendering-failure scenarios.
- **FR-012**: The system MUST ensure that only approved public-safe forecast information is shown through this feature.
- **FR-013**: If the approved public-safe forecast version includes only some service categories, the system MUST show only the included categories and MUST indicate incomplete category coverage rather than treating omitted categories as zero demand.
- **FR-014**: Each portal response MUST render one internally consistent approved public-safe forecast version even if a newer approved version becomes available while the request is in progress.

### Key Entities *(include if feature involves data)*

- **Public Forecast View Request**: One public portal access attempt to load approved 311 demand forecasts by category, along with request timing and correlation context where available.
- **Approved Public Forecast Dataset**: The forecast demand data by service category that has been approved for public release and is eligible for retrieval by the portal.
- **Public Forecast Visualization Payload**: The transformed, public-facing representation of the approved forecast dataset prepared for charts, summaries, or indicators.
- **Public Forecast Sanitization Outcome**: The result of applying public-safety filtering rules to the retrieved forecast data, indicating whether the data passed as-is or required sanitization before display.
- **Public Forecast Display Event**: An operational record of successful retrieval, sanitization, rendering, display, missing-data, or rendering-failure outcomes for a public portal request.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In stakeholder acceptance testing, 100% of public portal requests with approved public-safe forecast data display category-level forecast information in an understandable public format.
- **SC-002**: In stakeholder acceptance testing, 100% of scenarios containing restricted forecast details display only sanitized public-safe output with no restricted information visible in the UI.
- **SC-003**: In stakeholder acceptance testing, 100% of public portal requests where approved forecast data is unavailable show a clear error message and produce a traceable missing-data log entry.
- **SC-004**: In stakeholder acceptance testing, 100% of visualization rendering failures produce a traceable rendering-failure log entry and show an error state instead of broken forecast visuals.
- **SC-005**: In stakeholder acceptance testing, 100% of successful public displays produce a traceable record of retrieval and display outcomes for the same request or equivalent correlation context where available.

## Assumptions & Dependencies

- Forecast generation and approval workflows already exist in earlier use cases and provide the current approved public-safe forecast version that UC-17 reads without redefining how forecasts are produced.
- The public portal is intended for residents and is accessible without sign-in.
- The public-safe output contract for this feature is limited to category-level demand content plus a forecast window label and published or last-updated timestamp.
- Public-safety filtering rules exist or will be defined by the implementation so that restricted details can be removed before display when necessary.
- The portal reflects the latest approved public-safe forecast made available by upstream workflows and does not promise a separate real-time refresh cadence beyond those approvals.
- The exact visual form of the public forecast may vary by implementation, but it must remain understandable to a general public audience.
