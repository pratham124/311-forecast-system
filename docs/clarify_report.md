# Clarification Report

Below is a report of the clarifications that Codex requested after running the /speckit.clarify command for each use case. We've included the options we chose and a short justification for it as well. These clarifications were used to help validate our specifications generated via /speckit.specify.

## Use Case 1

After running /speckit.clarify for UC-01, Codex output that there were no ambiguities needed clarifying: "No critical ambiguities detected worth formal clarification."

## Use Case 2

### Question 1
Question 1: Review Handling Scope
What does "flagged for review" actually mean in scope?

|--------|-------------|
| A | Manual review only blocks the dataset; approval or reprocessing happens outside this feature. |
| B | Manual reviewers can approve a flagged dataset directly within this feature. |
| C | Manual reviewers can trigger dataset reprocessing within this feature, but not approve directly. |
| D | Manual reviewers can both approve and reprocess within this feature. |
| Short | Provide a different short answer (<=5 words). |

Response: Choose option A as it keeps this feature bounded around automated validation and safe blocking behavior, which matches the current spec and reduces downstream implementation and test ambiguity.

### Question 2
Question 2: Duplicate Threshold Basis
How should the system decide that the duplicate rate is excessive?

|--------|-------------|
| A | Use a fixed duplicate count. |
| B | Use a percentage of total records. |
| C | Use both count and percentage. |
| Short | Your own answer in <=5 words. |

Response: Choose Option B as a percentage-based threshold scales with dataset size and makes acceptance behavior consistent across small and large ingests.

### Question 3
Question 3: Duplicate Resolution Output
What should the clean dataset contain when duplicates are found?

|--------|-------------|
| A | Keep one existing record from each duplicate group. |
| B | Create one cleaned record per duplicate group, allowing non-conflicting field consolidation. |
| C | Remove the whole duplicate group and require review. |
| Short | Your own answer in <=5 words. |

Response: Choose Option B since using a single cleaned record per duplicate group keeps downstream datasets predictable and aligns with the current approval model of one clean dataset version.

## Use Case 3

### Question 1
Question 1: Time Granularity
What time granularity should the 1-day forecast use?

|--------|-------------|
| A | Forecast demand in hourly buckets for the next 24 hours |
| B | Forecast one total demand value for the full next 24-hour window |
| C | Forecast in larger fixed buckets such as 4-hour or shift-level periods |
| Short | Provide a different short answer (<=5 words) |

Response: Chose Option A as hourly buckets across the next 24 hours are the strongest default for staffing and dispatch planning because they preserve within-day demand patterns without expanding scope beyond the stated 1-day forecast.

## Use Case 4
### Question 1
Question 1: "Current" forecast meaning.
What does "current" forecast mean in the context of FR-008?


| Option | Description |
|--------|-------------|
| A | Rolling horizon: “current” means any forecast covering the next 7 days from request time. |
| B | Calendar week: “current” means one forecast per operational week (e.g., Monday-Sunday). |
| C | Daily anchor: “current” means one forecast per day, each covering the next 7 days. |
| Short | Provide a different short answer (<=5 words). |

Response: Chose Option B as anchoring on the calendar week makes it more deterministic to determine the current weekly forecast, and it will help simplify acceptance tests later on.

### Question 2
Question 2: Weekly Forecast Boundary
Which week boundary should define the operational calendar week for the “current forecast” rule?

| Option | Description |
|--------|-------------|
| A | Week starts Monday 00:00 in local operational timezone. |
| B | Week starts Sunday 00:00 in local operational timezone. |
| C | Week starts at scheduled run timestamp each week. |
| Short | Provide a different short answer (<=5 words). |

## Use Case 5

### Question 1
Question 1: Standard Uncertainty Bands
Which uncertainty bands should UC-05 standardize on for the dashboard view?

| Option | Description |
|--------|-------------|
| A | Display P10, P50, and P90 as the standard uncertainty range set |
| B | Display only P50 and P90 |
| C | Allow the dashboard to choose any available quantiles without a fixed standard |
| Short | Provide a different short answer (<=5 words) |

Response: Chose Option A since P10, P50, and P90 are already the standard quantiles used in UC-03 and UC-04, so standardizing on them here keeps the visualization consistent with the rest of the forecasting pipeline.

### Question 2
Question 2: Historical Context Window
How much historical demand should the dashboard show alongside the forecast?

| Option | Description |
|--------|-------------|
| A | Show only the immediately preceding period matching the forecast horizon |
| B | Show the previous 7 days of historical demand |
| C | Show the previous 30 days of historical demand |
| Short | Provide a different short answer (<=5 words) |

Response: Chose Option B as 7 days of historical context provides enough trend visibility for operational planning without overcrowding the chart, and it aligns naturally with the weekly forecast horizon from UC-04.

### Question 3
Question 3: Fallback Staleness Limit
How old can a fallback visualization be before it should no longer be shown?

| Option | Description |
|--------|-------------|
| A | Show a fallback visualization only if it is from the same forecast cycle |
| B | Show a fallback visualization if it is no more than 24 hours old |
| C | Show the most recent fallback visualization regardless of age, as long as it is labeled |
| Short | Provide a different short answer (<=5 words) |

Response: Chose Option B as a 24-hour staleness limit keeps fallback visualizations useful during short outages while preventing stale or misleading forecasts from being shown as if they were current.

## Use Case 6
### Question 1
Question 1: How should UC-06 define the evaluation scope across forecast products?

| Option | Description |
|--------|-------------|
| A | Evaluate only the daily forecast product |
| B | Evaluate only the weekly forecast product |
| C | Evaluate daily and weekly forecast products separately |
| D | Combine daily and weekly products into one shared evaluation |
| Short | Provide a different short answer (<=5 words) |

Response: Chose Option C since daily and weekly forecasts represent different horizons, so they should be evaluated separately.

## Use Case 7
### Question 1
Question 1: How should UC-07 define the geographic filtering scope for historical demand exploration?

| Option | Description |
|--------|-------------|
| A | Citywide only |
| B | Only stored reliable geography levels |
| C | Require neighbourhood-level geography |
| D | Require ward-level geography |
| Short | Provide a different short answer (<=5 words) |

Response: Chose Option B as we should support the geography levels that are available and consistent in our data source.

## Use Case 8
### Question 1
Question 1: When the planner selects multiple categories or geographies, and forecast data exists for only some of them, what should the system do?

|--------|-------------|
  | A | Fail the entire request if any selected category or geography is missing data. |
  | B | Show partial comparison results for available combinations and explicitly identify the missing combinations. |
  | C | Automatically drop missing combinations without calling them out to the planner. |
  | Short | Provide a different short answer (<=5 words). |

Response: Choose Option B as we should show partial comparison results for available combinations and explicitly identify the missing combinations.

### Question 2
Question 2: If some of the selected historical and forecast data cannot be aligned to the same category or geographic definitions, should the system still show a partial comparison or block the comparison entirely?

|--------|-------------|
  | A | Show an error state and do not display the comparison if any selected historical and forecast data cannot be aligned to common definitions. |
  | B | Show only the combinations that can be aligned and silently omit the rest. |
  | C | Show only the combinations that can be aligned and explicitly identify the excluded combinations. |
  | Short | Provide a different short answer (<=5 words). |

Response: Choose Option A as we should fail the comparison when selected data cannot be aligned to the same category or geographic definitions. That avoids presenting partial matches that could look valid but distort planning decisions.

## Use Case 9
### Question 1
Question 1: Should we limit number of weather measure?

|--------|-------------|
| A | Show all supported weather measures together whenever the overlay is enabled |
| B | Let the manager choose a single weather measure to display at a time |
| C | Show a fixed default measure only, with no user choice |
| Short | Provide a different short answer (<=5 words) |

Response: Choose Option B as we should let managers choose one weather measure at a time keeps the overlay readable and reduces ambiguity in the interaction model, acceptance tests, and data presentation.

### Question 2
Question 2: What should the system do when the manager’s selected geography does not have a valid weather-data match under the alignment rules?

|--------|-------------|
| A | Use the nearest available weather geography automatically when an exact match is unavailable |
| B | Aggregate or broaden to a larger covering geography automatically |
| C | Do not show the overlay unless the selected geography can be matched under approved rules |
| Short | Provide a different short answer (<=5 words) |

Response: Choose Option C as we should only show the overlay when the selected geography can be matched under approved alignment rules is the safest choice because it avoids misleading correlations and keeps acceptance tests unambiguous.

## Use Case 10
### Question 1
Question 1: When repeated forecast updates stay above the same threshold for the same category/region/window, what alert behavior should the feature require?

|--------|-------------|
| A | Send a notification on every forecast update that remains above the threshold. |
| B | Send a notification only on threshold crossing, then send another only after the forecast returns to or below threshold and later exceeds again. |
| C | Send one notification per forecast window per day, even if repeated updates stay above threshold. |
| Short | Provide a different short answer (<=5 words). |

Response: Choose Option B as we should send one alert when a scope first crosses the threshold, then suppress repeats until the forecast falls back to or below the threshold and exceeds again. This avoids alert fatigue and gives a clear reset rule for testing and operations.

### Question 2
Question 2: If an operational manager has multiple configured notification channels for the same alert, what delivery rule should apply?

 |--------|-------------|
| A | Attempt all configured channels; overall delivery succeeds if at least one channel succeeds. |
| B | Attempt channels in priority order and stop after the first successful delivery. |
| C | Require every configured channel to succeed for the alert to count as delivered. |
| Short | Provide a different short answer (<=5 words). |

Response: Choose Option A as we should evaluate all configured channels for the operational manager and treat delivery as successful if at least one channel succeeds, while recording any channel-specific failures. This gives the best operational resilience without requiring every channel to be perfectly available.

## Use Case 11
### Question 1
Question 1: Which surge detection approach should storm mode use, given that LightGBM is already the system's core model?

|--------|-------------|
| A | Use the active LightGBM P50 forecast residual and confirm surges only when both a residual z-score threshold and a percent-above-forecast floor pass. |
| B | Use the residual z-score threshold alone to confirm abnormal demand surges. |
| C | Train and serve a separate storm-mode machine learning detector. |
| Short | Provide a different short answer (<=5 words). |

Response: Choose Option A as LightGBM is the core model and storm mode should use a residual z-score over a rolling baseline plus a percent-above-forecast floor as a dual-check. A z-score alone cannot distinguish a meaningful surge from noisy residuals when forecast values are very low.

### Question 2
Question 2: Should UC-11 reuse UC-10 threshold-alert persistence or store surge records separately?

|--------|-------------|
| A | Reuse UC-10 threshold-alert tables for surge candidates, events, and delivery attempts. |
| B | Store surge candidates, confirmations, events, and delivery attempts in separate surge-specific tables. |
| C | Share notification-event tables but split only detector and state records. |
| Short | Provide a different short answer (<=5 words). |

Response: Choose Option B as surge events should use separate surge-specific tables and not share UC-10 persistence. Surge events have different trigger lineage and confirmation semantics from threshold alerts.

### Question 3
Question 3: When should surge detection run for UC-11?

|--------|-------------|
| A | Run on a fixed cron schedule independent of ingestion completion. |
| B | Trigger after each successful UC-01 ingestion run completes. |
| C | Run as a real-time streaming detector outside the ingestion workflow. |
| Short | Provide a different short answer (<=5 words). |

Response: Choose Option B as surge detection should run after each successful UC-01 ingestion run. This keeps surge checks grounded in the most recent ingested actuals without adding separate scheduling overhead.

## Use Case 12
### Question 1
Question 1: Driver Attribution Scope
What driver attribution output should the drill-down show for an alert?

Recommended: Option A — Show the top 5 ranked contributing drivers for the selected alert.

| Option | Description |
|--------|-------------|
| A | Show the top 5 ranked contributing drivers for the selected alert. |
| B | Show all available contributing drivers for the selected alert. |
| C | Show only the single highest-ranked contributing driver. |
| Short | Provide a different short answer (<=5 words). |

Response: Choose Option A as showing the top 5 ranked contributing drivers gives enough explanatory context for investigation without overcrowding the drill-down view. It also keeps the UI and acceptance criteria bounded around a consistent, testable driver set.

### Question 2
Question 2: Anomaly Context Window
What recent anomaly window should the detail view use around the selected alert?

Recommended: Option B — Show anomalies from the previous 7 days.

| Option | Description |
|--------|-------------|
| A | Show anomalies from the previous 24 hours. |
| B | Show anomalies from the previous 7 days. |
| C | Show anomalies from the previous 30 days. |
| Short | Provide a different short answer (<=5 words). |

Response: Choose Option B as a 7-day anomaly window provides enough recent context to interpret whether the alert fits an emerging pattern without making the detail timeline too noisy. It also aligns well with operational review over the past week.

### Question 3
Question 3: Multiple Missing Components
If two or more supporting components are unavailable, should the system still show whatever remains or switch to an error state?

Recommended: Option A — Show the remaining reliable context and clearly mark each unavailable component.

| Option | Description |
|--------|-------------|
| A | Show the remaining reliable context and clearly mark each unavailable component. |
| B | Switch to an overall error state whenever two or more supporting components are unavailable. |
| C | Show only alert metadata and hide all context panels when multiple supporting components are unavailable. |
| Short | Provide a different short answer (<=5 words). |

Response: Choose Option A as the drill-down should preserve any reliable context that is still available rather than discarding useful information. Clear unavailable-state labeling keeps the view honest while maintaining operational value during partial outages.

## Use Case 13

The original `/speckit.clarify` question text and option tables for UC-13 were not preserved in the repository, and no additional ambiguities remain beyond the accepted clarifications already captured in `spec.md`.

## Use Case 14

The original `/speckit.clarify` question text and option tables for UC-14 were not preserved in the repository, and no additional ambiguities remain beyond the accepted clarifications already captured in `spec.md`.

## Use Case 15

The original `/speckit.clarify` question text and option tables for UC-15 were not preserved in the repository. The accepted clarifications already captured in `spec.md` are that storm mode activates only for the affected scope, uses weather-only trigger inputs, and reverts both uncertainty and alert sensitivity to baseline when forecast adjustment fails.

## Use Case 17

The original `/speckit.clarify` question text and option tables for UC-17 were not preserved in the repository. The accepted clarifications already captured in `spec.md` are that the portal is anonymous, reads only the current approved public-safe forecast version, limits the response to public-safe category-level fields, and marks incomplete category coverage explicitly rather than implying omitted categories are zero.

## Use Case 18

### Question 1
Question 1:

| Option | Description |
|--------|-------------|
| A | Any signed-in user can access the user guide |
| B | Only specific roles can access the user guide |
| C | The guide is public, even without sign-in |
| Short | Provide a different short answer (<=5 words) |

Response: Choose Option A as the spec currently assumes the user guide is broadly available to any product user, which is the lowest-friction and lowest-risk default for internal help content unless there is a compliance reason to restrict it.

## Use Case 19
### Question 1
Question 1: Who is allowed to submit feedback/bug reports?

| Option | Description |
|--------|-------------|
| A | Authenticated users only; require signed-in identity on every submission. |
| B | Allow anonymous and authenticated submissions; contact info optional. |
| C | Allow anonymous feedback, but require authentication for bug reports. |
| Short | Provide a different short answer (<=5 words). |

Response: Chose Option B as this maximizes the number of reports we can receive to make the app better. It also allows for following up on users who decide to include contact info.

## Question 2
Question 2: Should users be required to classify submissions as Feedback vs Bug Report at the time of
submission?


| Option | Description |
|--------|-------------|
| A | Require users to choose exactly one type: Feedback or Bug Report. |
| B | Make type optional; system/team can classify later. |
| C | Auto-classify by content only; do not ask user for type. |
| Short | Provide a different short answer (<=5 words). |

Response: Chose Option A since making this explicit makes things more obvious and clear. It also helps us identify weakpoints in our app earlier if these are already classified.
