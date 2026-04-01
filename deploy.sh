#!/bin/bash

# Configuration
# Automatically find the directory where this script is located
PROJECT_ROOT=$(dirname "$(readlink -f "$0")")
FRONTEND_DIR="$PROJECT_ROOT/front_end"
NGINX_CONF="$PROJECT_ROOT/nginx.conf"
NGINX_WEB_ROOT="/var/www/html"
VENV_PATH="$PROJECT_ROOT/.venv/deploy_app"
BACKEND_SCRIPT="$PROJECT_ROOT/gemini_chat/server.py"
LOG_FILE="$PROJECT_ROOT/server.log"

echo "------------------------------------------------"
echo "Starting HCDP AI Deployment Script"
echo "------------------------------------------------"

# 1. Clean up existing processes
echo "[*] Stopping existing application processes..."
fuser -k 8000/tcp 2>/dev/null
fuser -k 5173/tcp 2>/dev/null
# Optional: Stop nginx if you want a full restart 
# (but usually systemctl reload is enough)
# sudo systemctl stop nginx

# 2. Build Frontend
echo "[*] Building frontend assets..."
cd "$FRONTEND_DIR" || exit
npm install
npm run build

# 3. Deploy Frontend to Nginx
echo "[*] Deploying frontend to $NGINX_WEB_ROOT..."
sudo mkdir -p "$NGINX_WEB_ROOT"
sudo rm -rf "$NGINX_WEB_ROOT/*"
sudo cp -r "$FRONTEND_DIR/dist/"* "$NGINX_WEB_ROOT/"

# 4. Configure Nginx
echo "[*] Configuring Nginx..."
# Link the provided nginx.conf from the repository to sites-enabled
sudo cp "$NGINX_CONF" "/etc/nginx/sites-available/hcdp-app"
sudo ln -sf "/etc/nginx/sites-available/hcdp-app" "/etc/nginx/sites-enabled/hcdp-app"
# Remove default if it exists to avoid conflicts
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx and reload
sudo nginx -t && sudo systemctl reload nginx

# 5. Start Backend in Virtual Environment
echo "[*] Starting FastAPI Backend..."
cd "$PROJECT_ROOT" || exit

if [ -f "$VENV_PATH/bin/activate" ]; then
    source "$VENV_PATH/bin/activate"
    echo "[*] Activated virtual environment: $VENV_PATH"
else
    echo "[!] Warning: Virtual environment not found at $VENV_PATH. Using system python."
fi

echo "------------------------------------------------"
echo "SUCCESS: HCDP AI is now live!"
echo "Frontend: http://localhost (via Nginx)"
echo "Backend: Port 8000 (proxied via /api/)"
echo "------------------------------------------------"
echo "[*] Displaying server logs below (Ctrl+C to stop the server):"

# Run backend in foreground
python "$BACKEND_SCRIPT"
