#!/usr/bin/env bash
# One-time (or repeat-safe): create scripts/env.local from the example template.
# Both codex-uc-exec.sh and run-ui-e2e-local.sh source env.local automatically when it exists.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXAMPLE="$DIR/env.local.example"
TARGET="$DIR/env.local"
if [[ ! -f "$TARGET" ]]; then
  cp "$EXAMPLE" "$TARGET"
  echo "Created $TARGET — set E2E_EMAIL and E2E_PASSWORD, then run Codex or make ui-e2e-local."
else
  echo "$TARGET already exists; not overwriting."
fi
