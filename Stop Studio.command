#!/bin/bash
set -e

cd "$(dirname "$0")"

PORT="8000"

if ! command -v lsof >/dev/null 2>&1; then
  osascript -e 'display dialog "lsof was not found, so the server cannot be stopped." buttons {"OK"}'
  exit 1
fi

PID="$(lsof -tiTCP:${PORT} -sTCP:LISTEN || true)"
if [ -n "$PID" ]; then
  kill "$PID" || true
  sleep 0.2
  osascript -e 'display dialog "Studio server stopped." buttons {"OK"}'
  exit 0
fi

osascript -e 'display dialog "Studio server is not running." buttons {"OK"}'
exit 0
