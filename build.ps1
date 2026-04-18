# setup.ps1
$ErrorActionPreference = "Stop"

Write-Host "`n--- E2E Voting Prototype: Environment Setup ---" -ForegroundColor Cyan

# 1. Kill ghost processes locking the DB
Write-Host "[1/4] Checking for lingering app processes..." -ForegroundColor Yellow
$currentVenvPath = "$PSScriptRoot\venv"
Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "$currentVenvPath*" } | Stop-Process -Force
Start-Sleep -Seconds 1

# 2. Virtual Environment
if (-not (Test-Path "$PSScriptRoot\venv")) {
    Write-Host "[2/4] Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
} else {
    Write-Host "[2/4] Virtual environment found." -ForegroundColor Gray
}

# 3. Dependencies
Write-Host "[3/4] Installing requirements..." -ForegroundColor Yellow
& "$PSScriptRoot\venv\Scripts\python.exe" -m pip install --upgrade pip | Out-Null
& "$PSScriptRoot\venv\Scripts\pip.exe" install -r requirements.txt

# 4. Database Cleanup
$dbPath = "$PSScriptRoot\web\instance\app.db"
if (Test-Path $dbPath) {
    Write-Host "[4/4] Removing old database..." -ForegroundColor Yellow
    Remove-Item $dbPath -Force
} else {
    Write-Host "[4/4] Database is clean." -ForegroundColor Gray
}

Write-Host "`nSetup Complete! To start the app, run:" -ForegroundColor Green
Write-Host ".\venv\Scripts\python.exe -m web.app" -ForegroundColor White
