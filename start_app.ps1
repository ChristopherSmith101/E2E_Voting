# start_app.ps1 - V3 (The "No Ghost Processes" Edition)
$ErrorActionPreference = "Stop"

Write-Host "`n--- E2E Voting Prototype: Automated Setup ---" -ForegroundColor Cyan

# 1. Kill any existing Python processes that might be locking the DB
Write-Host "[1/5] Checking for lingering app processes..." -ForegroundColor Yellow
$currentVenvPath = "$PSScriptRoot\venv"
Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "$currentVenvPath*" } | Stop-Process -Force
Start-Sleep -Seconds 1 # Give Windows a moment to release the file lock

# 2. Virtual Environment Check
if (-not (Test-Path "$PSScriptRoot\venv")) {
    Write-Host "[2/5] Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
} else {
    Write-Host "[2/5] Virtual environment found." -ForegroundColor Gray
}

$pythonExe = "$PSScriptRoot\venv\Scripts\python.exe"
$pipExe = "$PSScriptRoot\venv\Scripts\pip.exe"

# 3. Install Dependencies
Write-Host "[3/5] Syncing dependencies..." -ForegroundColor Yellow
& $pythonExe -m pip install --upgrade pip | Out-Null
& $pipExe install -r requirements.txt

# 4. Database Cleanup
$dbPath = "$PSScriptRoot\web\instance\app.db"
if (Test-Path $dbPath) {
    Write-Host "[4/5] Clearing old database..." -ForegroundColor Yellow
    try {
        Remove-Item $dbPath -Force -ErrorAction Stop
    } catch {
        Write-Warning "Could not delete $dbPath. If the app fails, close any open DB browsers or other terminals."
    }
} else {
    Write-Host "[4/5] Database environment is clean." -ForegroundColor Gray
}

# 5. Start Application
Write-Host "[5/5] Starting Flask Server..." -ForegroundColor Green
Write-Host "URL: http://127.0.0.1:5000" -ForegroundColor Cyan
& $pythonExe -m web.app
