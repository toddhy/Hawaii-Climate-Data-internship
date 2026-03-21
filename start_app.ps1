# Startup Script for HCDP Project

# 1. Start Backend (FastAPI)
Write-Host "Starting Backend Server..." -ForegroundColor Cyan
$PythonExe = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $PythonExe)) {
    $PythonExe = "python" # Fallback to system python
}
$BackendProcess = Start-Process $PythonExe -ArgumentList "gemini_chat/server.py" -NoNewWindow -PassThru

# 2. Start Frontend (Vite)
Write-Host "Starting Frontend Server..." -ForegroundColor Cyan
Set-Location front_end
if (-not (Test-Path "node_modules")) {
    Write-Host "node_modules not found. Running npm install..." -ForegroundColor Yellow
    npm install
}
$FrontendProcess = Start-Process cmd -ArgumentList "/c npm run dev" -NoNewWindow -PassThru
Set-Location ..

Write-Host "Applications are running. Press Ctrl+C to stop both servers." -ForegroundColor Yellow

# Function to clean up processes
function Stop-Processes {
    Write-Host "`nStopping servers..." -ForegroundColor Red
    if ($BackendProcess -and -not $BackendProcess.HasExited) {
        taskkill /F /T /PID $BackendProcess.Id 2>$null
    }
    if ($FrontendProcess -and -not $FrontendProcess.HasExited) {
        taskkill /F /T /PID $FrontendProcess.Id 2>$null
    }
    Write-Host "Servers stopped." -ForegroundColor Green
}

# Wait for Ctrl+C
try {
    while ($true) {
        Start-Sleep -Seconds 1
        if ($BackendProcess.HasExited -or $FrontendProcess.HasExited) {
            Write-Host "One of the processes has exited." -ForegroundColor Red
            break
        }
    }
}
catch {
    # This catch block might not be triggered by Ctrl+C in all PS versions/hosts
}
finally {
    Stop-Processes
}
