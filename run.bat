@echo off
TITLE LAND-SAFE AI — Command Center Prototype Server
echo =====================================================================
echo  LAND-SAFE AI: NER Landslide Risk Monitoring ^& Early Warning System
echo  Smart India Hackathon Prototype (SIH Round 2)
echo =====================================================================
echo.

cd /d "%~dp0"

echo [1/3] Checking Python installation...
python --version
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH!
    pause
    exit /b 1
)

echo.
echo [2/3] Verifying dependencies...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo Installing required packages from backend/requirements.txt...
    pip install -r backend\requirements.txt
) else (
    echo All core dependencies are installed.
)

echo.
echo [3/3] Starting LAND-SAFE AI Unified Server on http://127.0.0.1:8000 ...
echo Press Ctrl+C at any time to shut down the server.
echo.

start "" http://127.0.0.1:8000

python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
pause
