# Clarification Report

Below is a report of the clarifications that Codex requested after running the /speckit.clarify command for each use case. We've included the options we chose and a short justification for it as well. These clarifications were used to help validate our specifications generated via /speckit.specify.

Below is a template of how we should write the clarify report based on how it was done in lab2.
Copy the question and the recommended option if codex gives you one and write the response + a justification for that. Sometimes codex asks frivolous questions though so ignore any questions that you think have already been answered in the spec.

## Use Case X (TEMPLATE)

### Question 1 (TEMPLATE)
Question 1 (Announcements Ordering)
We need to remove ambiguity about how public announcements are presented, since it affects UI behavior and acceptance
testing.

Recommended: Option A — Newest-first is the most common and predictable for announcement feeds, and minimizes user effort
to find current info.

| Option | Description |
|--------|-------------|
| A | Newest-first (most recent announcement on top) |
| B | Oldest-first (chronological from earliest) |
| C | Group by category, then newest-first within each group |
| D | Group by importance/priority, then newest-first within each group |
| Short | Provide a different short answer (<=5 words) |

Response: Chose option A since newest first makes sense and is expected from a UX view.

### Question 2
Question 2 (Announcement Detail Navigation)
This affects UX flow and acceptance checks: how should a guest get to the announcement details?

|--------|-------------|
| A | Click a list item to open a detail view |
| B | Expand/collapse details inline within the list |
| C | Open details in a modal overlay |
| Short | Provide a different short answer (<=5 words) |

Response: Chose option A since this simple design would be easy for users to understand. The annoucement might also be somewhat large so a modal overlay (option C) or doing it inline (option B) probably would not work very well.

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