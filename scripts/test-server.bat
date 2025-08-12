@echo off
cd /d "%~dp0"
echo Starting local test server...
echo.
echo Your site will open at: http://localhost:8000
echo Press Ctrl+C to stop the server
echo.
start "" http://localhost:8000
python -m http.server 8000
pause