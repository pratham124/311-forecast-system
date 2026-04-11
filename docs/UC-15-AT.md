# UC-15 Acceptance Test Suite: Weather-Aware Forecasting and Storm-Mode Alerting

**Use Case**: UC-15 Weather-Aware Forecasting and Storm-Mode Alerting  
**Scope**: Operations Analytics System  
**Goal**: Verify forecast behavior remains weather-aware where supported, verify storm mode is consistently treated as the same surge/anomaly state used in UC-11, verify alert and notification behavior under that shared state, and verify degraded paths remain safe and traceable.

---

## Clarification

For this acceptance suite, **storm mode is equivalent to the confirmed surge/anomaly state from UC-11**.

---

## Assumptions / Test Harness Requirements

- A test environment with controllable components:
  - **Weather Context Provider** (available, unavailable, unusable payloads)
  - **Forecasting Engine** (weather-aware and baseline-compatible behavior)
  - **Surge/Anomaly Confirmation Logic** (active/inactive outcomes)
  - **Alert Evaluation Logic** (storm-mode-aware path and baseline path)
  - **Notification Service** (success and delivery failure with follow-up status)
- Seeded scenarios:
  - baseline scenario (storm mode inactive)
  - storm-mode scenario (surge/anomaly confirmed)
  - degraded weather-context scenario
- Observability:
  - access to operational records sufficient to correlate forecast behavior context, storm-mode state, alert outcome, and notification outcome

---

## AT-01 — Forecast behavior is weather-aware for supported scenarios
**Covers**: UC-15 Main Scenario Step 1

**Preconditions**
- Weather context is available for the scenario.

**Steps**
1. Run a supported forecast scenario with weather context enabled.
2. Review output and operational records.

**Expected Results**
- Forecast behavior is recorded as weather-aware.
- Scenario completes without requiring storm mode.

---

## AT-02 — Storm mode in UC-15 maps to the UC-11 surge/anomaly state
**Covers**: Clarification + Main Scenario Step 2

**Preconditions**
- Surge/anomaly confirmation logic is enabled.

**Steps**
1. Trigger a confirmed surge/anomaly scenario.
2. Review storm-mode state representation for UC-15.

**Expected Results**
- UC-15 storm mode is active when and only when the UC-11-equivalent surge/anomaly state is active.
- No second independent storm-mode state is observed.

---

## AT-03 — Storm-mode-aware alert behavior applies when shared storm mode is active
**Covers**: Main Scenario Step 3

**Preconditions**
- Shared storm mode is active for the evaluated scope.

**Steps**
1. Run alert evaluation for a scope where storm-mode-aware behavior is expected.
2. Compare against baseline alert behavior for the same scope.

**Expected Results**
- Alert evaluation follows storm-mode-aware behavior while shared storm mode is active.
- Behavior differs from baseline where scope rules require a difference.

---

## AT-04 — Demand-risk evaluation and notification follow shared storm-mode context
**Covers**: Main Scenario Steps 4-5

**Preconditions**
- Shared storm mode is active.
- Notification pathway is operational.

**Steps**
1. Execute demand-risk evaluation for an alertable scenario.
2. Observe notification behavior.

**Expected Results**
- Alert outcomes are evaluated under the active storm-mode context.
- Notification is sent when alert conditions are met.

---

## AT-05 — Operational records preserve one coherent trail
**Covers**: Main Scenario Step 6

**Preconditions**
- Execute a full successful scenario.

**Steps**
1. Retrieve operational records for the scenario.
2. Verify correlation across forecast behavior context, storm-mode state, alert evaluation, and notification outcome.

**Expected Results**
- One coherent review trail is available.
- Records are sufficient for operator follow-up.

---

## AT-06 — Weather context unavailable uses baseline-compatible behavior safely
**Covers**: Extension 1a

**Preconditions**
- Weather context provider is unavailable.

**Steps**
1. Run forecasting and alert evaluation workflow.
2. Review outputs and records.

**Expected Results**
- System records weather-context unavailability.
- Forecast behavior remains baseline-compatible.
- Workflow remains operational.

---

## AT-07 — Storm mode inactive keeps alert behavior baseline
**Covers**: Extension 2a

**Preconditions**
- Surge/anomaly confirmation is negative for the scenario.

**Steps**
1. Run alert evaluation.
2. Inspect storm-mode state and alert behavior context.

**Expected Results**
- Storm mode remains inactive.
- Alert behavior remains baseline.

---

## AT-08 — Notification failure preserves follow-up outcome
**Covers**: Extension 5a

**Preconditions**
- Alert condition is met.
- Notification delivery is forced to fail.

**Steps**
1. Trigger alert in active operational context.
2. Inject notification delivery failure.
3. Review follow-up state.

**Expected Results**
- Delivery failure is recorded.
- Notification outcome is marked retry-pending or manual-review-required.
- Failure remains traceable in the same operational review context.

---

## Traceability Matrix

| Acceptance Test | UC-15 Flow Covered |
|---|---|
| AT-01 | Main Scenario (1) |
| AT-02 | Clarification + Main Scenario (2) |
| AT-03 | Main Scenario (3) |
| AT-04 | Main Scenario (4-5) |
| AT-05 | Main Scenario (6) |
| AT-06 | Extension 1a |
| AT-07 | Extension 2a |
| AT-08 | Extension 5a |
