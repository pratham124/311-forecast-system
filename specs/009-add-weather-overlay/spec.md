# Feature Specification: Weather Overlay Explorer

**Feature Branch**: `009-add-weather-overlay`  
**Created**: 2026-03-13  
**Status**: Draft  
**Input**: User description: "docs/UC-09.md and docs/UC-09-AT.md"

## Clarifications

### Session 2026-03-13

- Q: When the weather overlay is enabled, how many weather measures can be shown at once? → A: A single weather measure is shown at a time, selected by the operational manager.
- Q: What should happen when the selected geography cannot be matched under approved weather-alignment rules? → A: The system does not show the overlay unless the selected geography can be matched under approved rules.
- Q: What should happen if the operational manager changes filters while a weather overlay request is still in progress? → A: The system cancels or discards the in-flight request and only shows overlay results for the latest selection.
- Q: What qualifies a forecast-explorer geography and selection as supported for weather overlay? → A: A supported geography is one with an approved direct mapping to the Edmonton-area weather-station selection and approved time-bucket alignment; a supported selection is the latest non-superseded request that uses a supported geography, time range, and weather measure and is eligible to produce a visible overlay.
- Q: How are missing weather data, retrieval failure, and disabled state treated? → A: Missing weather data and provider retrieval failure are separate requirement and status cases, and disabled is both a user-visible off state and a canonical overlay display state.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View weather context with forecasts (Priority: P1)

An operational manager can turn on a weather overlay while reviewing forecast and historical demand so they can see whether weather events align with changes in demand.

**Why this priority**: This is the core user value of the feature. Without the overlay itself, the feature does not help forecast interpretation.

**Independent Test**: Can be fully tested by opening the forecast explorer, enabling the overlay for a supported geography and time range, selecting one supported weather measure, and confirming that the chosen weather information appears alongside forecast and historical demand in a way that supports visual comparison.

**Acceptance Scenarios**:

1. **Given** the forecast explorer is open for a supported geography and time range, **When** the operational manager enables the weather overlay and selects a supported weather measure, **Then** the explorer displays that weather information aligned with the existing demand view.
2. **Given** the weather overlay is displayed, **When** the operational manager reviews the chart, **Then** they can distinguish the weather layer from forecast and historical demand without losing readability of the base view.

---

### User Story 2 - Continue analysis when weather data cannot be shown (Priority: P2)

An operational manager can continue using the forecast explorer even when weather data is unavailable, misaligned, or cannot be rendered, so the base forecast workflow remains dependable.

**Why this priority**: The forecast explorer is already operationally important, so the optional overlay must not block or degrade the primary analysis workflow.

**Independent Test**: Can be fully tested by forcing missing data, alignment failure, and rendering failure conditions and confirming that the base forecast view remains available while the overlay is suppressed and a clear status message is shown.

**Acceptance Scenarios**:

1. **Given** the operational manager enables the overlay and matching weather data is unavailable, **When** the retrieval attempt completes, **Then** the system keeps the forecast explorer visible without the overlay and informs the user that weather data is unavailable.
2. **Given** the operational manager enables the overlay and the weather data cannot be safely aligned or displayed, **When** the failure is detected, **Then** the system does not show the overlay, preserves the base forecast view, and records the failure for operational follow-up.

---

### User Story 3 - Keep overlay synchronized with user selections (Priority: P3)

An operational manager can turn the overlay on or off and change the viewed geography or time range without seeing stale weather data, so the displayed context always matches the current analysis.

**Why this priority**: Correct synchronization prevents misleading interpretation and supports routine exploratory use.

**Independent Test**: Can be fully tested by enabling the overlay, disabling it, re-enabling it, and changing the geography and time range to confirm the weather layer is removed or refreshed to match the current selection.

**Acceptance Scenarios**:

1. **Given** the weather overlay is visible, **When** the operational manager disables it, **Then** the weather layer is removed and the base forecast visualization remains unchanged.
2. **Given** the overlay is enabled, **When** the operational manager changes the geography or time range while a prior overlay request is in progress or after a prior overlay was shown, **Then** the system only displays overlay results for the latest selection and does not retain data from the previous view.

### Edge Cases

- A selected geography or time range has forecast data but no matching weather records.
- A selected geography cannot be matched to weather data under approved alignment rules, so the overlay is suppressed instead of using a fallback geography.
- A weather-provider request fails before weather records can be returned, so the overlay is suppressed and reported as a retrieval failure rather than as missing weather data.
- Weather data exists but uses a different time grain than the demand view and cannot be aligned under established business rules.
- The operational manager changes filters while a prior overlay request is still in progress, and only the newest selection is allowed to produce a visible overlay.
- The operational manager repeatedly toggles the overlay on and off during the same session.
- A previously successful overlay becomes unavailable for a later selection in the same analysis session.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide an explicit control in the forecast explorer that allows an operational manager to enable or disable an optional weather overlay.
- **FR-002**: The system MUST retrieve weather information that matches the geography and time range currently shown in the forecast explorer when the overlay is enabled for a supported selection.
- **FR-003**: The system MUST treat a forecast-explorer geography as supported for weather overlay only when approved alignment rules define a direct mapping from that geography to the approved Edmonton-area weather-station selection and the active demand-view time buckets; if no approved mapping exists, the system MUST suppress the overlay instead of substituting a fallback geography or station.
- **FR-004**: The system MUST display the weather overlay together with forecast and historical demand data in a way that preserves the readability of all visible layers.
- **FR-005**: The system MUST support at least temperature and snowfall as weather measures available for overlay analysis.
- **FR-006**: The system MUST allow the operational manager to choose which single supported weather measure is shown in the overlay for the current view.
- **FR-007**: The system MUST prevent display of weather information when matching weather records are missing for an otherwise supported selection.
- **FR-008**: The system MUST prevent display of weather information when weather-provider retrieval fails, when the data cannot be aligned confidently, or when the overlay cannot be rendered correctly.
- **FR-009**: When the weather overlay cannot be shown, the system MUST keep the base forecast explorer usable and present a clear status message that explains whether the overlay is unavailable because records are missing, provider retrieval failed, geography matching failed, alignment failed, or rendering failed. Geography matching failure and alignment failure are distinct failure reasons even when both produce the non-visible `misaligned` overlay state.
- **FR-010**: The system MUST update or remove the weather overlay whenever the operational manager changes the viewed geography, changes the time range, or disables the overlay.
- **FR-011**: The system MUST avoid showing stale or duplicated weather layers after repeated enable, disable, or filter-change actions within the same session.
- **FR-012**: The system MUST record successful overlay displays and overlay failures with enough context for operational support to determine the selected geography, time range, selected weather measure, and failure category.
- **FR-013**: The system MUST prevent more than one weather measure from being displayed in the overlay at the same time.
- **FR-014**: The system MUST cancel or discard in-progress overlay work for superseded selections and only display overlay results for the operational manager's latest geography, time range, and weather-measure selection.
- **FR-015**: The system MUST treat a supported selection as the latest non-superseded overlay request whose geography, time range, and selected weather measure are all supported under the approved alignment rules and are therefore eligible to produce a visible overlay.

### Key Entities *(include if feature involves data)*

- **Forecast Explorer View**: The active analytical view containing the selected geography, time range, forecast demand, and historical demand that the operational manager is reviewing.
- **Weather Overlay Selection**: The manager's choice to show or hide weather context for the current explorer view, including the single supported weather measure selected for the overlay.
- **Weather Observation Set**: The collection of weather values relevant to the selected geography and time range that can be aligned for comparison against demand patterns using the approved Edmonton-area station mapping and without substituting a fallback geography or station.
- **Overlay Display State**: The canonical state of the overlay workflow for a given view, including `disabled` when the manager has the overlay turned off, `loading` while the latest supported selection is in progress, `visible` when the overlay is shown, `unavailable` when matching weather records are missing, `retrieval-failed` when the weather provider request fails, `misaligned` when approved geography or time-bucket alignment cannot be achieved, `superseded` when a newer selection replaces the request in progress, and `failed-to-render` when visualization fails, together with the associated user-facing status message where applicable.

## Assumptions

- Weather overlay use is optional and does not replace the primary forecast and historical demand views.
- Weather overlay retrieval uses Government of Canada MSC GeoMet as the external weather data source.
- UC-09 reuses the forecast explorer's existing forecast horizon and uncertainty outputs from the prior forecast and visualization features.
- Operational managers already have access to the forecast explorer and are authorized to view the same geography and time range they use today.
- The business has approved geography-alignment rules that determine which forecast-explorer geographies are eligible for weather overlay by mapping each supported geography directly to an approved Edmonton-area weather-station selection and to the demand-view time buckets.
- If the selected geography cannot be matched under those approved rules, the system suppresses the overlay instead of substituting a nearby, broader, or otherwise fallback geography or station.
- Initial rollout focuses on operational analysis rather than exporting or printing weather-enriched views.
- If multiple weather measures are available, the manager selects one measure at a time for display in the overlay.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In at least 95% of supported selections, the weather overlay is shown within 5 seconds after an operational manager enables it. For this measure, a supported selection is the latest non-superseded request that uses a supported geography, supported time range, and supported weather measure and that is eligible to produce a visible overlay; invalid, unavailable, retrieval-failed, misaligned, failed-to-render, and superseded requests are excluded from this timing target.
- **SC-002**: In usability testing, at least 90% of operational managers can correctly identify a weather event aligned with a visible demand change on their first attempt.
- **SC-003**: In 100% of tested missing-data, alignment-failure, and rendering-failure scenarios, the base forecast explorer remains available without a misleading weather layer.
- **SC-004**: In at least 95% of tested filter or toggle changes, the weather overlay reflects the current geography and time range without showing stale data from a prior view.
