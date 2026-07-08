#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/rag-pdf-chatbot}"
APP_USER="${APP_USER:-${SUDO_USER:-$USER}}"
APP_GROUP="${APP_GROUP:-$APP_USER}"
SERVICE_NAME="${SERVICE_NAME:-rag-pdf-chatbot}"
HF_HOME="${HF_HOME:-$APP_DIR/.hf-cache}"

sudo tee "/etc/systemd/system/${SERVICE_NAME}.service" >/dev/null <<EOF
[Unit]
Description=RAG PDF Chatbot Streamlit App
After=network-online.target ollama.service
Wants=network-online.target

[Service]
Type=simple
User=${APP_USER}
Group=${APP_GROUP}
WorkingDirectory=${APP_DIR}
Environment=HOME=/home/${APP_USER}
Environment=HF_HOME=${HF_HOME}
ExecStart=${APP_DIR}/venv/bin/streamlit run app.py --server.address 0.0.0.0 --server.port 8501 --server.headless true
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable "${SERVICE_NAME}"
sudo systemctl restart "${SERVICE_NAME}"

echo "Installed service ${SERVICE_NAME}."
