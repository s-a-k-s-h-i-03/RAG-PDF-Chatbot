# Ubuntu VM Deployment

This folder contains a self-hosted deployment path for the current Streamlit + Ollama app.

Files:

- `bootstrap.sh`: one-time VM setup
- `install_service.sh`: creates the systemd service
- `update.sh`: pulls the latest code and restarts the app
- `nginx/rag-pdf-chatbot.conf`: reverse proxy for public access

Recommended target:

- Ubuntu 22.04 or 24.04
- 2 vCPU minimum
- 4 GB RAM minimum
- 20+ GB disk

Run the first-time setup on the VM:

```bash
chmod +x deploy/ubuntu-vm/*.sh
APP_DIR=/opt/rag-pdf-chatbot ./deploy/ubuntu-vm/bootstrap.sh
```
