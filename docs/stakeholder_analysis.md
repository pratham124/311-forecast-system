# Stakeholder Analysis

## Proactive311 System

### Time Series Forecasting & Alerting System for Edmonton 311 Service Demand

---

## 1. Purpose

This document identifies all stakeholders of the Proactive311 project and conducts an impact analysis for each one. Proactive311 is a time series forecasting and alerting system designed to support the City of Edmonton's 311 service operations by providing demand forecasting, anomaly detection, and alerting capabilities that enable proactive resource allocation.

## 2. Stakeholder Identification

Stakeholders were identified through analysis of the project's requirements, system architecture, and organizational context. They are classified as **internal** (within the City of Edmonton or the project delivery organization) or **external** (outside the delivery organization but affected by or able to affect the project).

| # | Stakeholder | Type | Role |
|---|-------------|------|------|
| 1 | Operational Managers | Internal | Manage daily 311 staffing, dispatch, and resource allocation. Primary users of demand forecasts and alerts. |
| 2 | City Planners / Performance Teams | Internal | Conduct strategic capacity planning, performance evaluation, and budget allocation using historical trends and forecast analytics. |
| 3 | Developers | Internal | Design, build, test, deploy, and maintain the Proactive311 system. |
| 4 | Edmonton Residents | External | Members of the public who use 311 services and may access a public-facing forecast portal. |
| 5 | Data Providers | External | External services that supply 311 service request data and weather data (e.g., City of Edmonton Open Data, Environment and Climate Change Canada) via APIs. |
| 6 | Field Workers | Internal | 311 service personnel (e.g., road maintenance, sanitation, forestry) whose schedules are directly influenced by forecast-driven staffing decisions. |

---

## 3. Impact Analysis

This section conducts an impact analysis for each identified stakeholder, assessing:

- **Expectations** -- What the stakeholder wants or needs from the project.
- **Influence** -- Their ability to affect project decisions and outcomes.
- **Stance** -- Whether they are supportive, neutral, or opposed.
- **Impact of the project on them** -- How the project changes their situation.
- **Impact of them on the project** -- How they can help or hinder the project.
- **Risks they may pose** -- Threats to the project stemming from this stakeholder.

---

### 3.1 Operational Managers

| Dimension | Assessment |
|-----------|------------|
| **Expectations** | Accurate short-term (1-day) and medium-term (7-day) demand forecasts. Reliable threshold-based and anomaly alerts with configurable notification settings. Weather-aware forecasts with confidence indicators. High system availability during operational hours. An interface that supports rapid decision-making rather than adding complexity. |
| **Influence** | **High.** They are the primary users. Their adoption or rejection directly determines whether the system delivers value. Their operational feedback is the primary input for validating and improving forecast models. |
| **Stance** | **Supportive** -- provided the system demonstrably improves their ability to plan staffing and dispatch. Will become resistant if early experiences are poor or if the system adds overhead without clear benefit. |
| **Impact on them** | **Positive:** Enables proactive rather than reactive staffing, reducing overtime, missed demand, and last-minute scrambling. **Negative (if system fails):** Inaccurate forecasts lead to poor staffing decisions, eroding trust and causing reversion to manual judgment -- leaving them worse off than before because they invested time learning a tool they now distrust. |
| **Impact on project** | Their buy-in is essential. If Operational Managers refuse to use the system, the project fails regardless of technical quality. Conversely, their enthusiastic adoption creates a virtuous cycle of feedback and improvement. |
| **Risks** | Resistance to change if the interface is perceived as complex or disruptive to existing workflows. Alert fatigue from excessive false-positive notifications, leading to all alerts being ignored. Loss of trust from early forecast errors that are not quickly acknowledged and addressed. |

---

### 3.2 City Planners / Performance Teams

| Dimension | Assessment |
|-----------|------------|
| **Expectations** | Validated, deduplicated historical data. Ability to explore trends by service category, geography, and time range. Forecast accuracy metrics that compare the system against simple baseline methods to prove it adds value. Cross-category and cross-geography comparison tools for resource prioritization. |
| **Influence** | **High.** They control budget allocation and strategic priorities. Their evaluation of the system's return on investment determines whether funding continues. They also shape which features are prioritized. |
| **Stance** | **Supportive** -- when clear evidence of value is presented. May become skeptical if accuracy is unclear, data quality is questionable, or the system cannot answer the strategic questions they need for capacity planning. |
| **Impact on them** | **Positive:** Data-driven evidence for capacity planning, resource allocation, and performance reporting that was previously unavailable or manually assembled. **Negative:** If data quality is poor or forecasts are inaccurate, analyses built on the system's output are compromised, creating accountability risk for planners who relied on it. |
| **Impact on project** | They approve or deny funding and set feature priorities. Their satisfaction directly determines the project's long-term survival. Scope creep is a risk if their analytical ambitions outpace the project's delivery capacity. |
| **Risks** | Withdrawing support if return on investment is not demonstrated within a reasonable timeframe. Expanding scope with new analytical requests that delay core delivery. Questioning data integrity in ways that undermine confidence across all stakeholder groups. |

---

### 3.3 Developers

| Dimension | Assessment |
|-----------|------------|
| **Expectations** | Clear, stable requirements. Well-defined API contracts with data providers. Adequate testing infrastructure and deployment pipelines. Access to domain expertise for forecasting model decisions. Sustainable development pace without constant scope changes. |
| **Influence** | **Medium-High.** They make all technical implementation and architecture decisions. Their choices directly determine system quality, performance, scalability, and long-term maintainability. |
| **Stance** | **Supportive** -- when the project has clear goals, balanced scope, and reasonable timelines. Will become disengaged or resistant if requirements constantly shift, timelines are unrealistic, or technical debt is ignored. |
| **Impact on them** | The project is their primary work deliverable. Success builds professional skills and reputation; poor management creates frustration and burnout. Unreasonable timelines or shifting requirements erode quality and morale. |
| **Impact on project** | They are the builders. Turnover, burnout, or poor technical decisions directly threaten delivery timeline and system quality. Concentrated knowledge in one team member creates a single point of failure. |
| **Risks** | Key-person dependency if specialized forecasting knowledge is held by one developer. Accumulation of technical debt from rushed iterations that makes future changes increasingly expensive. Burnout from scope creep or timeline pressure. Insufficient domain knowledge leading to poorly tuned forecast models that underperform in practice. |

---

### 3.4 Edmonton Residents

| Dimension | Assessment |
|-----------|------------|
| **Expectations** | Transparent, easy-to-understand information about expected 311 service demand. Privacy protection -- no personal or identifiable data exposed through the public portal. An accessible interface usable by people with varying levels of technical literacy and ability. Improved 311 service quality as a result of better city resource planning. |
| **Influence** | **Low** individually; **Medium** collectively. Public opinion influences political decisions. Social media amplifies complaints rapidly and can shift the political calculus around project funding. |
| **Stance** | **Neutral to supportive** -- if the system visibly improves 311 service quality or provides useful public information. Most residents will be unaware of the system unless it affects their service experience or a public portal is prominently available. |
| **Impact on them** | **Positive:** Better-informed decisions about when and how to access 311 services. Improved service quality from more efficient city resource allocation. Greater transparency into municipal operations. **Negative:** Privacy risks if the system exposes sensitive data. Frustration if the public portal is confusing, inaccessible, or presents misleading information. |
| **Impact on project** | Public support provides political legitimacy and justifies continued funding. Public complaints -- especially about privacy, accessibility, or service quality -- create political pressure that can force project changes or defunding. |
| **Risks** | Privacy incidents that erode public trust and trigger regulatory consequences. Accessibility failures that exclude portions of the population and invite legal or advocacy challenges. Misinterpretation of forecast information leading to public confusion or unfounded criticism of the city. |

---

### 3.5 Data Providers

| Dimension | Assessment |
|-----------|------------|
| **Expectations** | Compliance with API terms of use and rate limits. Responsible and secure use of their data. Manageable load on their infrastructure from automated pulls. Stable, predictable data consumption patterns. |
| **Influence** | **Critical.** The entire system depends on their data. If 311 data providers restrict access, change schemas without notice, or suffer outages, the system's core forecasting capability is immediately degraded or disabled. Weather data providers have a secondary but important influence on forecast enrichment and storm-mode features. |
| **Stance** | **Neutral.** Proactive311 is one of many consumers of their data. They are neither advocates nor opponents -- they simply expect their terms to be respected. |
| **Impact on them** | Additional API consumption load. Reputational exposure if their data is misused or if a data-driven decision based on their data causes public harm. Potential increase in support requests if integration issues arise. |
| **Impact on project** | They are a critical dependency. Data availability, quality, freshness, and schema stability directly determine whether the system can produce accurate forecasts. A single unannounced schema change can break the entire data ingestion pipeline. |
| **Risks** | API withdrawal or access restriction due to policy changes. Unannounced schema changes that break ingestion and go undetected until forecasts degrade. Prolonged outages that leave the system operating on stale data. Licensing or terms-of-use changes that restrict how data can be processed, stored, or publicly displayed. |

---

### 3.6 Field Workers

| Dimension | Assessment |
|-----------|------------|
| **Expectations** | Fair and predictable work scheduling. Adequate staffing during peak demand periods so they are not chronically overworked. Advance notice of expected high-demand shifts. Human oversight over scheduling decisions -- not purely algorithmic assignment without manager judgment. |
| **Influence** | **Low** directly. They do not interact with the system and have limited formal decision authority. However, they exert indirect influence through union channels, manager feedback, absenteeism rates, and public statements. Collective action through organized labor can create significant project friction. |
| **Stance** | **Neutral to supportive** -- if forecasts lead to better, more predictable staffing. Potentially **opposed** if they perceive themselves as being managed by an algorithm without human consideration, or if the system is used to justify understaffing. |
| **Impact on them** | **Positive:** Better demand forecasts lead to more predictable schedules, fewer emergency call-ins, more adequate staffing during surges, and less chronic overwork. **Negative:** If the system systematically underestimates demand, they bear the real-world consequences through overwork, unpredictable schedule disruptions, and unsafe workloads. They are the stakeholder group most concretely affected by forecast errors. |
| **Impact on project** | Indirect but significant. Worker dissatisfaction surfaces through unions, media, or manager feedback and creates political pressure to modify or halt the project. Their on-the-ground experience is the ultimate validation of whether forecasts translate to real operational improvement. |
| **Risks** | Formal grievances through labor channels if algorithmic scheduling is perceived as unfair or if collective agreements are violated. Low morale and increased absenteeism. Negative media coverage if workers speak publicly about poor conditions linked to the system. Union-led political pressure to constrain or defund the project. |

---

## 4. Regulatory, Legal, Environmental, Social, and Ethical Considerations

The following constraints and sensitivities cut across the stakeholder landscape and must be considered in project decisions, system design, and stakeholder engagement.

### 4.1 Regulatory and Legal

| Consideration | Description | Affected Stakeholders |
|---------------|-------------|----------------------|
| **Federal PIPEDA Act** | The Personal Information Protection and Electronic Documents Act applies where personal information crosses provincial or organizational boundaries. If third-party data providers supply information that could identify individuals, PIPEDA obligations may apply. | Data Providers, Edmonton Residents |
| **Open Data Licensing** | 311 and weather data may be subject to open data licenses that restrict use, require attribution, or impose redistribution conditions. | Data Providers, Developers |
| **Labor Law and Collective Agreements** | Scheduling decisions influenced by the system must comply with collective bargaining agreements, overtime rules, and employment standards legislation. | Field Workers, Operational Managers |

### 4.2 Environmental

Proactive311 is a support web application, so it does not directly alter the physical environment. However, there are some environmental considerations:

- **Environmental Event Awareness.** The system ingests weather data and supports storm-mode forecasting, aligning operational planning with environmental conditions such as floods, extreme cold, or severe storms.
- **Indirect Efficiency Gains.** Better resource allocation (fewer unnecessary dispatches, improved crew routing) could modestly reduce the environmental footprint of 311 operations.
- **Infrastructure Energy.** Data centre and cloud infrastructure consume energy. The project should align with the city's sustainability policies.
- **Machine learning training.** Machine learning is widely known to require lots of energy from the power grid. We should strive to limit the amount of power we use to train our models.

### 4.3 Social

| Consideration | Description | Affected Stakeholders |
|---------------|-------------|----------------------|
| **Equity of Service** | Forecast-driven resource allocation must not systematically disadvantage any neighbourhood or demographic. Historical data biases (e.g., underreporting from certain areas) could perpetuate inequitable service distribution if not identified and corrected. | Edmonton Residents, City Planners |
| **Accessibility** | Public-facing features must comply with Web Content Accessibility Guidelines (WCAG) and be usable by people with disabilities, limited English proficiency, and varying digital literacy. | Edmonton Residents |
| **Worker Dignity** | Field workers must not be reduced to units in an optimization algorithm. Human oversight of scheduling decisions is essential, and workers should understand how forecasts inform their assignments. | Field Workers, Operational Managers |
| **Public Trust** | The public must trust that the system uses data responsibly and that forecast-driven decisions serve their interests. Transparency about system capabilities and limitations is critical. | Edmonton Residents |

### 4.4 Ethical

| Consideration | Description | Affected Stakeholders |
|---------------|-------------|----------------------|
| **Algorithmic Fairness** | Forecasting models must be evaluated for bias. If training data reflects historical inequities in service delivery, the model may perpetuate those inequities. Regular bias audits should be conducted. | Edmonton Residents, City Planners |
| **Transparency and Explainability** | Stakeholders should be able to understand why the system produces a given forecast or alert. Unexplainable models undermine trust and accountability. | Operational Managers, City Planners |
| **Human Oversight** | The system should support decision-making, not replace it. Operational Managers must retain authority to override forecasts and alerts based on their judgment. | Operational Managers, Field Workers |
| **Purpose Limitation** | Data collected for 311 forecasting must not be repurposed for surveillance, individual worker performance monitoring, or other uses beyond the stated purpose. | Field Workers, Edmonton Residents |
| **Minimal Data Collection** | The system should collect only data necessary for its stated purpose. Unnecessary collection of personal or sensitive information increases risk without adding value. | Edmonton Residents, Data Providers |

---

## 5. Risk Analysis

The following table consolidates stakeholder-related risks from the impact analysis.

| Risk | Impact | Likelihood | Mitigation Strategy | Contingency Plan |
|------|--------|------------|---------------------|------------------|
| Low adoption by Operational Managers | **High** | **Medium** | Early involvement in design. Iterative prototyping with feedback loops. Training and onboarding. | Assign change champions. Simplify the interface based on usability testing. |
| Data Provider API disruption or withdrawal | **High** | **Low** | Formalize SLAs. Implement data caching and fallback mechanisms. | Activate cached data. Explore alternative sources. Enable manual upload. |
| Forecast inaccuracy erodes trust | **High** | **Medium** | Evaluate against baselines. Display confidence indicators. Publish accuracy metrics. | Revert to baselines. Root cause analysis. Retrain models. |
| Alert fatigue from excessive notifications | **Medium** | **Medium** | Configurable thresholds. False-positive filtering. Contextual alert drill-down. | Increase thresholds temporarily. Batch alerts into digests. |
| Scope creep from City Planners | **Medium** | **High** | Formal change request process. Feature prioritization. Regular scope reviews. | Defer to future releases. Re-baseline timeline. |
| Public data privacy incident | **High** | **Low** | Data filtering for public portal. Security audits. Privacy impact assessment. | Suspend portal. Investigate breach. Notify per FOIP. |
| Developer turnover or knowledge loss | **Medium** | **Medium** | Documentation. Code reviews. Cross-training. Knowledge sharing. | Onboard replacements via docs. Engage contract resources. |
| Field worker dissatisfaction with scheduling | **Low** | **Medium** | Communicate benefits. Gather feedback via managers. Ensure human oversight. | Adjust forecast-to-schedule translation. Increase manager discretion. |
| Weather data unavailability | **Medium** | **Low** | Graceful degradation. Caching. Multiple sources. | Disable overlay. Widen uncertainty bands. Alert managers. |
| City funding withdrawal | **High** | **Low** | Regular ROI reporting. Demonstrate value. Align with city strategy. | Minimum viable scope. Alternative funding. Phased delivery. |

---

## 6. Plan Responses

In order to plan responses for our stakeholders, we must first do the following three actions:

1. **Support your friends** Operational Managers and City Planners are the primary beneficiaries. Maintain close, collaborative engagement. Respond to feedback rapidly. Demonstrate value continuously.

2. **Make new friends** Edmonton Residents and Field Workers are not natural allies but can become supporters through transparency, demonstrated improvement in service quality and scheduling, and genuine communication.

3. **Neutralize opposition.** Data Providers require reliability and compliance to remain cooperative. Field Workers' concerns about algorithmic scheduling must be addressed proactively through human oversight guarantees and transparent communication about how forecasts inform staffing.

---

## 7. Execute Plans and Monitor

### 7.1 Evaluation Questions

At each review cycle, the following questions must be answered:

1. **Were we successful in meeting the needs of our supporters?** Track whether Operational Managers and City Planners have their expectations met and remain actively engaged.

2. **Were we successful in expanding our base of support?** Assess whether Residents and Field Workers have become more supportive through demonstrated value and transparent communication.

3. **Were we successful in neutralizing our opponents?** Monitor whether Data Provider concerns are addressed and Field Worker scheduling concerns have been mitigated through human oversight.

4. **Do these answers change over time?** Stakeholder positions evolve. This analysis must be revisited as the project progresses.

### 7.2 Review Schedule

| Review | Scope | Frequency |
|--------|-------|-----------|
| Sprint Retrospective | Developer engagement, blockers | Every 2 weeks |
| Operational Review | Manager satisfaction, forecast usage | Monthly |
| Stakeholder Health Check | All engagement metrics | Quarterly |
| Strategic Review | ROI, city goal alignment, funding | Semi-annually |

---

## References

1. Project Management Institute (PMI). (2017). *A Guide to the Project Management Body of Knowledge (PMBOK Guide)*, 6th Edition. Newtown Square, PA: Project Management Institute.

---
