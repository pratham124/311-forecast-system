# UC-17 Acceptance Test Suite: View Forecasts as Public Resident

**Use Case**: UC-17 View Public Forecast of 311 Demand by Category  
**Scope**: Public-Facing Forecast Portal  
**Goal**: Verify a Public Resident can view approved, public-safe forecasts of 311 demand by category in an understandable format; the system retrieves and filters data according to public-safety rules; renders clear charts/summaries; and logs outcomes while handling missing data and rendering failures gracefully.

---

## Assumptions / Test Harness Requirements
- A public portal environment (no authentication required unless specified by implementation) that exposes **public-safe** forecast data only. fileciteturn11file0
- A controllable **Data Storage / Retrieval Layer** supporting:
  - successful retrieval of approved public-safe forecast demand by category fileciteturn11file0
  - “forecast data unavailable” (no data) condition fileciteturn11file0
  - injected retrieval failures (timeout / unavailable / 5xx) fileciteturn11file0
- A controllable **Public-Safety Filtering** step supporting:
  - pass (data already public-safe)
  - fail (restricted details present) leading to sanitization/removal fileciteturn11file0
- A controllable **Visualization Module** supporting:
  - successful rendering of charts/summaries for public residents fileciteturn11file0
  - injected visualization rendering failure fileciteturn11file0
- Observability:
  - UI states observable (loaded, error message/state, sanitized summary shown)
  - logs accessible for assertions (successful display, missing data, filtering action, rendering error) fileciteturn11file0

---

## AT-01 — Public forecast portal loads
**Covers**: Main Success Scenario Step 1 fileciteturn11file0  
**Preconditions**
- Public portal is reachable.
- Visualization services are operational. fileciteturn11file0

**Steps**
1. Public Resident navigates to the public forecast portal.

**Expected Results**
- Portal loads successfully.
- The resident can see the forecast content area (charts/summaries region) or a loading state.
- No error state is displayed on initial load.

---

## AT-02 — System retrieves approved forecast demand data by service category
**Covers**: Main Success Scenario Step 2 fileciteturn11file0  
**Preconditions**
- Approved public-safe forecast data exists by service category. fileciteturn11file0

**Steps**
1. Open the public forecast portal.
2. Observe loading state and then results.
3. Inspect logs/captured requests for data retrieval.

**Expected Results**
- System retrieves approved forecast demand data by service category.
- Retrieval succeeds without exposing restricted details.
- Logs indicate retrieval success.

---

## AT-03 — System prepares data for public visualization
**Covers**: Main Success Scenario Step 3 fileciteturn11file0  
**Preconditions**
- Forecast data retrieval succeeds (AT-02).

**Steps**
1. Load the portal with available forecast data.
2. Observe transformation/aggregation behavior (via UI structure and/or logs).

**Expected Results**
- System prepares a public-facing representation (simple, readable aggregation by category).
- Output is suitable for a public audience (no internal operational metadata).
- Logs indicate preparation success (or equivalent stage completion).

---

## AT-04 — Charts/summaries render showing expected demand levels by category
**Covers**: Main Success Scenario Steps 4–5; Success End Condition fileciteturn11file0  
**Preconditions**
- Forecast data exists and visualization module is operational.

**Steps**
1. Load the portal.
2. Inspect the rendered charts/summaries.

**Expected Results**
- The system renders charts/indicators/summaries showing expected demand levels by service category. fileciteturn11file0
- Forecast demand is displayed in an understandable format for a public resident. fileciteturn11file0
- Resident can interpret expected service load and use it to make a decision about reaching services. fileciteturn11file0

---

## AT-05 — Successful public display is logged
**Covers**: Main Success Scenario Step 6 fileciteturn11file0  
**Preconditions**
- A successful render occurred (AT-04).

**Steps**
1. Perform a successful portal view where forecasts are displayed.
2. Retrieve logs/events for the session.

**Expected Results**
- System logs successful data retrieval and display. fileciteturn11file0
- Log entry includes at least timestamp and outcome (and any correlation id if implemented).

---

## AT-06 — Forecast data unavailable: system logs missing data and displays error message
**Covers**: Extension 2a (2a1–2a2); Failed End Condition fileciteturn11file0  
**Preconditions**
- Configure forecast data retrieval to return “missing/unavailable” for public portal.

**Steps**
1. Open the public forecast portal.
2. Observe UI and logs.

**Expected Results**
- System logs missing forecast data. fileciteturn11file0
- UI displays a clear error message instead of forecast information. fileciteturn11file0
- No misleading “empty” charts are shown.

---

## AT-07 — Public-safety filtering fails: system sanitizes data and displays safe summary
**Covers**: Extension 3a (3a1–3a2) fileciteturn11file0  
**Preconditions**
- Forecast data retrieval succeeds but includes restricted details that must not be shown publicly.
- Public-safety filtering rules are enabled. fileciteturn11file0

**Steps**
1. Open the public forecast portal under a scenario where data fails public-safety filtering.
2. Observe displayed content and logs.

**Expected Results**
- System removes restricted/sensitive details. fileciteturn11file0
- System displays a sanitized summary to the resident. fileciteturn11file0
- (If applicable) Logs record that filtering/sanitization occurred.
- No restricted details are visible in the UI.

---

## AT-08 — Visualization rendering error: system logs failure and displays error state
**Covers**: Extension 4a (4a1–4a2); Failed End Condition fileciteturn11file0  
**Preconditions**
- Forecast data retrieval and preparation succeed.
- Force Visualization Module to fail rendering. fileciteturn11file0

**Steps**
1. Open the public forecast portal.
2. Inject rendering failure during chart/summaries rendering.
3. Observe UI and logs.

**Expected Results**
- System logs rendering failure. fileciteturn11file0
- UI displays an error state instead of charts/summaries. fileciteturn11file0
- No corrupted or partial visuals are displayed.

---

## AT-09 — Clarity and public data safety: resident sees valid safe summaries or a clear error (never restricted or misleading content)
**Covers**: Key Behavioral Theme Across All Alternatives fileciteturn11file0  
**Preconditions**
- Test harness supports:
  - forecast missing/unavailable (AT-06)
  - public-safety filtering required (AT-07)
  - visualization rendering failure (AT-08)

**Steps**
1. Execute AT-04 (normal success) and verify understandable public display.
2. Execute AT-06 and verify clear error message.
3. Execute AT-07 and verify sanitized summary with no restricted details.
4. Execute AT-08 and verify clear error state.
5. Review logs for each run.

**Expected Results**
- Only approved and safe information is shown to the public. fileciteturn11file0
- Missing data and rendering issues are logged and communicated clearly. fileciteturn11file0
- The resident either sees valid forecast summaries or a clear error message, with no misleading partials. fileciteturn11file0

---

## Traceability Matrix
| Acceptance Test | UC-17 Flow Covered |
|---|---|
| AT-01 | Main Success Scenario (1) fileciteturn11file0 |
| AT-02 | Main Success Scenario (2) fileciteturn11file0 |
| AT-03 | Main Success Scenario (3) fileciteturn11file0 |
| AT-04 | Main Success Scenario (4–5); Success End Condition fileciteturn11file0 |
| AT-05 | Main Success Scenario (6) fileciteturn11file0 |
| AT-06 | Extension 2a; Failed End Condition fileciteturn11file0 |
| AT-07 | Extension 3a fileciteturn11file0 |
| AT-08 | Extension 4a; Failed End Condition fileciteturn11file0 |
| AT-09 | Key Behavioral Theme Across All Alternatives fileciteturn11file0 |
