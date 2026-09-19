# LAND-SAFE AI — PowerShell One-Click Startup Script
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host " LAND-SAFE AI: NER Landslide Risk Monitoring & Early Warning System" -ForegroundColor Green
Write-Host " Smart India Hackathon Prototype (SIH Round 2)" -ForegroundColor White
Write-Host "=====================================================================" -ForegroundColor Cyan

Set-Location -Path $PSScriptRoot

Write-Host "`n[1/3] Checking Python installation..." -ForegroundColor Yellow
python --version

Write-Host "`n[2/3] Checking dependencies..." -ForegroundColor Yellow
$fastapi = pip show fastapi 2>$null
if (-not $fastapi) {
    Write-Host "Installing dependencies from backend/requirements.txt..." -ForegroundColor Yellow
    pip install -r backend/requirements.txt
} else {
    Write-Host "Core dependencies verified." -ForegroundColor Green
}

Write-Host "`n[3/3] Launching LAND-SAFE AI on http://127.0.0.1:8000 ..." -ForegroundColor Green
Start-Process "http://127.0.0.1:8000"

python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
