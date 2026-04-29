#!/usr/bin/env bash
# Arajim — convenience launcher. Starts backend + frontend in parallel.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [ ! -f .env ]; then
  echo "[arajim] no .env found — copying .env.example -> .env"
  cp .env.example .env
fi

# shellcheck disable=SC1091
set -a; source .env; set +a

# --- backend ---
(
  cd backend
  if [ ! -d .venv ]; then
    python3 -m venv .venv
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install -r requirements.txt
  fi
  echo "[arajim:backend] starting on :${PORT:-8000}"
  exec .venv/bin/uvicorn main:app --host "${HOST:-0.0.0.0}" --port "${PORT:-8000}" --reload
) &
BACKEND_PID=$!

# --- frontend ---
(
  cd frontend
  if [ ! -d node_modules ]; then npm install; fi
  echo "[arajim:frontend] starting on :5173"
  exec npm run dev
) &
FRONTEND_PID=$!

trap 'kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true' INT TERM EXIT
wait
