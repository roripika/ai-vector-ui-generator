#!/bin/bash
set -e

cd "$(dirname "$0")"

# Pick Python (.venv preferred)
if [ -x ".venv/bin/python" ]; then
  PY=".venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PY="python3"
elif command -v python >/dev/null 2>&1; then
  PY="python"
else
  osascript -e 'display dialog "Python was not found. Create .venv or install python3." buttons {"OK"}'
  exit 1
fi

LOG="./studio_server.log"
URL="http://127.0.0.1:8000/studio.html"

# If already running, just open the URL
if command -v lsof >/dev/null 2>&1; then
  if lsof -iTCP:8000 -sTCP:LISTEN >/dev/null 2>&1; then
    open "$URL"
    exit 0
  fi
fi

# Start server
nohup "$PY" -m src.preview > "$LOG" 2>&1 &

# Wait briefly then open browser
sleep 0.7
open "$URL"

exit 0
