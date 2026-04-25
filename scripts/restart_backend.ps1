# HCDP Fast Backend Restarter (Windows)
# ------------------------------------
# This script kills any process running on port 8000 and restarts the AI server.

$port = 8000
$pid_obj = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -First 1

if ($pid_obj) {
    Write-Host "[*] Stopping existing backend (PID: $pid_obj)..." -ForegroundColor Yellow
    Stop-Process -Id $pid_obj -Force
}

Write-Host "[*] Starting HCDP AI Backend..." -ForegroundColor Cyan
Set-Location "$PSScriptRoot\.."

$VENV_PYTHON = ".\.venv\Scripts\python.exe"
if (Test-Path $VENV_PYTHON) {
    Write-Host "[*] Using virtual environment: .venv" -ForegroundColor Green
    & $VENV_PYTHON gemini_chat/server.py
} else {
    Write-Host "[!] .venv not found. Falling back to system python..." -ForegroundColor Gray
    python gemini_chat/server.py
}
