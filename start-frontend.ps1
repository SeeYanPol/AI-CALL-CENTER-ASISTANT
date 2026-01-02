# CallSim Frontend Starter Script
# Starts a simple HTTP server for the frontend

Write-Host "================================" -ForegroundColor Cyan
Write-Host "   CallSim Frontend Starter" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
$pythonCheck = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Python not found! Please install Python 3.10+" -ForegroundColor Red
    exit 1
}

Write-Host "Starting HTTP server on port 5500..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Frontend URL: http://localhost:5500" -ForegroundColor Green
Write-Host "Start Page:   http://localhost:5500/index.html" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start Python HTTP server on port 5500
python -m http.server 5500
