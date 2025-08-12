#!/usr/bin/env bash
cd "$(dirname "$0")"
echo "Starting local test server at http://localhost:8000"
python3 -m http.server 8000 &
SERVER_PID=$!
sleep 1
if command -v open &> /dev/null; then
    open "http://localhost:8000"
elif command -v xdg-open &> /dev/null; then
    xdg-open "http://localhost:8000"
fi
echo "Press Ctrl+C to stop the server"
trap "kill $SERVER_PID 2>/dev/null" EXIT
wait $SERVER_PID