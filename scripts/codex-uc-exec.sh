#!/usr/bin/env bash
# Run Codex non-interactively for UC-07 through UC-12 implementation prompts.
# Usage: REPO=/path/to/clone ./scripts/codex-uc-exec.sh 07
# Default REPO is the parent of this script (repository root).
#
# Uses codex exec --json; after each run prints token breakdown (input / cached_input /
# output / reasoning) to stderr and appends JSON to CODEX_USAGE_LOG (see finalize_usage_from_jsonl).
# Install jq for aggregation. Raw JSONL: /tmp/codex-uc<NN>-last-run.jsonl
#
# By default runs with --dangerously-bypass-approvals-and-sandbox (without --full-auto; current
# Codex rejects using both). That lets the agent use git without sandbox blocking .git. Risky:
# only use on repos you trust. Set CODEX_SANDBOXED=1 for --full-auto + workspace-write sandbox only.
#
# All UC prompts instruct Codex to: from repo root run `make test` and `make coverage`, then fix
# failures until green and branch coverage meets requirements for new/changed code; limit scope to
# the target UC. UC-08–UC-12 also: spec branch; local CI parity (venv + sqlite DB + pytest + npm ci
# / test / build like .github/workflows/ci.yml); commit and push; launch API + Vite in background.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="${REPO:-$(cd "$SCRIPT_DIR/.." && pwd)}"
UC="${1:-}"

if [[ ! "$UC" =~ ^(07|08|09|10|11|12)$ ]]; then
  echo "Usage: $0 07|08|09|10|11|12" >&2
  echo "Optional: set REPO to your clone path (default: $REPO)" >&2
  exit 1
fi

OUT="/tmp/codex-uc${UC}-last-message.txt"
cd "$REPO"

# CODEX_USAGE_LOG: append one JSON object per run (default: under ~/Documents/capstone/codex-logs-311).
# Requires jq for aggregation. JSONL for the run is always at /tmp/codex-uc${UC}-last-run.jsonl
run_codex_uc() {
  local jsonl="/tmp/codex-uc${UC}-last-run.jsonl"
  local -a mode=()
  if [[ -n "${CODEX_SANDBOXED:-}" ]]; then
    mode=(--full-auto)
  else
    mode=(--dangerously-bypass-approvals-and-sandbox)
  fi
  # No prompt argument: Codex reads instructions from stdin (the heredoc). Do not pass `-`; some
  # Codex builds reject it ("unexpected argument '-' found").
  codex exec "${mode[@]}" --json -C "$REPO" -o "$OUT" 2>&1 | tee "$jsonl"
  local cx="${PIPESTATUS[0]}"
  finalize_usage_from_jsonl "$jsonl" "$UC" || true
  return "$cx"
}

finalize_usage_from_jsonl() {
  local jsonl="$1" uc="$2"
  local log="${CODEX_USAGE_LOG:-$HOME/Documents/capstone/codex-logs-311/usage-runs.jsonl}"
  [[ -f "$jsonl" ]] || return 0
  if ! command -v jq &>/dev/null; then
    echo "codex-uc-exec: install jq to print an aggregated token breakdown; raw JSONL: $jsonl" >&2
    return 0
  fi
  mkdir -p "$(dirname "$log")" 2>/dev/null || true
  local totals
  totals=$(jq -s -c '
    [.[] | select(.type == "turn.completed" and (.usage | type) == "object") | .usage]
    | if length == 0 then
        {"input_tokens":0,"cached_input_tokens":0,"output_tokens":0,"reasoning_tokens":0}
      else
        reduce .[] as $u ({
            input_tokens: 0,
            cached_input_tokens: 0,
            output_tokens: 0,
            reasoning_tokens: 0
          };
            .input_tokens += ($u.input_tokens // 0) |
            .cached_input_tokens += ($u.cached_input_tokens // 0) |
            .output_tokens += ($u.output_tokens // 0) |
            .reasoning_tokens += ($u.reasoning_tokens // 0)
          )
      end
    ' "$jsonl")
  printf '\n=== Codex token usage (UC-%s, summed over turns) ===\n' "$uc" >&2
  echo "$totals" | jq -r '
    "  input_tokens:         \(.input_tokens // 0)",
    "  cached_input_tokens:  \(.cached_input_tokens // 0)",
    "  output_tokens:        \(.output_tokens // 0)",
    "  reasoning_tokens:     \(.reasoning_tokens // 0)"
  ' >&2
  jq -n --argjson u "$totals" --arg dt "$(date -u +%Y-%m-%dT%H:%M:%SZ)" --arg uc "$uc" \
    '{utc: $dt, uc: $uc, usage: $u}' >>"$log" 2>/dev/null || true
  echo "  (append log: $log)" >&2
}

case "$UC" in
07)
  run_codex_uc <<'EOF'
You are implementing UC-07 in the 311-forecast-system monorepo. Work only inside the real tree; do not create backend/src or a top-level tests directory.

PATH REMAPPING (mandatory):
- All backend application code lives under backend/app/ (import package app). New modules go next to existing routes, services, repositories, schemas, models, pipelines, clients, core.
- Alembic migrations live under backend/migrations/versions/ (not backend/alembic). Follow existing revision naming and upgrade pattern from backend/migrations/env.py and backend/app/core/db.py.
- Backend tests live under backend/tests/contract, backend/tests/integration, backend/tests/unit with pytest markers as in backend/pyproject.toml.
- Frontend: Vite + React under frontend/src/; colocate Vitest tests like existing pages. Wire new pages in frontend/src/App.tsx and match Tailwind/UI patterns from existing features.

Authoritative requirements (read before coding):
- docs/UC-07.md and docs/UC-07-AT.md (acceptance source of truth).
- specs/007-historical-demand-exploration/spec.md, plan.md, data-model.md, research.md, quickstart.md.
- specs/007-historical-demand-exploration/tasks.md — execute phases in order (Setup → Foundational → US1 → … → Polish). For every task, map file paths through PATH REMAPPING; ignore wrong paths in tasks.md that point to backend/src or root tests/.
- OpenAPI: specs/007-historical-demand-exploration/contracts/historical-demand-api.yaml — align route paths, schemas, and status codes.

Engineering constraints:
- Match existing patterns: JWT auth in app/core/auth.py, route dependencies in app/api/dependencies/, FastAPI routers included from app/main.py, SQLAlchemy session via get_db_session, structured logging in app/core/logging.py where applicable.
- Reuse existing integrations where relevant (cleaned dataset / forecast lineage) instead of duplicating.
- Do not weaken security: enforce roles per spec; no secrets in logs.

Post-implementation verification (mandatory — from the repository root, the directory that contains the top-level Makefile):
- **Makefile alignment:** The root Makefile defines `test` as `backend-test` then `frontend-test` (`cd backend && .venv/bin/pytest`, then `cd frontend && npm test`). `coverage` is an alias of `backend-coverage` only (`cd backend && .venv/bin/pytest --cov=app --cov-branch --cov-report=term-missing`); it does not run frontend coverage. If `make test` fails because the venv or deps are missing, run `make install` (or `make backend-venv`, `make backend-install`, `make frontend-install` per `make help`). For the same build check the Makefile uses for frontend release, run `make frontend-build` (sets `VITE_API_BASE_URL` like local dev).
1. Run `make test`. All backend and frontend tests must pass.
2. Run `make coverage`. If any tests fail, or branch coverage for new/changed code does not meet project or lab requirements (e.g. 100% branch on new code where required), fix the code or tests—by editing directly or by a follow-up Codex run with specific instructions—until both `make test` and `make coverage` are satisfactory.
3. Treat docs/UC-07-AT.md as the acceptance source of truth; implement those scenarios and keep automated coverage aligned with them.

Cross-use-case scope:
- Do not change behavior or structure intended for other use cases except minimal unavoidable shared wiring; all unrelated tests must remain green.

Feature scope (UC-07):
Explore Historical 311 Demand Data. Implement historical filter context and query endpoints, persistence for HistoricalDemandAnalysisRequest/Result/SummaryPoint/AnalysisOutcomeRecord per data-model.md. historical_context_service must resolve approved cleaned dataset from UC-02 lineage and expose only geography levels that are reliable in stored data. historical_warning_service handles high-volume warnings with proceed/decline semantics. Terminal outcomes: no_data, retrieval_failed, render_failed; preserve filter context. Extend frontend with HistoricalDemandPage and feature folder historical-demand. Note: an existing HistoricalDemandService in app/services/historical_demand_service.py serves forecast visualization; either extend carefully without breaking UC-05 or introduce clearly named UC-07 services/modules to avoid conflating responsibilities—choose the approach that keeps UC-05 tests green.

Deliverables: Full implementation per tasks.md phases, with migrations, API, services, repositories, frontend UI, and tests. End with a short summary of what changed and how to run tests.
EOF
  ;;
08)
  run_codex_uc <<'EOF'
You are implementing UC-08 in the 311-forecast-system monorepo. Work only inside the real tree; do not create backend/src or a top-level tests directory.

Git workflow (mandatory — do this first, before any file edits or commits):
- Create and switch to a new git branch named exactly `008-compare-demand-forecasts` (the spec feature branch). From your current HEAD run `git checkout -b 008-compare-demand-forecasts`. If that branch already exists locally, run `git checkout 008-compare-demand-forecasts` instead. Do all implementation work only on that branch; do not commit on main (or whatever you started from) for this work.

PATH REMAPPING (mandatory):
- All backend application code lives under backend/app/ (import package app). New modules go next to existing routes, services, repositories, schemas, models, pipelines, clients, core.
- Alembic migrations live under backend/migrations/versions/. Follow existing revision naming and upgrade pattern from backend/migrations/env.py and backend/app/core/db.py.
- Backend tests live under backend/tests/contract, backend/tests/integration, backend/tests/unit with pytest markers as in backend/pyproject.toml.
- Frontend: Vite + React under frontend/src/; colocate Vitest tests like existing pages. Wire new pages in frontend/src/App.tsx and match Tailwind/UI patterns.

Authoritative requirements:
- docs/UC-08.md and docs/UC-08-AT.md.
- specs/008-compare-demand-forecasts/spec.md, plan.md, data-model.md, research.md, quickstart.md.
- specs/008-compare-demand-forecasts/tasks.md — phases in order; remap every file path per PATH REMAPPING.
- OpenAPI: specs/008-compare-demand-forecasts/contracts/demand-comparison-api.yaml.

Engineering constraints:
- Match existing auth, routing, DB, and logging patterns under backend/app/.
- Do not weaken security; no secrets in logs.

Local CI parity — mandatory before `git commit` and `git push` (must mirror `.github/workflows/ci.yml`; fix all failures first):
1. **Backend** (shell `cd` to `backend/`; same env as CI `backend-tests`):
   - Python **3.10** as in CI (`python-version: "3.10"`). Prefer `python3.10 -m venv .venv` then `. .venv/bin/activate` then `python -m pip install -r requirements.txt`. If you use `uv venv`, the venv may have **no pip**: use `uv pip install -r requirements.txt --python .venv/bin/python` instead—**never** run bare `pip install` if it might target another Python (e.g. user site-packages on 3.9).
   - `export DATABASE_URL=sqlite+pysqlite:///./ci-test.db`
   - Run the **full** suite: `.venv/bin/python -m pytest` (or `pytest` with venv activated). **All** tests must pass.
2. **Frontend** (shell `cd` to `frontend/`; same as CI `frontend-tests`):
   - `npm ci`
   - `npm test -- --run`
   - `npm run build` (runs `tsc --noEmit && vite build` — must succeed).
3. Repeat the above until **every** step is green. Do **not** commit or push if any step fails.

Repo-root verification (mandatory — lab-style aggregate checks):
- **Makefile alignment:** Root `make test` runs backend then frontend tests exactly as in the top-level Makefile (`cd backend && .venv/bin/pytest`, then `cd frontend && npm test`). `make coverage` is backend-only (`backend-coverage`). Ensure `make install` (or individual `make backend-venv` / `make backend-install` / `make frontend-install`) has been run so those targets succeed. Use `make frontend-build` for the Makefile’s frontend production build step (with `VITE_API_BASE_URL`).
- From the repository root: run `make test`, then `make coverage`. If either fails, or branch coverage for new/changed code misses requirements (e.g. 100% branch on new code where required), fix implementation or tests until both are green.
- Do not change behavior or structure intended for other use cases; unrelated tests must keep passing.

Git publish (mandatory when there are changes to commit):
- On branch `008-compare-demand-forecasts`, stage all intended files, commit with a clear message (e.g. `feat(uc-08): demand comparison`), then run `git push -u origin 008-compare-demand-forecasts`. If push fails (e.g. non-fast-forward), report the error and stop; do not force-push unless the user explicitly asked. If there is nothing to commit, say so and skip push.

Launch app for manual verification (mandatory **last** step — after tests and after commit/push attempt, so the user can see the implementation in a browser):
- **Backend:** from `backend/`, use a **dedicated** SQLite file for dev (avoids Alembic "table already exists" if `backend.db` is stale), e.g. `export DATABASE_URL=sqlite+pysqlite:///./.local-app.sqlite` and `export FRONTEND_ORIGIN=http://localhost:5173`. Start Uvicorn in the **background**, e.g. `nohup .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 > /tmp/codex-uc08-api.log 2>&1 &` (use the same venv you used for pytest).
- **Frontend:** from `frontend/`, after `npm ci` if needed, start Vite in the **background**, e.g. `nohup npm run dev -- --host 127.0.0.1 --port 5173 > /tmp/codex-uc08-vite.log 2>&1 &`.
- If ports **8000** or **5173** are in use, pick other ports and state them explicitly in your summary.
- In your **final summary**, always list:
  - **UI:** http://127.0.0.1:5173/ (or the port you chose)
  - **API docs:** http://127.0.0.1:8000/docs
  - **Log files** (e.g. `/tmp/codex-uc08-api.log`, `/tmp/codex-uc08-vite.log`) for troubleshooting.

Feature scope (UC-08):
Compare historical demand (UC-02 approved lineage) with forecast demand (active UC-03 or UC-04) for selected categories, optional geographies, and one continuous time range. Implement deterministic forecast source selection and one allowable comparison granularity per plan/spec. Use a single outcome vocabulary; expose render_failed only via the render-event path, not the initial comparison response. Add backend services demand_comparison_* and demand_lineage_repository as in tasks; frontend feature demand-comparisons and DemandComparisonPage. Include warning_required flow for large requests (US2) and missing combination / failure handling per spec.

Deliverables: Full implementation per tasks.md phases; green local CI parity; commit + push when applicable; app launched in background; end with summary, exact URLs, and how you ran CI-parity commands.
EOF
  ;;
09)
  run_codex_uc <<'EOF'
You are implementing UC-09 in the 311-forecast-system monorepo. Work only inside the real tree; do not create backend/src or a top-level tests directory.

Git workflow (mandatory — do this first, before any file edits or commits):
- Create and switch to a new git branch named exactly `009-add-weather-overlay` (the spec feature branch). From your current HEAD run `git checkout -b 009-add-weather-overlay`. If that branch already exists locally, run `git checkout 009-add-weather-overlay` instead. Do all implementation work only on that branch; do not commit on main (or whatever you started from) for this work.

PATH REMAPPING (mandatory):
- Backend under backend/app/ (package app). Migrations under backend/migrations/versions/. Tests under backend/tests/{contract,integration,unit}/. Frontend under frontend/src/ with colocated Vitest tests.

Authoritative requirements:
- docs/UC-09.md and docs/UC-09-AT.md.
- specs/009-add-weather-overlay/spec.md, plan.md, data-model.md, research.md, quickstart.md.
- specs/009-add-weather-overlay/tasks.md — phases in order; remap all paths (tasks may reference backend/src or ForecastExplorerPage incorrectly).
- OpenAPI: specs/009-add-weather-overlay/contracts/weather-overlay-api.yaml.

Engineering constraints:
- Match existing FastAPI, auth, DB, and logging patterns.
- Reuse app/clients/geomet_client.py where possible.

Local CI parity — mandatory before `git commit` and `git push` (mirror `.github/workflows/ci.yml`; fix all failures first):
1. **Backend** (`cd backend/`): Python **3.10**; `python3.10 -m venv .venv` → `python -m pip install -r requirements.txt`, or `uv venv .venv --python 3.10` + `uv pip install -r requirements.txt --python .venv/bin/python` (avoid bare `pip` pointing at the wrong Python). `export DATABASE_URL=sqlite+pysqlite:///./ci-test.db`. Run `.venv/bin/python -m pytest` — **all** tests must pass.
2. **Frontend** (`cd frontend/`): `npm ci`, `npm test -- --run`, `npm run build` — all must pass.
3. Do **not** commit or push until every step is green.

Repo-root verification (mandatory — lab-style aggregate checks):
- **Makefile alignment:** Root `make test` runs backend then frontend tests exactly as in the top-level Makefile (`cd backend && .venv/bin/pytest`, then `cd frontend && npm test`). `make coverage` is backend-only (`backend-coverage`). Ensure `make install` (or individual `make backend-venv` / `make backend-install` / `make frontend-install`) has been run so those targets succeed. Use `make frontend-build` for the Makefile’s frontend production build step (with `VITE_API_BASE_URL`).
- From the repository root: run `make test`, then `make coverage`. Fix failures or insufficient branch coverage on new/changed code until both are green.
- Do not change behavior intended for other use cases; unrelated tests must stay passing.

Feature scope (UC-09):
Optional weather overlay on the forecast explorer view. Map the spec's ForecastExplorerPage to the existing ForecastVisualizationPage and forecast visualization chart stack. Add weather_overlay_service, alignment rules, routes per contract (GET overlay + POST render-events). Persist operational / observability records per data-model.md. Implement non-visible states (unavailable, retrieval-failed, misaligned, failed-to-render) without breaking the base chart. Frontend: weather-overlay feature module (controls, layer, status) integrated into ForecastVisualizationPage.

Git publish (mandatory when there are changes to commit):
- On branch `009-add-weather-overlay`, stage all intended files, commit with a clear message (e.g. `feat(uc-09): weather overlay on forecast visualization`), then run `git push -u origin 009-add-weather-overlay`. If push fails (e.g. non-fast-forward), report the error and stop; do not force-push unless the user explicitly asked. If there is nothing to commit, say so and skip push.

Launch app for manual verification (mandatory **last** step):
- From `backend/`: `export DATABASE_URL=sqlite+pysqlite:///./.local-app.sqlite`, `export FRONTEND_ORIGIN=http://localhost:5173`, then background Uvicorn, e.g. `nohup .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 > /tmp/codex-uc09-api.log 2>&1 &`.
- From `frontend/`: `nohup npm run dev -- --host 127.0.0.1 --port 5173 > /tmp/codex-uc09-vite.log 2>&1 &` (after `npm ci` if needed).
- If ports are busy, use others and report them. Final summary must include **UI** URL (default http://127.0.0.1:5173/), **API docs** (http://127.0.0.1:8000/docs), and log paths.

Deliverables: Full implementation per tasks.md phases; green local CI parity; commit + push; app launched; summary with URLs and exact CI commands you ran.
EOF
  ;;
10)
  run_codex_uc <<'EOF'
You are implementing UC-10 in the 311-forecast-system monorepo. Work only inside the real tree; do not create backend/src or a top-level tests directory.

Git workflow (mandatory — do this first, before any file edits or commits):
- Create and switch to a new git branch named exactly `010-demand-threshold-alerts` (the spec feature branch). From your current HEAD run `git checkout -b 010-demand-threshold-alerts`. If that branch already exists locally, run `git checkout 010-demand-threshold-alerts` instead. Do all implementation work only on that branch; do not commit on main (or whatever you started from) for this work.

PATH REMAPPING (mandatory):
- Backend under backend/app/. Migrations under backend/migrations/versions/ (next revision after existing chain). Tests under backend/tests/. Frontend under frontend/src/.

Authoritative requirements:
- docs/UC-10.md and docs/UC-10-AT.md (if present) plus specs/010-demand-threshold-alerts/spec.md, plan.md, data-model.md, research.md, quickstart.md.
- specs/010-demand-threshold-alerts/tasks.md — full phase order; remap every backend/src or root tests path.
- OpenAPI: specs/010-demand-threshold-alerts/contracts/threshold-alerts-api.yaml.

Engineering constraints:
- Match JWT auth, route dependencies, and scheduler patterns (see app/services/*_scheduler.py, APScheduler).
- Geography-specific threshold precedence over category-only rules per spec.
- Notification client abstraction without hard-coded real third-party credentials.

Local CI parity — mandatory before `git commit` and `git push` (mirror `.github/workflows/ci.yml`; fix all failures first):
1. **Backend** (`cd backend/`): Python **3.10**; reliable venv + install (see UC-09 instructions—use `python -m pip` or `uv pip` into `.venv`). `export DATABASE_URL=sqlite+pysqlite:///./ci-test.db`. `.venv/bin/python -m pytest` — all pass.
2. **Frontend** (`cd frontend/`): `npm ci`, `npm test -- --run`, `npm run build` — all pass.
3. No commit/push until green.

Repo-root verification (mandatory — lab-style aggregate checks):
- **Makefile alignment:** Root `make test` runs backend then frontend tests exactly as in the top-level Makefile (`cd backend && .venv/bin/pytest`, then `cd frontend && npm test`). `make coverage` is backend-only (`backend-coverage`). Ensure `make install` (or individual `make backend-venv` / `make backend-install` / `make frontend-install`) has been run so those targets succeed. Use `make frontend-build` for the Makefile’s frontend production build step (with `VITE_API_BASE_URL`).
- From the repository root: run `make test`, then `make coverage`. Fix failures or insufficient branch coverage on new/changed code until both are green.
- Do not change behavior intended for other use cases; unrelated tests must stay passing.

Feature scope (UC-10):
Threshold-based forecast alerts: configuration, evaluation runs, per-scope outcomes, threshold state, notification events, channel attempts per data-model. Frontend alert review surfaces per tasks.

Git publish (mandatory when there are changes to commit):
- On branch `010-demand-threshold-alerts`, stage all intended files, commit with a clear message (e.g. `feat(uc-10): demand threshold alerts`), then run `git push -u origin 010-demand-threshold-alerts`. If push fails (e.g. non-fast-forward), report the error and stop; do not force-push unless the user explicitly asked. If there is nothing to commit, say so and skip push.

Launch app for manual verification (mandatory **last** step):
- Backend: `DATABASE_URL=sqlite+pysqlite:///./.local-app.sqlite`, `FRONTEND_ORIGIN=http://localhost:5173`, `nohup .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 > /tmp/codex-uc10-api.log 2>&1 &`.
- Frontend: `nohup npm run dev -- --host 127.0.0.1 --port 5173 > /tmp/codex-uc10-vite.log 2>&1 &`.
- Final summary: UI URL, `/docs` URL, log paths; alternate ports if needed.

Deliverables: Full implementation per tasks.md phases; green local CI parity; commit + push; app launched; summary with URLs and CI commands.
EOF
  ;;
11)
  run_codex_uc <<'EOF'
You are implementing UC-11 in the 311-forecast-system monorepo. Work only inside the real tree; do not create backend/src or a top-level tests directory.

Git workflow (mandatory — do this first, before any file edits or commits):
- Create and switch to a new git branch named exactly `011-abnormal-demand-surge-notifications` (the spec feature branch). From your current HEAD run `git checkout -b 011-abnormal-demand-surge-notifications`. If that branch already exists locally, run `git checkout 011-abnormal-demand-surge-notifications` instead. Do all implementation work only on that branch; do not commit on main (or whatever you started from) for this work.

PATH REMAPPING (mandatory):
- Backend under backend/app/. Migrations under backend/migrations/versions/. Tests under backend/tests/. Frontend under frontend/src/.

Authoritative requirements:
- Governing UC docs under docs/ plus specs/011-abnormal-demand-surge-notifications/spec.md, plan.md, data-model.md, research.md, quickstart.md.
- specs/011-abnormal-demand-surge-notifications/tasks.md — phases in order; remap paths.
- OpenAPI: specs/011-abnormal-demand-surge-notifications/contracts/surge-alerts-api.yaml.

Engineering constraints:
- Match existing ingestion and forecast lineage patterns where the spec requires hooks after UC-01 runs.
- Dual-threshold confirmation, surge state, filtered/suppressed outcomes, notification persistence.

Local CI parity — mandatory before `git commit` and `git push` (mirror `.github/workflows/ci.yml`; fix all failures first):
1. **Backend** (`cd backend/`): Python **3.10**, venv + deps as for UC-09/10, `export DATABASE_URL=sqlite+pysqlite:///./ci-test.db`, `.venv/bin/python -m pytest` — all pass.
2. **Frontend** (`cd frontend/`): `npm ci`, `npm test -- --run`, `npm run build` — all pass.
3. No commit/push until green.

Repo-root verification (mandatory — lab-style aggregate checks):
- **Makefile alignment:** Root `make test` runs backend then frontend tests exactly as in the top-level Makefile (`cd backend && .venv/bin/pytest`, then `cd frontend && npm test`). `make coverage` is backend-only (`backend-coverage`). Ensure `make install` (or individual `make backend-venv` / `make backend-install` / `make frontend-install`) has been run so those targets succeed. Use `make frontend-build` for the Makefile’s frontend production build step (with `VITE_API_BASE_URL`).
- From the repository root: run `make test`, then `make coverage`. Fix failures or insufficient branch coverage on new/changed code until both are green.
- Do not change behavior intended for other use cases; unrelated tests must stay passing.

Feature scope (UC-11):
Surge detection using residual vs active forecast (daily/weekly), z-score and percent-above-forecast confirmation, surge state machine, notification events and channel attempts. Manual replay API per contract. Frontend surge review UI per tasks.

Git publish (mandatory when there are changes to commit):
- On branch `011-abnormal-demand-surge-notifications`, stage all intended files, commit with a clear message (e.g. `feat(uc-11): abnormal demand surge notifications`), then run `git push -u origin 011-abnormal-demand-surge-notifications`. If push fails (e.g. non-fast-forward), report the error and stop; do not force-push unless the user explicitly asked. If there is nothing to commit, say so and skip push.

Launch app for manual verification (mandatory **last** step):
- Backend: `DATABASE_URL=sqlite+pysqlite:///./.local-app.sqlite`, `FRONTEND_ORIGIN=http://localhost:5173`, `nohup .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 > /tmp/codex-uc11-api.log 2>&1 &`.
- Frontend: `nohup npm run dev -- --host 127.0.0.1 --port 5173 > /tmp/codex-uc11-vite.log 2>&1 &`.
- Final summary: UI URL, `/docs` URL, log paths; alternate ports if needed.

Deliverables: Full implementation per tasks.md phases; green local CI parity; commit + push; app launched; summary with URLs and CI commands.
EOF
  ;;
12)
  run_codex_uc <<'EOF'
You are implementing UC-12 in the 311-forecast-system monorepo. Work only inside the real tree; do not create backend/src or a top-level tests directory.

Git workflow (mandatory — do this first, before any file edits or commits):
- Create and switch to a new git branch named exactly `012-uc-12-drill-alert-details` (the spec feature branch). From your current HEAD run `git checkout -b 012-uc-12-drill-alert-details`. If that branch already exists locally, run `git checkout 012-uc-12-drill-alert-details` instead. Do all implementation work only on that branch; do not commit on main (or whatever you started from) for this work.

PATH REMAPPING (mandatory):
- Backend under backend/app/. Migrations under backend/migrations/versions/. Tests under backend/tests/. Frontend under frontend/src/.

Authoritative requirements:
- Governing UC docs under docs/ plus specs/012-uc-12-drill-alert-details/spec.md, plan.md, data-model.md, research.md, quickstart.md.
- specs/012-uc-12-drill-alert-details/tasks.md — phases in order; remap all backend/src and root tests paths.
- OpenAPI: specs/012-uc-12-drill-alert-details/contracts/alert-detail-context-api.yaml.

Engineering constraints:
- alert_source_resolution_service must resolve threshold_alert and surge_alert against UC-10 and UC-11 persistence. If those features are not in the branch yet, use minimal stubs only where unavoidable and document TODOs—prefer implementing when alerts exist.

Local CI parity — mandatory before `git commit` and `git push` (mirror `.github/workflows/ci.yml`; fix all failures first):
1. **Backend** (`cd backend/`): Python **3.10**, venv + deps as for UC-09, `export DATABASE_URL=sqlite+pysqlite:///./ci-test.db`, `.venv/bin/python -m pytest` — all pass.
2. **Frontend** (`cd frontend/`): `npm ci`, `npm test -- --run`, `npm run build` — all pass.
3. No commit/push until green.

Repo-root verification (mandatory — lab-style aggregate checks):
- **Makefile alignment:** Root `make test` runs backend then frontend tests exactly as in the top-level Makefile (`cd backend && .venv/bin/pytest`, then `cd frontend && npm test`). `make coverage` is backend-only (`backend-coverage`). Ensure `make install` (or individual `make backend-venv` / `make backend-install` / `make frontend-install`) has been run so those targets succeed. Use `make frontend-build` for the Makefile’s frontend production build step (with `VITE_API_BASE_URL`).
- From the repository root: run `make test`, then `make coverage`. Fix failures or insufficient branch coverage on new/changed code until both are green.
- Do not change behavior intended for other use cases; unrelated tests must stay passing.

Feature scope (UC-12):
Authenticated drill-down: forecast distribution, top-5 drivers, 7-day anomaly context; partial and error states; render-event reporting; correlated observability per data-model.

Git publish (mandatory when there are changes to commit):
- On branch `012-uc-12-drill-alert-details`, stage all intended files, commit with a clear message (e.g. `feat(uc-12): drill alert details and context`), then run `git push -u origin 012-uc-12-drill-alert-details`. If push fails (e.g. non-fast-forward), report the error and stop; do not force-push unless the user explicitly asked. If there is nothing to commit, say so and skip push.

Launch app for manual verification (mandatory **last** step):
- Backend: `DATABASE_URL=sqlite+pysqlite:///./.local-app.sqlite`, `FRONTEND_ORIGIN=http://localhost:5173`, `nohup .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 > /tmp/codex-uc12-api.log 2>&1 &`.
- Frontend: `nohup npm run dev -- --host 127.0.0.1 --port 5173 > /tmp/codex-uc12-vite.log 2>&1 &`.
- Final summary: UI URL, `/docs` URL, log paths; alternate ports if needed.

Deliverables: Full implementation per tasks.md phases; green local CI parity; commit + push; app launched; summary with URLs and CI commands.
EOF
  ;;
esac

echo "Codex finished. Last message: $OUT" >&2
