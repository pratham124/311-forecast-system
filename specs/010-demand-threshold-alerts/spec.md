# Feature Specification: Demand Threshold Alerts

**Feature Branch**: `010-demand-threshold-alerts`  
**Created**: 2026-03-13  
**Status**: Draft  
**Input**: User description: "docs/UC-10.md and docs/UC-10-AT.md"

## Clarifications

### Session 2026-03-13

- Q: When repeated forecast updates stay above the same threshold for the same category, region, and forecast window, what alert behavior should apply? → A: Send one notification on threshold crossing, then send another only after the forecast returns to or below threshold and later exceeds again.
- Q: If an operational manager has multiple configured notification channels for the same alert, what delivery rule should apply? → A: Attempt all configured channels, classify the alert as delivered only when all configured channels succeed, classify it as a partial delivery when at least one succeeds and at least one fails, and record any failed channels for follow-up.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Receive actionable spike alerts (Priority: P1)

As an operational manager, I want to be notified when a forecast bucket for a service category exceeds its configured threshold so that I can prepare staffing and dispatch changes before service demand spikes.

**Why this priority**: This is the primary business outcome of the feature and delivers direct operational value as soon as a single threshold-based alert can be generated and sent.

**Independent Test**: Can be fully tested by configuring a threshold for a category, triggering a forecast update with a forecast bucket above that threshold for one forecast window type and window identifier, and confirming that an alert with the expected context is delivered.

**Acceptance Scenarios**:

1. **Given** a threshold is configured for a service category and a new forecast bucket exceeds it for a specific forecast window type and forecast window, **When** the forecast is evaluated, **Then** the system creates and sends a notification to the operational manager with the category, forecast bucket value, threshold value, forecast window type, and affected forecast window.
2. **Given** a threshold is configured only at the category level, **When** an alert is created, **Then** the notification identifies the category and does not require a geographic region to be present.
3. **Given** an alert has already been sent for a category, optional geographic region, forecast window type, and forecast window that remains above the threshold, **When** later forecast updates stay above that threshold without first returning to or below it, **Then** the system does not send another alert for that same scope.

---

### User Story 2 - Use geography-specific thresholds (Priority: P2)

As an operational manager, I want threshold alerts to optionally apply to a specific geographic region so that I only receive alerts for the locations that need local operational response.

**Why this priority**: Geographic scoping improves alert relevance and prevents false positives, but the feature still provides value without it.

**Independent Test**: Can be fully tested by configuring a threshold for a category and region, triggering forecast updates for multiple regions, and verifying that only the exceeding scoped region and forecast window produces an alert.

**Acceptance Scenarios**:

1. **Given** a threshold is configured for a service category within a specific geographic region, **When** that region exceeds the threshold and another region does not, **Then** the system sends an alert only for the exceeding region.
2. **Given** both a category-only threshold and a category-plus-geography threshold could match the same regional forecast bucket, **When** the forecast is evaluated, **Then** the system applies only the category-plus-geography threshold to that regional scope.
3. **Given** an alert is triggered for a geographic threshold, **When** the notification is delivered, **Then** it includes the affected geographic region, forecast window type, and forecast window that exceeded the threshold.

---

### User Story 3 - Preserve traceability when alerts cannot be sent (Priority: P3)

As an operational manager, I want failed or skipped notifications to be visible through system records so that missed alerts can be investigated and corrected.

**Why this priority**: Reliable traceability reduces operational risk when alert delivery or configuration is incomplete, but it depends on the core alert flow already existing.

**Independent Test**: Can be fully tested by triggering a forecast update under missing-threshold and failed-delivery conditions and verifying the resulting records and follow-up status.

**Acceptance Scenarios**:

1. **Given** no threshold is configured for the relevant forecast scope, **When** a forecast update is evaluated, **Then** the system records the configuration issue and does not send an alert.
2. **Given** a threshold exceedance is detected but notification delivery fails, **When** the alert attempt completes, **Then** the system records the failure and marks the alert for retry or manual review.
3. **Given** an operational manager has multiple configured alert channels, **When** at least one channel succeeds and another fails, **Then** the system records the alert as a partial delivery while preserving the failed channel outcome for follow-up.

---

### User Story 4 - Review alert outcomes and channel failures (Priority: P3)

As an operational manager, I want to review alert history and delivery outcomes so that I can confirm which demand spikes were delivered successfully and which require follow-up.

**Why this priority**: Alert review is necessary to act on partial and failed delivery outcomes, but it depends on the core alert-generation flow already existing.

**Independent Test**: Can be fully tested by creating successful, partial-delivery, and failed alert outcomes and confirming that the resulting records expose the operational details needed for follow-up.

**Acceptance Scenarios**:

1. **Given** alert events have been recorded, **When** an operational manager reviews alert history, **Then** each alert outcome shows the service category, optional geographic region, forecast window type, forecast window, forecast bucket value, threshold value, and overall delivery outcome.
2. **Given** an alert was delivered through every configured channel, **When** the operational manager reviews that alert, **Then** the alert history shows the alert as delivered.
3. **Given** an alert was delivered through at least one channel while another channel failed, **When** the operational manager reviews that alert, **Then** the alert history shows the alert as a partial delivery and identifies the failed channel outcome for follow-up.
4. **Given** an alert was not delivered through any configured channel, **When** the operational manager reviews that alert, **Then** the alert history shows whether retry is pending or manual review is required and preserves the failed delivery details.

### Edge Cases

- A forecast value exactly equal to a configured threshold should not be treated as an exceedance.
- A forecast update that contains multiple exceedances across categories or regions should produce a distinct alert outcome for each exceeded scope.
- When both a category-only threshold and a category-plus-geography threshold could match the same regional forecast bucket, the geography-specific threshold applies to that regional scope and the category-only threshold does not create a second alert for the same bucket.
- A forecast update for a category or region without an applicable threshold should be logged as a configuration gap without blocking evaluation of other configured scopes.
- If notification delivery fails after an exceedance is detected, the failure record should preserve the alert details needed for retry or manual follow-up.
- If the forecast update is repeated with unchanged or still-exceeding values, the system should suppress duplicate alerts until the forecast bucket for that same scope returns to or below the threshold and later exceeds it again.
- If multiple notification channels are configured, a failure in one channel should not cause the entire alert to be treated as undelivered when another configured channel succeeds.
- If threshold settings change between consecutive evaluations of the same category, optional geographic region, forecast window type, and forecast window, the next evaluation should use the newly configured threshold and determine alert eligibility from that new threshold value.
- If all configured notification channels succeed for the same alert, the overall delivery outcome should be recorded as delivered rather than partial delivery.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST evaluate updated forecast results against configured demand thresholds whenever a forecast is generated or refreshed.
- **FR-002**: The system MUST support threshold definitions by service category and by service category plus geographic region.
- **FR-003**: The system MUST compare the forecast bucket value for each evaluated service category, optional geographic region, forecast window type, and forecast window against the applicable threshold for that same scope.
- **FR-003a**: Daily forecast products MUST be evaluated using the forecast bucket and forecast window type provided by the published daily forecast, and weekly forecast products MUST be evaluated using the forecast bucket and forecast window type provided by the published weekly forecast.
- **FR-003b**: For each evaluated scope, the forecast window type and forecast window MUST be recorded and used consistently for threshold comparison, duplicate suppression, alert creation, and operational review.
- **FR-004**: The system MUST create a notification event when a forecast bucket value is greater than its applicable threshold.
- **FR-005**: Each notification event MUST include, at minimum, the service category, optional geographic region, forecast bucket value, threshold value, forecast window type, and affected forecast window.
- **FR-006**: The system MUST send threshold-exceedance notifications to the operational manager through the configured alert channel or channels.
- **FR-007**: The system MUST record successful notification delivery outcomes for monitoring and audit purposes.
- **FR-007a**: When multiple alert channels are configured for the same operational manager, the system MUST attempt delivery through all configured channels for the alert.
- **FR-007b**: The system MUST use the following overall delivery outcomes consistently in alert records and alert review: `delivered` when every configured channel succeeds, `partial delivery` when at least one configured channel succeeds and at least one configured channel fails, `retry pending` when no configured channel succeeds and the alert remains queued for retry, and `manual review required` when no configured channel succeeds and operator follow-up is required.
- **FR-007c**: When one or more configured channels fail but at least one succeeds, the system MUST record each channel-specific failure and classify the overall alert outcome as partial delivery.
- **FR-008**: If no applicable threshold is configured for a forecast scope being evaluated, the system MUST record the configuration issue and MUST NOT send a notification for that unconfigured scope.
- **FR-009**: If forecast values remain below or equal to the applicable threshold, the system MUST complete evaluation without creating a notification event for that scope.
- **FR-010**: If notification delivery fails for every configured channel, the system MUST record the failure outcome and preserve the notification event in a status of retry pending or manual review required.
- **FR-011**: Updated threshold settings MUST be applied to subsequent forecast evaluations without requiring prior alerts to be resent.
- **FR-011a**: If both a category-only threshold and a category-plus-geography threshold could match the same regional forecast bucket, the system MUST apply only the category-plus-geography threshold to that regional scope.
- **FR-011b**: If threshold settings change between consecutive evaluations of the same service category, optional geographic region, forecast window type, and forecast window, the next evaluation MUST use the updated threshold settings when determining whether to create, suppress, or re-arm alerts.
- **FR-012**: The system MUST maintain traceable records linking each forecast evaluation, notification attempt, and final outcome.
- **FR-012a**: Traceable alert review records MUST expose, at minimum, the service category, optional geographic region, forecast window type, forecast window, forecast bucket value, threshold value, overall delivery outcome, and any failed channel outcomes associated with the alert.
- **FR-013**: After sending a threshold-exceedance notification for a category, optional geographic region, forecast window type, and forecast window, the system MUST suppress additional notifications for that same scope until the forecast bucket value returns to or below the threshold and a later forecast bucket for that same scope exceeds it again.

### Key Entities *(include if feature involves data)*

- **Threshold Configuration**: A business rule that defines the maximum forecasted demand allowed for a service category, optionally narrowed to a geographic region and forecast window type.
- **Forecast Evaluation**: A record of a forecast update being checked against one or more threshold configurations, including the evaluated service category, optional geographic region, forecast window type, forecast window, forecast bucket value, and outcome.
- **Notification Event**: An alert record created when a threshold exceedance is detected, including the alert details, overall delivery outcome (`delivered`, `partial delivery`, `retry pending`, or `manual review required`), channel delivery attempts, and reviewable follow-up status.
- **Operational Manager**: The business recipient responsible for receiving and acting on demand-threshold alerts.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In stakeholder acceptance testing, 100% of configured threshold exceedances that newly cross above threshold for a given service category, optional geographic region, forecast window type, and forecast window generate one alert record for that exceeded scope.
- **SC-002**: In stakeholder acceptance testing, 100% of successful alert records reach the intended operational manager within 5 minutes of the forecast update being available for evaluation.
- **SC-003**: In stakeholder acceptance testing, 100% of forecast updates with values below or equal to configured thresholds produce no alert notifications.
- **SC-004**: In stakeholder acceptance testing, 100% of missing-threshold and failed-delivery cases create traceable records that allow staff to identify the affected category, optional region, forecast window, and follow-up status.

## Assumptions

- Thresholds are maintained before forecast updates are evaluated and are available to the feature at evaluation time.
- The operational manager already has at least one configured notification destination managed elsewhere in the product.
- Forecast updates provide enough information to determine the service category, optional geographic region, forecast window type, forecast window, and forecast bucket value being evaluated.
- Retry execution and manual review workflows may already exist elsewhere; this feature only needs to place failed notifications into a trackable follow-up state.
