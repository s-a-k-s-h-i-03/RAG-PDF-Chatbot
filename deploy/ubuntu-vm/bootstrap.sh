#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/rag-pdf-chatbot}"
REPO_URL="${REPO_URL:-https://github.com/s-a-k-s-h-i-03/RAG-PDF-Chatbot.git}"
APP_USER="${APP_USER:-${SUDO_USER:-$USER}}"
APP_GROUP="${APP_GROUP:-$APP_USER}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
OLLAMA_MODEL="${OLLAMA_MODEL:-tinyllama}"

echo "==> Installing base packages"
sudo apt-get update
sudo apt-get install -y git curl ca-certificates python3-venv python3-pip nginx

if ! command -v ollama >/dev/null 2>&1; then
  echo "==> Installing Ollama"
  curl -fsSL https://ollama.com/install.sh | sh
fi

echo "==> Enabling Ollama"
sudo systemctl enable ollama
sudo systemctl start ollama

echo "==> Preparing application directory"
sudo mkdir -p "$APP_DIR"
sudo chown -R "$APP_USER:$APP_GROUP" "$APP_DIR"

if [ ! -d "$APP_DIR/.git" ]; then
  echo "==> Cloning repository"
  git clone "$REPO_URL" "$APP_DIR"
else
  echo "==> Updating repository"
  git -C "$APP_DIR" pull --ff-only origin main
fi

echo "==> Creating virtual environment"
"$PYTHON_BIN" -m venv "$APP_DIR/venv"
source "$APP_DIR/venv/bin/activate"
python -m pip install --upgrade pip
pip install -r "$APP_DIR/requirements.txt"

echo "==> Warming Ollama model cache"
ollama pull "$OLLAMA_MODEL"

echo "==> Warming embedding cache"
export HF_HOME="$APP_DIR/.hf-cache"
python "$APP_DIR/scripts/preload_embeddings.py"

echo "==> Installing systemd service"
"$APP_DIR/deploy/ubuntu-vm/install_service.sh"

echo "==> Installing nginx site"
sudo cp "$APP_DIR/deploy/ubuntu-vm/nginx/rag-pdf-chatbot.conf" /etc/nginx/sites-available/rag-pdf-chatbot
sudo ln -sf /etc/nginx/sites-available/rag-pdf-chatbot /etc/nginx/sites-enabled/rag-pdf-chatbot
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

echo "==> Bootstrap complete"
echo "Streamlit service: sudo systemctl status rag-pdf-chatbot"
echo "Open: http://$(hostname -I | awk '{print $1}')"
