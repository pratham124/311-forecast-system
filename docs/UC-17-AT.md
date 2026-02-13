# UC-17 Acceptance Test Suite: View Forecasts as Public Resident

**Use Case**: UC-17 View Public Forecast of 311 Demand by Category  
**Scope**: Public-Facing Forecast Portal  
**Goal**: Verify a Public Resident can view approved, public-safe forecasts of 311 demand by category in an understandable format; the system retrieves and filters data according to public-safety rules; renders clear charts/summaries; and logs outcomes while handling missing data and rendering failures gracefully.

---

## Assumptions / Test Harness Requirements
- A public portal environment (no authentication required unless specified by implementation) that exposes **public-safe** forecast data only. 
- A controllable **Data Storage / Retrieval Layer** supporting:
  - successful retrieval of approved public-safe forecast demand by category 
  - “forecast data unavailable” (no data) condition 
  - injected retrieval failures (timeout / unavailable / 5xx) 
- A controllable **Public-Safety Filtering** step supporting:
  - pass (data already public-safe)
  - fail (restricted details present) leading to sanitization/removal 
- A controllable **Visualization Module** supporting:
  - successful rendering of charts/summaries for public residents 
  - injected visualization rendering failure 
- Observability:
  - UI states observable (loaded, error message/state, sanitized summary shown)
  - logs accessible for assertions (successful display, missing data, filtering action, rendering error) 

---

## AT-01 — Public forecast portal loads
**Covers**: Main Success Scenario Step 1   
**Preconditions**
- Public portal is reachable.
- Visualization services are operational. 

**Steps**
1. Public Resident navigates to the public forecast portal.

**Expected Results**
- Portal loads successfully.
- The resident can see the forecast content area (charts/summaries region) or a loading state.
- No error state is displayed on initial load.

---

## AT-02 — System retrieves approved forecast demand data by service category
**Covers**: Main Success Scenario Step 2   
**Preconditions**
- Approved public-safe forecast data exists by service category. 

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
**Covers**: Main Success Scenario Step 3   
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
**Covers**: Main Success Scenario Steps 4–5; Success End Condition   
**Preconditions**
- Forecast data exists and visualization module is operational.

**Steps**
1. Load the portal.
2. Inspect the rendered charts/summaries.

**Expected Results**
- The system renders charts/indicators/summaries showing expected demand levels by service category. 
- Forecast demand is displayed in an understandable format for a public resident. 
- Resident can interpret expected service load and use it to make a decision about reaching services. 

---

## AT-05 — Successful public display is logged
**Covers**: Main Success Scenario Step 6   
**Preconditions**
- A successful render occurred (AT-04).

**Steps**
1. Perform a successful portal view where forecasts are displayed.
2. Retrieve logs/events for the session.

**Expected Results**
- System logs successful data retrieval and display. 
- Log entry includes at least timestamp and outcome (and any correlation id if implemented).

---

## AT-06 — Forecast data unavailable: system logs missing data and displays error message
**Covers**: Extension 2a (2a1–2a2); Failed End Condition   
**Preconditions**
- Configure forecast data retrieval to return “missing/unavailable” for public portal.

**Steps**
1. Open the public forecast portal.
2. Observe UI and logs.

**Expected Results**
- System logs missing forecast data. 
- UI displays a clear error message instead of forecast information. 
- No misleading “empty” charts are shown.

---

## AT-07 — Public-safety filtering fails: system sanitizes data and displays safe summary
**Covers**: Extension 3a (3a1–3a2)   
**Preconditions**
- Forecast data retrieval succeeds but includes restricted details that must not be shown publicly.
- Public-safety filtering rules are enabled. 

**Steps**
1. Open the public forecast portal under a scenario where data fails public-safety filtering.
2. Observe displayed content and logs.

**Expected Results**
- System removes restricted/sensitive details. 
- System displays a sanitized summary to the resident. 
- (If applicable) Logs record that filtering/sanitization occurred.
- No restricted details are visible in the UI.

---

## AT-08 — Visualization rendering error: system logs failure and displays error state
**Covers**: Extension 4a (4a1–4a2); Failed End Condition   
**Preconditions**
- Forecast data retrieval and preparation succeed.
- Force Visualization Module to fail rendering. 

**Steps**
1. Open the public forecast portal.
2. Inject rendering failure during chart/summaries rendering.
3. Observe UI and logs.

**Expected Results**
- System logs rendering failure. 
- UI displays an error state instead of charts/summaries. 
- No corrupted or partial visuals are displayed.

---

## Traceability Matrix
| Acceptance Test | UC-17 Flow Covered |
|---|---|
| AT-01 | Main Success Scenario (1)  |
| AT-02 | Main Success Scenario (2)  |
| AT-03 | Main Success Scenario (3)  |
| AT-04 | Main Success Scenario (4–5); Success End Condition  |
| AT-05 | Main Success Scenario (6)  |
| AT-06 | Extension 2a; Failed End Condition  |
| AT-07 | Extension 3a  |
| AT-08 | Extension 4a; Failed End Condition  |