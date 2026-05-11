param(
  [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

if (!(Test-Path ".venv")) {
  python -m venv .venv
}

& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\pip.exe" install -r ".\backend\requirements.txt"

# Generate a sample asset (optional, but makes first-run easier).
& ".\.venv\Scripts\python.exe" ".\scripts\generate_sample_asset.py"

Write-Host ""
Write-Host "Starting DriveSafe Road Crack Detection System..."
Write-Host "Dashboard: http://localhost:$Port/"
Write-Host "Health:    http://localhost:$Port/api/health"
Write-Host ""

Set-Location ".\backend"
& "..\.venv\Scripts\uvicorn.exe" app.main:app --reload --host 0.0.0.0 --port $Port

