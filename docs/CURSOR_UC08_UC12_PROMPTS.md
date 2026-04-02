# Standalone prompts: UC-07 through UC-12

Each block below is **self-contained**: copy it into your agent or pipe it as stdin to Codex. Nothing here assumes `./scripts/codex-uc-exec.sh` or reading this file again mid-run.

**Optional Codex invocation** (from your clone root, replace the path):

```bash
cd /path/to/311-forecast-system
codex exec --dangerously-bypass-approvals-and-sandbox --json -C "$(pwd)" -o /tmp/codex-last-message.txt
# Paste the chosen prompt at the prompt; or use a heredoc. For sandbox-only: CODEX_SANDBOXED=1 codex exec --full-auto --json -C "$(pwd)" -o /tmp/codex-last-message.txt
```

---

## UC-07 — Prompt 1 (start or full run)

```text
You are implementing UC-07 in the 311-forecast-system monorepo. Work only inside the real tree; do not create backend/src or a top-level tests directory.

You alone perform every read, write, search, replace, create, and delete needed for this task (docs/, specs/, backend/, frontend/, ui-playwright/). Complete implementation, tests, and verification in this session until every gate below passes. Do not stop after a single failing make coverage; iterate until done.

PATH REMAPPING (mandatory):
- Backend application code: backend/app/ (import package app). Alembic: backend/migrations/versions/. Tests: backend/tests/{contract,integration,unit}/. Frontend: frontend/src/; colocate Vitest; wire routes in app/main.py and App.tsx per existing patterns.
- Remap every wrong path in specs/007-historical-demand-exploration/tasks.md (ignore backend/src or top-level tests/).

Authoritative requirements:
- docs/UC-07.md and docs/UC-07-AT.md
- specs/007-historical-demand-exploration/spec.md, plan.md, data-model.md, research.md, quickstart.md
- specs/007-historical-demand-exploration/tasks.md — phases in order
- OpenAPI: specs/007-historical-demand-exploration/contracts/historical-demand-api.yaml

Engineering constraints:
- Match JWT auth, route dependencies, DB session, structured logging under backend/app/. Reuse UC-02 lineage where relevant. Do not weaken security; no secrets in logs.

Feature scope (UC-07):
Historical filter context and query endpoints; persistence per data-model; historical_context_service resolves approved cleaned dataset and reliable geography levels; historical_warning_service for high-volume warnings; outcomes no_data, retrieval_failed, render_failed; HistoricalDemandPage and historical-demand feature. historical_demand_service may be shared with UC-05—extend without breaking UC-05 tests or split responsibilities clearly.

100% LINE AND 100% BRANCH (mandatory — from backend/, use pytest --cov=<module> --cov-branch --cov-report=term-missing until term-missing shows no gaps for each path):
- app/api/routes/historical_demand.py
- app/services/historical_context_service.py
- app/services/historical_demand_service.py
- app/services/historical_warning_service.py
- app/repositories/historical_demand_repository.py
- app/schemas/historical_demand.py
- app/models/historical_analysis_models.py
Plus any new app/ modules you add for UC-07 per tasks.md.

Completion loop:
1. Fix code/tests.
2. From repo root: make test, then make coverage (run make install / backend-venv / backend-install / frontend-install if needed). make frontend-build for production parity.
3. Re-run targeted coverage on the list above until 100% line and branch on every listed path; then make coverage green.
4. Treat docs/UC-07-AT.md as acceptance truth.

Cross-UC: Do not break other use cases; unrelated tests stay green.

Git: Use the branch your team uses for UC-07 (no fixed branch name required here). Commit/push when done; no force-push without explicit user approval.

Deliverables: Implementation per tasks.md; green make test/coverage; 100% line+branch on listed modules; short summary of commands run.
```

## UC-07 — Prompt 2 (resume)

```text
Continue UC-07 only. Read git status and recent commits. Finish remaining specs/007-historical-demand-exploration/tasks.md with PATH REMAPPING to backend/app/ and backend/tests/.

Loop until done: fix → make test && make coverage → targeted pytest --cov --cov-branch --cov-report=term-missing on app/api/routes/historical_demand.py, app/services/historical_context_service.py, app/services/historical_demand_service.py, app/services/historical_warning_service.py, app/repositories/historical_demand_repository.py, app/schemas/historical_demand.py, app/models/historical_analysis_models.py (100% line+branch) → repeat.

No backend/src, no top-level tests/, no force-push.
```

---

## UC-08 — Prompt 1 (start or full run)

```text
You are implementing UC-08 in the 311-forecast-system monorepo. Work only inside the real tree; do not create backend/src or a top-level tests directory.

You alone perform every read, write, search, replace, create, and delete needed (docs/, specs/, backend/, frontend/, ui-playwright/). Complete all work in this session until every gate passes.

Git workflow (first, before commits):
- Branch exactly 008-compare-demand-forecasts (git checkout -b 008-compare-demand-forecasts or git checkout 008-compare-demand-forecasts). All commits on this branch only.

PATH REMAPPING (mandatory):
- backend/app/, backend/migrations/versions/, backend/tests/{contract,integration,unit}/, frontend/src/. Remap every path in specs/008-compare-demand-forecasts/tasks.md.

Authoritative requirements:
- docs/UC-08.md and docs/UC-08-AT.md
- specs/008-compare-demand-forecasts/spec.md, plan.md, data-model.md, research.md, quickstart.md
- specs/008-compare-demand-forecasts/tasks.md — phases in order
- OpenAPI: specs/008-compare-demand-forecasts/contracts/demand-comparison-api.yaml

Engineering constraints:
- Match existing JWT auth, route dependencies, DB session, structured logging. Do not weaken security; no secrets in logs.

Feature scope (UC-08):
Compare historical demand (UC-02 approved lineage) with forecast demand (active UC-03 or UC-04) for selected categories, optional geographies, one continuous time range. Deterministic forecast source selection; one allowable comparison granularity per plan/spec. Single outcome vocabulary; render_failed only via render-event path, not initial comparison response. Backend: demand_comparison_* services, DemandComparisonRepository, DemandLineageRepository, schemas and models per data-model. Frontend: demand-comparisons feature and DemandComparisonPage. US2: warning_required for large requests; missing combination and failure handling per spec.

100% LINE AND 100% BRANCH (mandatory — from backend/, pytest --cov=... --cov-branch --cov-report=term-missing until no gaps):
- app/api/routes/demand_comparisons.py
- app/services/demand_comparison_context_service.py
- app/services/demand_comparison_render_service.py
- app/services/demand_comparison_result_builder.py
- app/services/demand_comparison_service.py
- app/services/demand_comparison_source_resolution.py
- app/services/demand_comparison_warning_service.py
- app/services/demand_comparison_outcomes.py
- app/repositories/demand_comparison_repository.py
- app/repositories/demand_lineage_repository.py
- app/schemas/demand_comparison_api.py
- app/schemas/demand_comparison_models.py
- app/models/demand_comparison_models.py
- app/core/demand_comparison_observability.py

Local CI parity (mirror .github/workflows/ci.yml — mandatory before git commit/push):
1. cd backend/: Python 3.10 venv; pip from that venv only (e.g. python3.10 -m venv .venv && . .venv/bin/activate && python -m pip install -r requirements.txt, or uv venv + uv pip install -r requirements.txt --python .venv/bin/python). export DATABASE_URL=sqlite+pysqlite:///./ci-test.db. .venv/bin/python -m pytest — all pass.
2. cd frontend/: npm ci, npm test -- --run, npm run build — all pass.

Repo root: make test, make coverage — both green (make install / backend-venv / backend-install / frontend-install if needed). make frontend-build for production parity.

Automated UI E2E (mandatory before commit/push):
- Copy scripts/env.local.example to scripts/env.local; set E2E_EMAIL and E2E_PASSWORD (quote # and | in values).
- Start API (background): cd backend, export DATABASE_URL=sqlite+pysqlite:///./.e2e-app.sqlite, export FRONTEND_ORIGIN=http://127.0.0.1:5173, export SCHEDULER_ENABLED=false, export AUTH_COOKIE_SECURE=false, optionally AUTH_SIGNUP_ALLOWLIST if needed; run .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
- Start Vite (background): cd frontend, export VITE_API_BASE_URL=http://127.0.0.1:8000, run ./node_modules/.bin/vite --host 127.0.0.1 --port 5173 (npm install in frontend first if vite missing)
- Wait until curl -fsS http://127.0.0.1:8000/openapi.json and curl -fsS http://127.0.0.1:5173/ succeed
- cd ui-playwright && npm ci && npx playwright install chromium && npm run test:with-eval — exit 0; read ui-playwright/test-results/ui-smoke/evaluation-report.json and confirm "ok": true
- Stop background servers when finished. Extend ui-playwright/tests/ if this UC adds new primary signed-in surfaces.

Cross-UC: Unrelated tests stay green.

Git publish (only after UI E2E passes): git add, commit (e.g. feat(uc-08): demand comparison), git push -u origin 008-compare-demand-forecasts. If push fails (non-fast-forward), report and stop; no force-push without user approval.

Deliverables: tasks.md complete; CI parity; make test/coverage; 100% line+branch on listed modules; green UI E2E; commit+push when applicable; summary with manual URLs if you also started dev servers (e.g. http://127.0.0.1:5173/, http://127.0.0.1:8000/docs).
```

## UC-08 — Prompt 2 (resume)

```text
Continue UC-08 on branch 008-compare-demand-forecasts only. Read git status and recent commits. Finish remaining specs/008-compare-demand-forecasts/tasks.md with PATH REMAPPING to backend/app/ and backend/tests/.

Loop: fix → backend Python 3.10, DATABASE_URL=sqlite+pysqlite:///./ci-test.db, full pytest → frontend npm ci / npm test -- --run / npm run build → make test && make coverage → 100% line+branch on demand_comparisons route, demand_comparison_* services, demand_comparison_outcomes, demand_comparison_repository, demand_lineage_repository, demand_comparison_api/schemas/models, demand_comparison_models, demand_comparison_observability → E2E: scripts/env.local (E2E_EMAIL, E2E_PASSWORD); background backend uvicorn (sqlite .e2e-app.sqlite, FRONTEND_ORIGIN http://127.0.0.1:5173, SCHEDULER_ENABLED=false, AUTH_COOKIE_SECURE=false) on 8000; background frontend vite with VITE_API_BASE_URL=http://127.0.0.1:8000 on 5173; wait for /openapi.json and /; cd ui-playwright && npm ci && npx playwright install chromium && npm run test:with-eval; ui-playwright/test-results/ui-smoke/evaluation-report.json "ok": true → commit/push.

No backend/src, no force-push.
```

---

## UC-09 — Prompt 1 (start or full run)

```text
You are implementing UC-09 in the 311-forecast-system monorepo. Work only inside the real tree; do not create backend/src or a top-level tests directory.

You alone perform every repository change needed. Complete all work in this session until every gate passes.

Git workflow (first): Branch exactly 009-add-weather-overlay (create or checkout). All commits on this branch only.

PATH REMAPPING (mandatory):
- Map backend/src/... in specs/009-add-weather-overlay/tasks.md to backend/app/... (package app). Migrations: backend/migrations/versions/. Tests: backend/tests/{contract,integration,unit}/. Frontend: frontend/src/. Integrate overlay into the existing forecast visualization page/chart stack (e.g. ForecastVisualizationPage); do not duplicate the explorer unless tasks require it after remapping.

Authoritative requirements:
- docs/UC-09.md and docs/UC-09-AT.md
- specs/009-add-weather-overlay/spec.md, plan.md, data-model.md, research.md, quickstart.md
- specs/009-add-weather-overlay/tasks.md — phase order; remap all paths
- OpenAPI: specs/009-add-weather-overlay/contracts/weather-overlay-api.yaml

Engineering constraints:
- Match FastAPI, auth, DB, logging. Reuse/extend app/clients/geomet_client.py where appropriate. Persist operational/observability records per data-model. Non-visible states (unavailable, retrieval-failed, misaligned, failed-to-render) must not break the base chart.

Feature scope (UC-09):
Optional weather overlay on forecast visualization: alignment rules, GET overlay + POST render-events per contract, frontend controls/layer/status module.

100% LINE AND 100% BRANCH (mandatory):
- Every new/changed module under app/ whose primary responsibility is UC-09 weather overlay (routes, services, repositories, schemas, models) matching *weather*overlay* patterns, plus any dedicated overlay helpers. If you only extend geomet_client.py, cover those branches or extract testable helpers. List exact app/... paths you enforced in your summary.

Local CI parity (before commit/push):
1. cd backend/: Python 3.10 venv; export DATABASE_URL=sqlite+pysqlite:///./ci-test.db; full pytest — all pass.
2. cd frontend/: npm ci, npm test -- --run, npm run build — all pass.

Repo root: make test, make coverage — green. Loop targeted --cov --cov-branch on UC-09 modules until 100% line+branch, then full make coverage.

Automated UI E2E (mandatory before commit/push):
- Copy scripts/env.local.example to scripts/env.local; set E2E_EMAIL and E2E_PASSWORD (quote # and | in values).
- Start API (background): cd backend, export DATABASE_URL=sqlite+pysqlite:///./.e2e-app.sqlite, export FRONTEND_ORIGIN=http://127.0.0.1:5173, export SCHEDULER_ENABLED=false, export AUTH_COOKIE_SECURE=false, optionally AUTH_SIGNUP_ALLOWLIST; .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
- Start Vite (background): cd frontend, export VITE_API_BASE_URL=http://127.0.0.1:8000, ./node_modules/.bin/vite --host 127.0.0.1 --port 5173
- Wait until curl -fsS http://127.0.0.1:8000/openapi.json and curl -fsS http://127.0.0.1:5173/ succeed
- cd ui-playwright && npm ci && npx playwright install chromium && npm run test:with-eval — exit 0; confirm ui-playwright/test-results/ui-smoke/evaluation-report.json has "ok": true
- Stop background servers when finished.

Cross-UC: Unrelated tests stay green.

Git publish: feat(uc-09): weather overlay example message; git push -u origin 009-add-weather-overlay. No force-push without user approval.

Deliverables: Full tasks.md phases remapped; green gates; 100% line+branch on UC-09 backend scope; green UI E2E; commit+push when applicable.
```

## UC-09 — Prompt 2 (resume)

```text
Continue UC-09 on branch 009-add-weather-overlay. Remap tasks from backend/src to backend/app/. Finish remaining specs/009-add-weather-overlay/tasks.md.

Loop: fix → backend py3.10 + sqlite DATABASE_URL + full pytest → frontend npm ci/test/build → make test && make coverage → 100% line+branch on all UC-09 weather overlay app modules → E2E: env.local + API 8000 + Vite 5173 + ui-playwright npm run test:with-eval + evaluation-report.json ok → commit/push. Integrate overlay into existing forecast visualization page. No backend/src, no force-push.
```

---

## UC-10 — Prompt 1 (start or full run)

```text
You are implementing UC-10 in the 311-forecast-system monorepo. Work only inside the real tree; do not create backend/src or a top-level tests directory.

You alone perform every repository change needed. Complete all work in this session until every gate passes.

Git workflow (first): Branch exactly 010-demand-threshold-alerts (create or checkout). All commits on this branch only.

PATH REMAPPING: backend/app/, backend/migrations/versions/, backend/tests/, frontend/src/. Remap specs/010-demand-threshold-alerts/tasks.md.

Authoritative requirements:
- docs/UC-10.md and docs/UC-10-AT.md
- specs/010-demand-threshold-alerts/spec.md, plan.md, data-model.md, research.md, quickstart.md
- specs/010-demand-threshold-alerts/tasks.md
- OpenAPI: specs/010-demand-threshold-alerts/contracts/threshold-alerts-api.yaml

Engineering constraints:
- JWT auth, route dependencies, APScheduler-compatible scheduling (*_scheduler.py patterns). Geography-specific threshold precedence over category-only rules. Notification client abstraction — no hard-coded third-party credentials.

Feature scope (UC-10):
Threshold configuration, evaluation runs, per-scope outcomes, threshold state, notification events, channel attempts per data-model. Frontend alert review surfaces per tasks.

100% LINE AND 100% BRANCH (mandatory):
- All backend Python files primary to UC-10: threshold_* services, threshold_* repositories/models/schemas, forecast_alerts route module (or equivalent under app/api/routes/), threshold evaluation pipeline (or equivalent under app/pipelines/), notification client modules added for this UC. List enforced app/... paths in the summary.

Local CI parity: backend Python 3.10, export DATABASE_URL=sqlite+pysqlite:///./ci-test.db, full pytest; frontend npm ci, npm test -- --run, npm run build. Repo root: make test, make coverage.

Automated UI E2E (mandatory before commit/push): scripts/env.local with E2E_EMAIL/E2E_PASSWORD; background API on 8000 (backend .venv uvicorn, DATABASE_URL sqlite .e2e-app.sqlite, FRONTEND_ORIGIN, SCHEDULER_ENABLED=false, AUTH_COOKIE_SECURE=false); background Vite on 5173 with VITE_API_BASE_URL=http://127.0.0.1:8000; wait for /openapi.json and /; cd ui-playwright && npm ci && npx playwright install chromium && npm run test:with-eval; evaluation-report.json at ui-playwright/test-results/ui-smoke/ must show "ok": true. Extend ui-playwright if new primary signed-in routes are added.

Cross-UC: Unrelated tests stay green.

Git publish: e.g. feat(uc-10): demand threshold alerts; git push -u origin 010-demand-threshold-alerts. No force-push without user approval.

Deliverables: tasks.md remapped; green gates; 100% line+branch on UC-10 scope; green UI E2E; commit+push when applicable.
```

## UC-10 — Prompt 2 (resume)

```text
Continue UC-10 on branch 010-demand-threshold-alerts. Remap specs/010-demand-threshold-alerts/tasks.md paths to backend/app/.

Loop: fix → backend CI pytest → frontend build/test → make test && make coverage → 100% line+branch on all threshold/forecast-alerts/notification UC-10 app modules → UI E2E: env.local creds, API+Vite up, ui-playwright npm run test:with-eval, evaluation-report.json ok true → commit/push. Respect geography threshold precedence and scheduler patterns. No backend/src, no force-push.
```

---

## UC-11 — Prompt 1 (start or full run)

```text
You are implementing UC-11 in the 311-forecast-system monorepo. Work only inside the real tree; do not create backend/src or a top-level tests directory.

You alone perform every repository change needed. Complete all work in this session until every gate passes.

Git workflow (first): Branch exactly 011-abnormal-demand-surge-notifications (create or checkout). All commits on this branch only.

PATH REMAPPING: backend/app/, backend/migrations/versions/, backend/tests/, frontend/src/. Remap specs/011-abnormal-demand-surge-notifications/tasks.md away from backend/src.

Authoritative requirements:
- docs/UC-11.md and docs/UC-11-AT.md
- specs/011-abnormal-demand-surge-notifications/spec.md, plan.md, data-model.md, research.md, quickstart.md
- specs/011-abnormal-demand-surge-notifications/tasks.md
- OpenAPI: specs/011-abnormal-demand-surge-notifications/contracts/surge-alerts-api.yaml

Engineering constraints:
- Hook into ingestion/forecast lineage per spec. Dual-threshold confirmation, surge state machine, filtered/suppressed outcomes, notification persistence. Manual replay API per contract.

Feature scope (UC-11):
Residual vs active forecast surge detection (daily/weekly), z-score and percent-above-forecast confirmation, surge state, notifications and channel attempts, frontend surge review UI per tasks.

100% LINE AND 100% BRANCH (mandatory):
- surge_* services, repositories, models, schemas, surge_alerts routes, surge evaluation pipeline (names per your remapped app/ layout). List enforced paths in summary.

Local CI parity: backend py3.10 + sqlite DATABASE_URL + full pytest; frontend npm ci/test/build; make test && make coverage.

Automated UI E2E (mandatory before commit/push): scripts/env.local (E2E_EMAIL, E2E_PASSWORD); background: backend DATABASE_URL=sqlite+pysqlite:///./.e2e-app.sqlite, FRONTEND_ORIGIN=http://127.0.0.1:5173, SCHEDULER_ENABLED=false, AUTH_COOKIE_SECURE=false, .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000; frontend VITE_API_BASE_URL=http://127.0.0.1:8000, ./node_modules/.bin/vite --host 127.0.0.1 --port 5173; wait for http://127.0.0.1:8000/openapi.json and http://127.0.0.1:5173/; cd ui-playwright && npm ci && npx playwright install chromium && npm run test:with-eval; ui-playwright/test-results/ui-smoke/evaluation-report.json "ok": true. Extend Playwright if new primary routes.

Cross-UC: Unrelated tests stay green.

Git publish: e.g. feat(uc-11): abnormal demand surge notifications; git push -u origin 011-abnormal-demand-surge-notifications. No force-push without user approval.

Deliverables: tasks.md remapped; green gates; 100% line+branch on UC-11 scope; green UI E2E; commit+push when applicable.
```

## UC-11 — Prompt 2 (resume)

```text
Continue UC-11 on branch 011-abnormal-demand-surge-notifications. Remap tasks to backend/app/.

Loop: fix → backend CI → frontend → make test && make coverage → 100% line+branch on surge_* UC-11 app modules → Playwright test:with-eval + evaluation-report.json ok → commit/push. No backend/src, no force-push.
```

---

## UC-12 — Prompt 1 (start or full run)

```text
You are implementing UC-12 in the 311-forecast-system monorepo. Work only inside the real tree; do not create backend/src or a top-level tests directory.

You alone perform every repository change needed. Complete all work in this session until every gate passes.

Git workflow (first): Branch exactly 012-uc-12-drill-alert-details (create or checkout). All commits on this branch only.

PATH REMAPPING: backend/app/, backend/migrations/versions/, backend/tests/, frontend/src/features/alert-details/ (or equivalent). Remap specs/012-uc-12-drill-alert-details/tasks.md from backend/src.

Authoritative requirements:
- docs/UC-12.md and docs/UC-12-AT.md
- specs/012-uc-12-drill-alert-details/spec.md, plan.md, data-model.md, research.md, quickstart.md
- specs/012-uc-12-drill-alert-details/tasks.md
- OpenAPI: specs/012-uc-12-drill-alert-details/contracts/alert-detail-context-api.yaml

Engineering constraints:
- alert_source_resolution_service (or equivalent) must resolve threshold_alert and surge_alert against UC-10 and UC-11 persistence. If those features are absent on the branch, avoid weakening contracts: prefer real models; use minimal stubs only where unavoidable and document gaps.

Feature scope (UC-12):
Authenticated drill-down: forecast distribution, top-5 drivers, 7-day anomaly context; partial and error states; render-event reporting; correlated observability (AlertDetailLoadRecord) per data-model.

100% LINE AND 100% BRANCH (mandatory):
- alert_detail*, alert_distribution_context_service, alert_driver_context_service, alert_anomaly_context_service, alert_source_resolution_service, routes/schemas/models/repos introduced for drill-down. List enforced app/... paths in summary.

Local CI parity: backend py3.10 + sqlite DATABASE_URL + full pytest; frontend npm ci/test/build; make test && make coverage.

Automated UI E2E (mandatory before commit/push): scripts/env.local (E2E_EMAIL, E2E_PASSWORD); background: backend DATABASE_URL=sqlite+pysqlite:///./.e2e-app.sqlite, FRONTEND_ORIGIN=http://127.0.0.1:5173, SCHEDULER_ENABLED=false, AUTH_COOKIE_SECURE=false, .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000; frontend VITE_API_BASE_URL=http://127.0.0.1:8000, ./node_modules/.bin/vite --host 127.0.0.1 --port 5173; wait for http://127.0.0.1:8000/openapi.json and http://127.0.0.1:5173/; cd ui-playwright && npm ci && npx playwright install chromium && npm run test:with-eval; ui-playwright/test-results/ui-smoke/evaluation-report.json "ok": true.

Cross-UC: Unrelated tests stay green.

Git publish: e.g. feat(uc-12): drill alert details and context; git push -u origin 012-uc-12-drill-alert-details. No force-push without user approval.

Deliverables: tasks.md remapped; green gates; 100% line+branch on UC-12 scope; green UI E2E; commit+push when applicable.
```

## UC-12 — Prompt 2 (resume)

```text
Continue UC-12 on branch 012-uc-12-drill-alert-details. Remap tasks to backend/app/.

Loop: fix → backend CI → frontend → make test && make coverage → 100% line+branch on alert detail/source resolution app modules → Playwright test:with-eval + evaluation-report.json ok → commit/push. Resolve threshold vs surge sources per UC-10/11 persistence. No backend/src, no force-push.
```
