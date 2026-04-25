#!/bin/bash
# HCDP Fast Backend Restarter (Linux/WSL)
# ---------------------------------------
# This script kills any process running on port 8000 and restarts the AI server.

PORT=8000
PID=$(lsof -t -i:$PORT)

if [ -n "$PID" ]; then
    echo "[*] Stopping existing backend (PID: $PID)..."
    kill -9 $PID
fi

echo "[*] Starting HCDP AI Backend..."
cd "$(dirname "$0")/.."

VENV_PATH="./.venv_linux/bin/python"
if [ -f "$VENV_PATH" ]; then
    echo "[*] Using virtual environment: .venv_linux"
    "$VENV_PATH" gemini_chat/server.py
else
    echo "[!] .venv_linux not found. Falling back to system python3..."
    python3 gemini_chat/server.py
fi
