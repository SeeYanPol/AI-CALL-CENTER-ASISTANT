# CallSim Backend Starter Script
# Starts the Flask backend server for CallSim

Write-Host "================================" -ForegroundColor Cyan
Write-Host "   CallSim Backend Starter" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
Write-Host "Checking Python installation..." -ForegroundColor Yellow
$pythonCheck = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "Found: $pythonCheck" -ForegroundColor Green
} else {
    Write-Host "Python not found! Please install Python 3.10+" -ForegroundColor Red
    exit 1
}

# Check if .env file exists
Write-Host ""
Write-Host "Checking configuration..." -ForegroundColor Yellow
if (Test-Path "backend\.env") {
    Write-Host ".env file found" -ForegroundColor Green
} else {
    Write-Host ".env file not found (using defaults)" -ForegroundColor Yellow
}

# Check if database exists
if (Test-Path "backend\callsim.db") {
    Write-Host "Database found" -ForegroundColor Green
} else {
    Write-Host "Database not found - will be created automatically" -ForegroundColor Yellow
}

# Stop any running Flask processes
Write-Host ""
Write-Host "Stopping existing Python processes..." -ForegroundColor Yellow
$pythonProcesses = Get-Process -Name python -ErrorAction SilentlyContinue
if ($pythonProcesses) {
    $pythonProcesses | ForEach-Object {
        Write-Host "  Stopping process $($_.Id)..." -ForegroundColor Gray
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 1
    Write-Host "Cleaned up old processes" -ForegroundColor Green
} else {
    Write-Host "No processes to stop" -ForegroundColor Green
}

# Start the server
Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "Starting Flask Backend Server..." -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend API: http://localhost:5000" -ForegroundColor Green
Write-Host "Frontend:    http://localhost:5500" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

Set-Location backend
python app_simple.py
