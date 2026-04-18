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

# --- Helper Functions ---
# Checks if a file has changed by comparing its MD5 hash with a stored value
check_hash() {
    local file=$1
    local hash_file=$2
    
    # If file doesn't exist, we can't check it
    if [ ! -f "$file" ]; then return 0; fi
    
    local current_hash=$(md5sum "$file" | awk '{ print $1 }')
    
    if [ -f "$hash_file" ]; then
        local last_hash=$(cat "$hash_file")
        if [ "$current_hash" == "$last_hash" ]; then
            return 1 # No change
        fi
    fi
    # Update hash file
    echo "$current_hash" > "$hash_file"
    return 0 # Changed or first run
}

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

# Only npm install if package.json changed or node_modules is missing
if check_hash "package.json" "$PROJECT_ROOT/.last_frontend_hash" || [ ! -d "node_modules" ]; then
    echo "[*] Changes detected or fresh install. Running npm install..."
    npm install
else
    echo "[*] No changes to package.json. Skipping npm install."
fi

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

# Create the virtual environment if it doesn't already exist
VENV_CREATED=false
if [ ! -f "$VENV_PATH/bin/activate" ]; then
    echo "[*] Virtual environment not found. Creating one at $VENV_PATH..."
    python3 -m venv "$VENV_PATH"
    VENV_CREATED=true
fi

# Always activate the venv before installing/running
source "$VENV_PATH/bin/activate"
echo "[*] Activated virtual environment: $VENV_PATH"

# Install/update Python dependencies into the venv only if requirements.txt changed
if check_hash "$PROJECT_ROOT/requirements.txt" "$PROJECT_ROOT/.last_backend_hash" || [ "$VENV_CREATED" = true ]; then
    echo "[*] Changes detected or fresh venv. Installing Python dependencies..."
    pip install -r "$PROJECT_ROOT/requirements.txt" --quiet
else
    echo "[*] No changes to requirements.txt. Skipping pip install."
fi

echo "------------------------------------------------"
echo "SUCCESS: HCDP AI is now live!"
echo "Frontend: http://localhost (via Nginx)"
echo "Backend: Port 8000 (proxied via /api/)"
echo "------------------------------------------------"
echo "[*] Displaying server logs below (Ctrl+C to stop the server):"

# Set production mode (disables uvicorn --reload, enables clean Ctrl+C shutdown)
export HCDP_ENV=production

# Use 'exec' to replace this shell with Python — signals (Ctrl+C) go directly to it
exec python "$BACKEND_SCRIPT"
