@echo off
title IMetric - Website Launcher
color 0A

echo ===================================================
echo     Starting IMetric Website...
echo ===================================================
echo.

:: Check virtual environment
if not exist ".venv\Scripts\python.exe" (
    echo Virtual environment not found. Setting up...
    python -m venv .venv
    .venv\Scripts\pip install -r backend\requirements.txt
)

:: Set PYTHONPATH to backend
set PYTHONPATH=backend

:: Build frontend if dist doesn't exist
if not exist "frontend\dist\index.html" (
    echo Building frontend application...
    cd frontend && npm run build && cd ..
)

echo Starting IMetric Server on http://localhost:8000...
start /b .venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > nul 2>&1

:: Wait 2 seconds for server startup
timeout /t 2 /nobreak > nul

echo Opening browser...
start http://localhost:8000

echo.
echo ===================================================
echo   IMetric is running at http://localhost:8000
echo   To stop the server, run stop_app.bat
echo ===================================================
echo.
pause
