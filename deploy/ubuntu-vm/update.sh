#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/rag-pdf-chatbot}"
BRANCH="${BRANCH:-main}"
SERVICE_NAME="${SERVICE_NAME:-rag-pdf-chatbot}"
OLLAMA_MODEL="${OLLAMA_MODEL:-tinyllama}"

cd "$APP_DIR"

echo "==> Fetching latest code"
git fetch origin "$BRANCH"
git checkout "$BRANCH"
git pull --ff-only origin "$BRANCH"

echo "==> Refreshing Python environment"
source "$APP_DIR/venv/bin/activate"
python -m pip install --upgrade pip
pip install -r "$APP_DIR/requirements.txt"

echo "==> Refreshing local model caches"
export HF_HOME="${HF_HOME:-$APP_DIR/.hf-cache}"
python "$APP_DIR/scripts/preload_embeddings.py"
ollama pull "$OLLAMA_MODEL"

echo "==> Restarting service"
sudo systemctl restart "$SERVICE_NAME"
sudo systemctl --no-pager --full status "$SERVICE_NAME" | head -n 20
