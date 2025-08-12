#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
PID_FILE=".server.pid"
PORT="${PORT:-8000}"

case "${1:-start}" in
  start)
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
      echo "Already running (PID $(cat "$PID_FILE")) at http://localhost:$PORT"; exit 0
    fi
    (python3 -m http.server "$PORT" || python -m http.server "$PORT") >/dev/null 2>&1 &
    echo $! > "$PID_FILE"
    echo "Started http://localhost:$PORT  (PID $(cat "$PID_FILE"))"
    echo "Open: http://localhost:$PORT/?site=lancaster-12"
    ;;
  stop)
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
      kill "$(cat "$PID_FILE")"
      echo "Stopped (PID $(cat "$PID_FILE"))"
    else
      echo "Not running"
    fi
    rm -f "$PID_FILE"
    ;;
  status)
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
      echo "Running (PID $(cat "$PID_FILE")) at http://localhost:$PORT"
    else
      echo "Not running"
    fi
    ;;
esac