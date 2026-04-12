# 311 Forecast System Details + Setup (MUST READ)

Platform for **Edmonton 311** service-demand data: ingestion from the open data API, validation and deduplication, **LightGBM**-based daily and weekly demand forecasts, visualizations, evaluations, threshold alerts, and a React operator UI. The backend is **FastAPI** on **PostgreSQL**; the frontend is **Vite + React + TypeScript + Tailwind**.

## Repository layout

| Path | Purpose |
|------|---------|
| `backend/` | FastAPI app, SQLAlchemy models, Alembic migrations (`backend/migrations/`), pytest suite |
| `frontend/` | Vite React SPA |
| `tests/` | Additional tests outside `backend/tests/` (when present) |
| `specs/` | Feature specs, plans, tasks, and OpenAPI drafts per use case |
| `docs/` | Project documentation |
| `ui-playwright/` | Optional Playwright UI smoke runs (see `ui-playwright/README.md`) |
| `scripts/` | Helper scripts (including Codex UC runners) |

Agent-oriented conventions and technology notes: [`AGENTS.md`](AGENTS.md).

## Prerequisites

- **Python** 3.10+ (3.11 matches project guidelines; CI uses 3.10)
- **Node.js** 20+ and npm
- **Docker** (for local PostgreSQL via Compose)

For Docker, ensure that running `docker --version` works in your terminal. If you are on Windows, I highly recommend running in WSL2. To do this, install Docker Desktop from [here](https://www.docker.com/products/docker-desktop/) and then enable WSL2 integration in the app using Settings -> Resources -> WSL integration.

## Quick start (local)

From the repository root:

1. **Start PostgreSQL**

   ```bash
   make db-up
   ```

   Default DB: `forecast_system`, user `forecast_user`, password `forecast_pass`, port `5432`. If port 5432 is busy: `export POSTGRES_PORT=5433` before `make db-up`, and use the same port in `DATABASE_URL` when running the API.

2. **Backend**

   ```bash
   make backend-venv
   make backend-install
   make backend-run
   ```

   The API serves on `http://127.0.0.1:8000` by default (`BACKEND_PORT` overrides).

3. **Frontend** (separate terminal)

   ```bash
   make frontend-install
   make frontend-dev
   ```

   The dev server defaults to `http://127.0.0.1:5173`; `make frontend-dev` sets `VITE_API_BASE_URL` to match the Makefile’s `API_BASE_URL` (keep `BACKEND_PORT` consistent if you change it).

### Logging In

By default, you are always able to register the account "manager@example.com" and login with it. The password can be set to anything. If you want to allow more emails to register, modify the AUTH_SIGNUP_ALLOWLIST environment variable. You change more configurations by reading the **Configuration** section of this README. Once signed in, you should first run data ingestion on the data ingestion page. **NOTE**: This can take a while on the first run (~10 minutes), but once done the subsequent calls should be fast. **Please be patient**. You can run the backend using `make backend-run-debug` to monitor the progress of data ingestion. After it is finished, go view the forecast page to see the forecast. You can also view the other pages to compare with historical data, view evaluations/accuracy, and alerts. There is also a help page to help you navigate the app as well.

### Configuration

Copy and adapt [`backend/.env.example`](backend/.env.example). The root `Makefile` passes core variables inline for `make backend-run`; for ad hoc runs, export `DATABASE_URL`, `FRONTEND_ORIGIN`, JWT settings, and **`AUTH_SIGNUP_ALLOWLIST`** (comma-separated `email:Role` entries; roles such as `CityPlanner` and `OperationalManager`) so first-time signup works locally. **Remember:**, you can always use `manager@example.com` and `planner@example.com` if this environment variable is not manually set.

Optional: enable scheduled jobs with `make backend-run-scheduled` (sets `SCHEDULER_ENABLED=true`).

## Testing

To run tests, use `make test`. If you want to generate the coverage report, use `make coverage` or `make backend-coverage`. Also make sure to check out any other `make` targets you are interested in.

## Common Make targets

Run `make help` for the full list. Highlights:

| Target | Description |
|--------|-------------|
| `make db-up` / `make db-down` | Start/stop Postgres (`compose.yaml`) |
| `make backend-test` | Pytest in `backend/` |
| `make backend-coverage` | Pytest with branch coverage |
| `make frontend-test` | Vitest |
| `make frontend-build` | Production build |
| `make install` | Backend + frontend dependencies |
| `make test` | Backend and frontend tests |

## Continuous integration

GitHub Actions (`.github/workflows/ci.yml`) runs backend tests against **SQLite** and frontend `npm ci`, tests, and build.

## Specs and APIs

Use-case design artifacts live under `specs/<feature>/` (`spec.md`, `plan.md`, `tasks.md`, contract YAML where applicable). The running API exposes OpenAPI at `/docs` and `/openapi.json` when the server is up.
