# Codex Token Tally — Proactive311

> All token counts are for `codex exec` runs using `gpt-5.2-codex` / `gpt-5.4` (high reasoning effort).  
> "Session" = one `codex exec` invocation.

---

## Pre-UC-11 Usage (prior sessions)

| Description | Tokens |
|-------------|--------|
| All prior Codex sessions (UC-01 through UC-10 + setup) | 43,238 |
| **Subtotal** | **43,238** |

---

## UC-11 — Notify on Abnormal Demand Surge Detection

**Branch**: `011-abnormal-demand-surge-notifications`  
**Date**: 2026-03-13

| Step | Codex Command / Session | Tokens Used | Running Total |
|------|------------------------|-------------|---------------|
| 0 | Prior sessions (carried forward) | 43,238 | 43,238 |
| 1 | `/speckit.specify` — generate spec.md from UC-11.md + UC-11-AT.md | 36,679 | 79,917 |
| 2 | `/speckit.clarify` — surface 3 ambiguities | 17,574 | 97,491 |
| 3 | Apply clarification answers (dual-threshold, separate tables, event-triggered) | 29,976 | 127,467 |
| 4 | `/speckit.plan` — plan.md, data-model.md, research.md, quickstart.md, surge-alerts-api.yaml | 81,993 | 209,460 |
| 5 | `/speckit.checklist` — requirements.md + ux-data-performance-api-security.md | 29,242 | 238,702 |
| 6 | `/speckit.tasks` — tasks.md | 38,537 | 277,239 |
| 7 | `/speckit.analyze` — analysis table + in-place fixes for 3 HIGH findings | 100,728 | 377,967 |
| 8 | Fix 2 MEDIUM findings (A04 daily-only forecast, A05 config precedence) | 27,651 | 405,618 |
| 9 | Update all 6 `docs/` validation report files | 123,406 | 529,024 |

**UC-11 subtotal**: 485,786 tokens  
**Grand total to date**: **529,024 tokens**

---

## Summary

| Milestone | Cumulative Total |
|-----------|-----------------|
| After prior sessions (pre-UC-11) | 43,238 |
| After UC-11 complete | **529,024** |
