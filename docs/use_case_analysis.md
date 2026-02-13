# Use Case Scenario Coverage Review

---

## **UC-01**

- Every narrative is a valid, plausible instantiation of a documented flow and correctly supports the user story’s goal.
- The set of scenarios cover all flows listed in the use case. Below is the mapping from each scenario to the corresponding flow in the use case: 
  - System successfuly initiates data refresh process at scheduled time -> Main happy path
  - Authentication failure -> Extension 2a
  - Data source unavailable -> Extension 4a
  - Data validation failure -> Extension 5a
  - Storage failure -> Extension 6a
- There were no scenarios that represented a flow not documented in the use case.
- The use case and scenarios are missing a plausible outcome: When fetching the latest 311 service request data and the returned data is empty.

### Prompt to Address
> Update UC-01 by adding an Extension for the case where the 311 API returns successfully but there are no new records since the last successful pull. Then write a fully dressed scenario narrative for that new extension, maintaining the Cockburn style and existing end conditions.

### Response

**Extension 4b — Data source returns no new records**

- 4b1: System logs that no new records were available.  
- 4b2: System keeps the current dataset unchanged and marks the run as successful.

#### Alternative Scenario 4b — No New Data Available

Authentication succeeds and the API responds, but indicates there are no new records since the last pull.  

The system logs that no new data was available, keeps the current dataset unchanged, and marks the run as successful.

Satisfies Success End Condition (dataset verified current).

---

## **UC-02**

- Every narrative is a valid, plausible instantiation of a documented flow from the use case and correctly supports the user story’s goal.   
- The set of scenarios cover all flows listed in the use case. Below is the mapping from each scenario to the corresponding flow in the use case:
  - System successfuly ingests new data set and logs completion-> Main happy path
  - Schema validation failure -> Extension 2a
  - Deduplication process failure -> Extension 4a
  - Excessive duplicate rate detected -> Extension 5a
  - Storage failure -> Extension 7a
- There were no scenarios that represented a flow not documented in the use case. 
- The use case and scenarios are complete and there are no needed additions to be made.

---

## **UC-03**

- Every narrative is a valid, plausible instantiation of a documented flow from the use case and correctly supports the user story’s goal. 
- The set of scenarios cover all flows listed in the use case. Below is the mapping from each scenario to the corresponding flow in the use case:
  - System successfuly provides a next 24-hour demand forecast per service category (and geography when available) -> Main happy path
  - Required data unavailable -> Extension 2a
  - Forecasting engine error -> Extension 4a
  - Geographic data incomplete -> Extension 6a
  - Storage failure -> Extension 7a
- There were no scenarios that represented a flow not documented in the use case.
- The use case and scenarios are missing a plausible outcome: A forecast is already current for the same 24-hour window and the manager requests again.

### Prompt to Address
> Update UC-03 by adding an extension for the case where a request is made but a current forecast for the next 24 hours already exists.

### Response

**Extension 1a — Current 24-hour forecast already exists**

- 1a1: System retrieves the existing forecast without rerunning the model.  
- 1a2: System logs that a current forecast was served.

#### Alternative Scenario 1a — Forecast Already Current

An operational manager requests a 1-day forecast. The system finds a forecast already marked as current for the upcoming 24-hour window.

The system retrieves the existing forecast and presents it for planning.  
The system logs that an existing current forecast was served.

Satisfies Success End Condition.

---

## **UC-04**

- Every narrative is a valid, plausible instantiation of a documented flow from the use case and correctly supports the user story’s goal.   
- The set of scenarios cover all flows listed in the use case. Below is the mapping from each scenario to the corresponding flow in the use case:
  - System successfuly provides a next 7-day demand forecast per service category (and geography when available) -> Main happy path
  - Required data unavailable -> Extension 2a
  - Forecasting engine error -> Extension 4a
  - Geographic data incomplete -> Extension 6a
  - Storage failure -> Extension 7a
- There were no scenarios that represented a flow not documented in the use case.
- The use case and scenarios are missing a plausible outcome: A forecast is already current for the same 7-day window and the manager requests again.

### Prompt to Address
> Update UC-04 by adding an extension for the case where a request is made but a current forecast for the next 7 days already exists.

### Response

**Extension 1a — Current 7-day forecast already exists**

- 1a1: System retrieves the existing forecast without rerunning the model.  
- 1a2: System logs that a current weekly forecast was served.

#### Alternative Scenario 1a — Weekly Forecast Already Current

An operational manager requests a weekly forecast. The system finds a forecast already marked as current for the next seven-day horizon.

The system retrieves the existing forecast and presents it for planning.  
The system logs that an existing current weekly forecast was served.

Satisfies Success End Condition.

---

## **UC-05**

- Every narrative is a valid, plausible instantiation of a documented flow from the use case and correctly supports the user story’s goal.  
- The set of scenarios cover all flows listed in the use case. Below is the mapping from each scenario to the corresponding flow in the use case:
  - Successfully provides forecast curves with uncertainty bands overlaid on historical data -> Main happy path
  - Forecase data unavailable -> Extension 2a
  - Historical data unavailable -> Extension 3a
  - Visualization rendering error -> Extension 5a
  - Uncertainty metrics missing -> Extension 6a
- There were no scenarios that represented a flow not documented in the use case.
- The use case and scenarios are complete and there are no needed additions to be made.

---

## **UC-06**

- Every narrative is a valid, plausible instantiation of a documented flow from the use case and correctly supports the user story’s goal. 
- The set of scenarios cover all flows listed in the use case. Below is the mapping from each scenario to the corresponding flow in the use case:
  - Successfuly evaluates the forecasting engine against baseline methods to determine whether the system provides improved predictive performance -> Main happy path
  - Required data unavailable -> Extension 2a
  - Baseline model failure -> Extension 3a
  - Forecast output missing -> Extension 4a
  - Storage failure -> Extension 7a
- There were no scenarios that represented a flow not documented in the use case.
- The use case and scenarios are missing a plausible outcome: Evaluation metric computation fails or produces invalid values.

### Prompt to Address
> Update UC-06 by adding an extension for when evaluation metric computation fails or produces invalid values.

### Response

**Extension 5a — Evaluation metric computation failure**

- 5a1: System logs metric calculation issues.  
- 5a2: System excludes affected metrics or categories.  
- 5a3: System continues evaluation for remaining valid metrics.

#### Alternative Scenario 5a — Metric Computation Failure

Data and model outputs are retrieved successfully, but one or more evaluation metrics cannot be computed.

The system logs the issue, excludes affected metrics, and computes remaining valid metrics.  
Results are stored with notes about excluded metrics.

Satisfies Success End Condition (partial evaluation with documented limitations).

---

## **UC-07**

- Every narrative is a valid, plausible instantiation of a documented flow from the use case and correctly supports the user story’s goal. 
- The set of scenarios cover all flows listed in the use case. Below is the mapping from each scenario to the corresponding flow in the use case:
  - City planner views historical data -> Main happy path
  - No data matches selected filters -> Extension 4a
  - Data retrieval failure -> Extension 4b
  - Visualization rendering error -> Extension 6a
- There were no scenarios that represented a flow not documented in the use case.
- The use case and scenarios are missing a plausible outcome: the city planner requests too much data, causing the request to take a long time to load. Below is the prompt used to address this:

### Prompt to Address
> Update UC-07 by including an extension to warn the user when too much data is requested which could cause the page to crash. 

### Response
**Extension 3a: High Data Volume Warning**
- 3a1: System detects that the selected filters will result in an exceptionally large dataset (e.g., city-wide data for a multi-year period).
- 3a2: System displays a warning message alerting the City Planner that the request may take a significant amount of time to load or impact browser performance.
- 3a3: City Planner acknowledges the warning and chooses to proceed.
- 3a4: System proceeds to Step 4.

#### Alternative Scenario 3a — High Data Volume Warning
After the City Planner selects a multi-year time range covering the entire city, the system identifies that the resulting data volume exceeds the standard performance threshold.

Instead of immediately running the query, the system displays a warning notification. This message informs the planner that retrieving and rendering such a large volume of historical 311 records may result in a long wait time or cause the interface to become temporarily unresponsive.

The City Planner, requiring the full dataset for a comprehensive year-over-year capacity study, clicks "Proceed." The system then initiates the data retrieval process, showing a "loading" state to indicate that the request is being processed despite the size.

--- 

## **UC-08**

- Every narrative is a valid, plausible instantiation of a documented flow from the use case and correctly supports the user story’s goal. 
- The set of scenarios cover all flows listed in the use case. Below is the mapping from each scenario to the corresponding flow in the use case:
  - City planner compares demand/forecast across categories -> Main happy path
  - No historical data available -> Extension 4a
  - Forecast data unavailable -> Extension 5a
  - Data alignment issue -> Extension 6a
  - Visualization rendering error -> Extension 8a
- There were no scenarios that represented a flow not documented in the use case.
- The use case and scenarios are missing a plausible outcome: the city planner requests too much data when comparing historical demand and forecasts, causing the request to take a long time to load. Below is the prompt used to address this:

### Prompt to Address
> Update UC-08 by including an extension to warn the user when too much data is requested which could cause the page to crash. 

### Response
**Extension 3a: High-Volume Comparative Request Warning** 
- 3a1: System detects that the combination of multiple categories, geographies, and the requested time range will result in an exceptionally large comparative dataset.
- 3a2: System displays a warning message stating that aligning large volumes of historical and forecast data may lead to significant loading times.
- 3a3: City Planner acknowledges the warning and chooses to proceed.
- 3a4: System proceeds to Step 4 and 5.

#### Alternative Scenario 3a — High-Volume Comparative Request Warning
The City Planner selects five different service categories (e.g., Sanitation, Road Maintenance, Forestry, etc.) across all city districts for a comparison spanning the next three years.

Because the system must not only pull millions of historical records but also trigger complex calculations from the Forecasting Engine for each category across every district, it identifies a high-load situation. The system then displays a warning notification that informs the planner that retrieving and rendering such a large volume of data may result in a long wait time or cause the interface to become temporarily unresponsive.

The City Planner, needing the full city-wide forecast for the upcoming budget cycle, clicks the "Proceed anyway" button. The system initiates the dual-retrieval process. To keep the user informed, the system displays a persistent loading indicator that tracks the progress of both the historical data pull and the forecast generation until the comparative charts finally render.

---

## **UC-09**

- Every narrative is a valid, plausible instantiation of a documented flow from the use case and correctly supports the user story’s goal. 
- The set of scenarios cover all flows listed in the use case. Below is the mapping from each scenario to the corresponding flow in the use case:
  - Weather data overlayed on forecast -> Main happy path
  - Weather data unavailable -> Extension 3a
  - Alignment issue between weather data and forecast -> Extension 4a
  - Visualization rendering error -> Extension 6a
- There were no scenarios that represented a flow not documented in the use case.
- The use case and scenarios are complete and there are no needed additions to be made.

---

## **UC-10**

- Every narrative is a valid, plausible instantiation of a documented flow from the use case and correctly supports the user story’s goal. 
- The set of scenarios cover all flows listed in the use case. Below is the mapping from each scenario to the corresponding flow in the use case:
  - Weather data overlayed on forecast -> Main happy path
  - Weather data unavailable -> Extension 3a
  - Alignment issue between weather data and forecast -> Extension 4a
  - Visualization rendering error -> Extension 6a
- There were no scenarios that represented a flow not documented in the use case.
- The use case and scenarios are complete and there are no needed additions to be made.

---

## **UC-11**

- Every narrative is a valid, plausible instantiation of a documented flow from the use case and correctly supports the user story’s goal. 
- The set of scenarios cover all flows listed in the use case. Below is the mapping from each scenario to the corresponding flow in the use case:
  - Notify on abnormal demand -> Main happy path
  - Surge detection error -> Extension 2a
  - False positive filtered -> Extension 4a
  - Notification delivery failure -> Extension 5a
- There were no scenarios that represented a flow not documented in the use case.
- The use case and scenarios are complete and there are no needed additions to be made.

---

## **UC-12**

- Every narrative is a valid, plausible instantiation of a documented flow from the use case and correctly supports the user story’s goal. 
- The set of scenarios cover all flows listed in the use case. Below is the mapping from each scenario to the corresponding flow in the use case:
  - Drill into alert details -> Main happy path
  - Forecast distribution data unavailable -> Extension 3a
  - Driver attribution data unavailable -> Extension 4a
  - Anomaly context unavailable -> Extension 5a
  - Visualization rendering error -> Extension 7a
- There were no scenarios that represented a flow not documented in the use case.
- The use case and scenarios are complete and there are no needed additions to be made.

---

## **UC-16**

- Every narrative is a valid, plausible instantiation of a documented flow from the use case and correctly supports the user story’s goal. 
- The set of scenarios cover all flows listed in the use case. Below is the mapping from each scenario to the corresponding flow in the use case:
  - Indicate degraded confidence on UI -> Main happy path
  - Confidence signals unavailable -> Extension 2a
  - False degradation signal -> Extension 3a
  - Visualization rendering error -> Extension 4a
- There were no scenarios that represented a flow not documented in the use case.
- The use case and scenarios are complete and there are no needed additions to be made.

---

## **UC-17**

- Every narrative is a valid, plausible instantiation of a documented flow from the use case and correctly supports the user story’s goal. 
- The set of scenarios cover all flows listed in the use case. Below is the mapping from each scenario to the corresponding flow in the use case:
  - Public users can see forecasts by category -> Main happy path
  - Forecast data unavailable -> Extension 2a
  - Data not approved for public use -> Extension 3a
  - Visualization rendering error -> Extension 4a
- There were no scenarios that represented a flow not documented in the use case.
- The use case and scenarios are complete and there are no needed additions to be made.

---

## **UC-18**

- Every narrative is a valid, plausible instantiation of a documented flow from the use case and correctly supports the user story’s goal. 
- The set of scenarios cover all flows listed in the use case. Below is the mapping from each scenario to the corresponding flow in the use case:
  - User acceses user guide -> Main happy path
  - Documentation unavailable -> Extension 2a
  - Display rendering error -> Extension 3a
- There were no scenarios that represented a flow not documented in the use case.
- The use case and scenarios are complete and there are no needed additions to be made.

---

## **UC-19**

- Every narrative is a valid, plausible instantiation of a documented flow from the use case and correctly supports the user story’s goal. 
- The set of scenarios cover all flows listed in the use case. Below is the mapping from each scenario to the corresponding flow in the use case:
  - User submits feedback/bug report -> Main happy path
  - Invalid or incomplete input in form -> Extension 5a
  - Issue tracking service unavailable -> Extension 6a
  - Storage failure -> Extension 7a
- There were no scenarios that represented a flow not documented in the use case.
- The use case and scenarios are complete and there are no needed additions to be made.
