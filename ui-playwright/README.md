# UI Playwright smoke (local)

This folder is **separate** from the main app packages: it does not ship with `frontend`’s Vitest suite or `make test`. Use it to capture full-page screenshots while driving the real app.

## One-command run (recommended)

From the **repository root**, with backend venv and frontend deps installed (`make install` or equivalent):

```bash
export E2E_EMAIL='you@example.com'
export E2E_PASSWORD='your-password'
# Optional: bootstrap allowlist on first use against the E2E DB
# In scripts/env.local use quotes if the value contains | (pipe is special when sourced):
# AUTH_SIGNUP_ALLOWLIST='you@example.com:CityPlanner|OperationalManager'

./scripts/run-ui-e2e-local.sh
```

The script will, unless `E2E_SKIP_SERVERS=1`:

1. Start **Uvicorn** from `backend/.venv` on `127.0.0.1:8000` (override with `BACKEND_PORT`).
2. Start **Vite** from `frontend/` on `127.0.0.1:5173` (override with `FRONTEND_PORT` or `E2E_FRONTEND_PORT`).
3. Wait until `http://127.0.0.1:8000/openapi.json` and the UI root respond.
4. Run `npm ci`, install Chromium, `npm run test:with-eval` in `ui-playwright/`.
5. Stop API and Vite and print log paths under `$TMPDIR` (or `/tmp`).

Use **`E2E_SKIP_SERVERS=1`** when you already have API + Vite running (e.g. `make backend-run` and `make frontend-dev`); align `E2E_BASE_URL` and `VITE_API_BASE_URL` / ports with your setup.

### Database for automated API

| Variable | Default | Notes |
|----------|---------|--------|
| `E2E_DATABASE_URL` | `sqlite+pysqlite:///./.e2e-app.sqlite` (relative to `backend/` cwd) | Dedicated file so dev DBs are untouched. |
| — | — | For Postgres: `make db-up`, set `E2E_DATABASE_URL` to your URL (same as `make backend-run`). |

## Prerequisites

- `backend/.venv` with Uvicorn (`make backend-venv backend-install`).
- `frontend/node_modules` (the script runs `npm install` in `frontend/` if `vite` is missing).
- A **registered** user for the chosen `DATABASE_URL` (seed via `AUTH_SIGNUP_ALLOWLIST` on first API boot, or existing data). The smoke test expects **Evaluations** and **Ingestion** in the nav (e.g. `CityPlanner` or `OperationalManager`).

## Environment

| Variable | Required | Description |
|----------|----------|-------------|
| `E2E_EMAIL` | Yes | Login email |
| `E2E_PASSWORD` | Yes | Login password |
| `E2E_SKIP_SERVERS` | No | `1` — do not start/stop API/Vite |
| `E2E_BASE_URL` | No | UI origin (default `http://127.0.0.1:5173` or matches `FRONTEND_PORT`) |
| `BACKEND_PORT` | No | API port (default `8000`) |
| `FRONTEND_PORT` / `E2E_FRONTEND_PORT` | No | Vite port (default `5173`) |
| `API_BASE_URL` | No | Passed to Vite as `VITE_API_BASE_URL` when script starts Vite (default `http://127.0.0.1:$BACKEND_PORT`) |
| `E2E_DATABASE_URL` | No | Backend `DATABASE_URL` when script starts API |
| `AUTH_SIGNUP_ALLOWLIST` | No | Passed through when starting API (e.g. `email:CityPlanner`) |
| `E2E_TRIGGER_INGESTION` | No | `1` — click “Trigger 311 ingestion” (slow; needs `OperationalManager`) |
| `E2E_MIN_SCREENSHOT_BYTES` | No | Minimum bytes per expected PNG for `npm run evaluate` (default `4096`) |

## Manual Playwright only

If servers are already up:

```bash
export E2E_SKIP_SERVERS=1
export E2E_BASE_URL='http://127.0.0.1:5173'
./scripts/run-ui-e2e-local.sh
```

Or:

```bash
cd ui-playwright
npm ci
npx playwright install chromium
E2E_EMAIL=you@example.com E2E_PASSWORD='...' npm test
npm run evaluate
```

## What the test does

1. Entry page → `01-entry.png`.
2. Sign in → Forecasts → `02-forecasts-initial.png`.
3. Forecast **time range** → **Next 7 days** → `03-forecasts-weekly-window.png`.
4. **Comparisons** → `10-demand-comparisons.png`.
5. **Historical** → `04-historical-initial.png`.
6. Edit historical date range → `05-historical-dates-changed.png`.
7. **Explore historical demand** → `06-historical-after-submit.png`.
8. **Evaluations** → `11-evaluations.png`.
9. **Ingestion** → `07-ingestion-page.png`.
10. **Forecasts** again → `09-back-to-forecasts.png`.

Optional `E2E_TRIGGER_INGESTION=1` adds `08-ingestion-trigger-clicked` or `08-ingestion-trigger-disabled`.

Screenshots: `ui-playwright/test-results/ui-smoke/*.png`.

## Evaluate step

`npm run evaluate` checks that expected PNGs exist and are at least `E2E_MIN_SCREENSHOT_BYTES` (heuristic against empty/blank captures). It writes `test-results/ui-smoke/evaluation-report.json` with `"ok": true` when every expected step passed. **Codex UC prompts require this to pass before commit/push** (see `docs/CODEX_PROMPTS_SUMMARY.md`).

## CI

Not wired into the default GitHub workflow by design; run locally when validating UC work in a browser.
