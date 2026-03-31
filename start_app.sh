#!/bin/bash

# Startup Script for HCDP Project (Linux/macOS)

# 1. Start Backend (FastAPI)
echo "Starting Backend Server..."
PYTHON_EXE=".venv/bin/python"
if [ ! -f "$PYTHON_EXE" ]; then
    PYTHON_EXE=$(which python3 || which python)
fi

$PYTHON_EXE gemini_chat/server.py &
BACKEND_PID=$!

# 2. Start Frontend (Vite)
echo "Starting Frontend Server..."
cd front_end
if [ ! -d "node_modules" ]; then
    echo "node_modules not found. Running npm install..."
    npm install
fi

npm run dev &
FRONTEND_PID=$!
cd ..

echo "Applications are running. Press Ctrl+C to stop both servers."

# Function to clean up processes
cleanup() {
    echo -e "\nStopping servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    wait $BACKEND_PID $FRONTEND_PID 2>/dev/null
    echo "Servers stopped."
    exit
}

# Trap Ctrl+C (SIGINT) and SIGTERM
trap cleanup SIGINT SIGTERM

# Wait for background processes
wait -n $BACKEND_PID $FRONTEND_PID

# If one process exits, cleanup the other and exit
cleanup
