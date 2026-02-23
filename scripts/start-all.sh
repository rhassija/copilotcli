#!/usr/bin/env bash
set -euo pipefail

BACKEND_HOST="${BACKEND_HOST:-0.0.0.0}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"

shutdown() {
  echo "Shutting down services..."
  if [[ -n "${BACKEND_PID:-}" ]]; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi
  if [[ -n "${FRONTEND_PID:-}" ]]; then
    kill "$FRONTEND_PID" 2>/dev/null || true
  fi
  wait || true
}

trap shutdown SIGINT SIGTERM

echo "Starting backend on ${BACKEND_HOST}:${BACKEND_PORT}..."
cd /app/backend
python -m uvicorn src.main:app --host "$BACKEND_HOST" --port "$BACKEND_PORT" &
BACKEND_PID=$!

echo "Starting frontend on 0.0.0.0:${FRONTEND_PORT}..."
cd /app/frontend
npm run dev -- --hostname 0.0.0.0 --port "$FRONTEND_PORT" &
FRONTEND_PID=$!

wait -n "$BACKEND_PID" "$FRONTEND_PID"
shutdown
