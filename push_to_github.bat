@echo off
title Push LAND-SAFE AI to GitHub
echo =====================================================================
echo  LAND-SAFE AI: Pushing repository to GitHub
echo  Target: https://github.com/sharajkumaran22/SIH26001.git
echo =====================================================================
cd /d "%~dp0"

echo.
echo Current Git Status:
git status -s

echo.
echo Executing: git push -u origin main
echo (If a browser window or sign-in prompt appears, please authorize GitHub)
echo.
git push -u origin main

echo.
if %ERRORLEVEL% EQU 0 (
    echo =====================================================================
    echo  SUCCESS: All files pushed successfully to GitHub!
    echo =====================================================================
) else (
    echo =====================================================================
    echo  Push failed or cancelled. Please check your GitHub credentials.
    echo =====================================================================
)
pause
