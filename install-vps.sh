#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-$HOME/ai-electro-layout-starter}"
PY=python3

echo "[1/7] Install system deps"
sudo apt update
sudo apt install -y $PY-venv nginx curl

echo "[2/7] Backend venv & deps"
cd "$APP_DIR/backend"
$PY -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "[3/7] Create systemd service"
SERVICE_PATH="/etc/systemd/system/ai-electro.service"
sudo bash -c "cat > $SERVICE_PATH" <<'EOF'
[Unit]
Description=AI Electro Layout Backend
After=network.target

[Service]
User=%i
WorkingDirectory=%h/ai-electro-layout-starter/backend
Environment=PYTHONUNBUFFERED=1
ExecStart=%h/ai-electro-layout-starter/backend/.venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable ai-electro.service
sudo systemctl restart ai-electro.service
sleep 2
sudo systemctl --no-pager --full status ai-electro.service || true

echo "[4/7] Nginx site config"
sudo mkdir -p /var/www/ai-electro-layout-starter/frontend
sudo bash -c "cat > /etc/nginx/sites-available/ai-electro" <<'EOF'
server {
    listen 80;
    server_name _;
    client_max_body_size 50M;

    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        root /var/www/ai-electro-layout-starter/frontend/dist;
        try_files $uri /index.html;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/ai-electro /etc/nginx/sites-enabled/ai-electro
sudo nginx -t
sudo systemctl reload nginx

echo "[5/7] Build frontend"
cd "$APP_DIR/frontend"
npm i
npm run build
sudo cp -r dist /var/www/ai-electro-layout-starter/frontend/

echo "[6/7] Check API"
curl -sSf http://127.0.0.1:8000/openapi.json >/dev/null && echo "API OK" || echo "API check failed"

echo "[7/7] Done. Open http://<server_ip>/"
