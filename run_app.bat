@echo off
TITLE LAND-SAFE AI — Desktop Application
cd /d "%~dp0"

echo =====================================================================
echo  LAND-SAFE AI: Launching Desktop Application Window
echo =====================================================================
echo.

python desktop_app.py
if errorlevel 1 (
    echo.
    echo Application exited or encountered an error.
    pause
)
