#!/usr/bin/env bash
# Full local UI smoke: start API + Vite (unless skipped), then Playwright + screenshot evaluation.
#
# Required: E2E_EMAIL, E2E_PASSWORD (registered user for that DATABASE_URL).
#
# Env (optional):
#   E2E_SKIP_SERVERS=1     — do not start/stop processes; assume API + Vite already running.
#   E2E_DATABASE_URL      — backend DB (default: sqlite+pysqlite:///./.e2e-app.sqlite under backend/)
#   BACKEND_PORT          — default 8000
#   FRONTEND_PORT / E2E_FRONTEND_PORT — Vite port; default 5173
#   E2E_BASE_URL          — Playwright base URL; default http://127.0.0.1:<frontend port>
#   AUTH_SIGNUP_ALLOWLIST — passed to API on boot (e.g. user:CityPlanner) so first login can succeed
#   SCHEDULER_ENABLED     — default false for this script
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ -f "$ROOT/scripts/env.local" ]]; then
  set -a
  # shellcheck source=/dev/null
  source "$ROOT/scripts/env.local"
  set +a
fi
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${E2E_FRONTEND_PORT:-${FRONTEND_PORT:-5173}}"
API_BASE_URL="${API_BASE_URL:-http://127.0.0.1:${BACKEND_PORT}}"
export E2E_BASE_URL="${E2E_BASE_URL:-http://127.0.0.1:${FRONTEND_PORT}}"

LOG_DIR="${TMPDIR:-/tmp}"
LOG_API="${LOG_DIR}/311-e2e-api-$$.log"
LOG_VITE="${LOG_DIR}/311-e2e-vite-$$.log"

if [[ -z "${E2E_EMAIL:-}" || -z "${E2E_PASSWORD:-}" ]]; then
  echo "Set E2E_EMAIL and E2E_PASSWORD (registered user for the database you use)." >&2
  exit 1
fi

wait_for_http() {
  local url=$1
  local max_seconds=${2:-180}
  local waited=0
  while (( waited < max_seconds )); do
    if curl -fsS --max-time 15 "$url" -o /dev/null; then
      return 0
    fi
    sleep 1
    waited=$((waited + 1))
  done
  echo "Timed out waiting for $url (${max_seconds}s)." >&2
  return 1
}

API_PID=""
VITE_PID=""

cleanup() {
  if [[ -n "${VITE_PID}" ]]; then
    kill "${VITE_PID}" 2>/dev/null || true
    wait "${VITE_PID}" 2>/dev/null || true
  fi
  if [[ -n "${API_PID}" ]]; then
    kill "${API_PID}" 2>/dev/null || true
    wait "${API_PID}" 2>/dev/null || true
  fi
}

if [[ "${E2E_SKIP_SERVERS:-}" != "1" ]]; then
  trap cleanup EXIT INT TERM

  if [[ ! -x "${ROOT}/backend/.venv/bin/uvicorn" ]]; then
    echo "Missing ${ROOT}/backend/.venv/bin/uvicorn — run: make backend-venv backend-install" >&2
    exit 1
  fi

  if [[ ! -x "${ROOT}/frontend/node_modules/.bin/vite" ]]; then
    echo "Installing frontend deps (vite missing)…" >&2
    (cd "${ROOT}/frontend" && npm install)
  fi

  E2E_DATABASE_URL="${E2E_DATABASE_URL:-sqlite+pysqlite:///./.e2e-app.sqlite}"
  export FRONTEND_ORIGIN="${FRONTEND_ORIGIN:-http://127.0.0.1:${FRONTEND_PORT}}"
  export SCHEDULER_ENABLED="${SCHEDULER_ENABLED:-false}"
  export AUTH_COOKIE_SECURE="${AUTH_COOKIE_SECURE:-false}"

  if [[ -z "${AUTH_SIGNUP_ALLOWLIST:-}" ]]; then
    echo "Note: AUTH_SIGNUP_ALLOWLIST is unset — ensure ${E2E_EMAIL} already exists in this DB, or set allowlist for bootstrap." >&2
  fi

  echo "Starting API on ${API_BASE_URL} (log: ${LOG_API})…" >&2
  (
    cd "${ROOT}/backend"
    export DATABASE_URL="${E2E_DATABASE_URL}"
    export FRONTEND_ORIGIN SCHEDULER_ENABLED AUTH_COOKIE_SECURE
    [[ -n "${AUTH_SIGNUP_ALLOWLIST:-}" ]] && export AUTH_SIGNUP_ALLOWLIST
    exec .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port "${BACKEND_PORT}"
  ) >"${LOG_API}" 2>&1 &
  API_PID=$!

  echo "Starting Vite on ${E2E_BASE_URL} (log: ${LOG_VITE})…" >&2
  (
    cd "${ROOT}/frontend"
    export VITE_API_BASE_URL="${API_BASE_URL}"
    exec ./node_modules/.bin/vite --host 127.0.0.1 --port "${FRONTEND_PORT}"
  ) >"${LOG_VITE}" 2>&1 &
  VITE_PID=$!

  wait_for_http "${API_BASE_URL}/openapi.json" 180 || {
    echo "API failed to become ready. Tail ${LOG_API}:" >&2
    tail -n 40 "${LOG_API}" >&2 || true
    exit 1
  }
  wait_for_http "${E2E_BASE_URL}/" 180 || {
    echo "Vite failed to become ready. Tail ${LOG_VITE}:" >&2
    tail -n 40 "${LOG_VITE}" >&2 || true
    exit 1
  }
  echo "API and Vite are up." >&2
else
  echo "E2E_SKIP_SERVERS=1 — using already-running servers (${E2E_BASE_URL})." >&2
fi

cd "${ROOT}/ui-playwright"
npm ci
npx playwright install chromium
npm run test:with-eval

if [[ "${E2E_SKIP_SERVERS:-}" != "1" ]]; then
  trap - EXIT INT TERM
  cleanup
  echo "Stopped temporary API and Vite. Logs: ${LOG_API} ${LOG_VITE}" >&2
fi
