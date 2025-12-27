#!/bin/bash

# Code-Server Entrypoint Script
# Ensures workspace is opened and configured on startup

set -e

WORKSPACE_DIR="/home/coder/workspace"
CONFIG_DIR="$WORKSPACE_DIR/.vscode"
EXTENSIONS_SCRIPT="/usr/local/bin/install-extensions.sh"
SETUP_SCRIPT="/usr/local/bin/setup-workspace.sh"

# Ensure workspace directory exists and has correct permissions
mkdir -p "$CONFIG_DIR"
chown -R coder:coder "$WORKSPACE_DIR" 2>/dev/null || true
chmod -R 775 "$WORKSPACE_DIR" 2>/dev/null || true

# Run workspace setup script (creates tasks.json, settings.json, etc.)
if [ -f "$SETUP_SCRIPT" ]; then
  bash "$SETUP_SCRIPT" || true
fi

# Install extensions in background (non-blocking)
if [ -f "$EXTENSIONS_SCRIPT" ]; then
  bash "$EXTENSIONS_SCRIPT" > /tmp/extension-install.log 2>&1 &
fi

# Start code-server with workspace opened
exec /usr/bin/code-server \
  --bind-addr 0.0.0.0:8080 \
  --open "$WORKSPACE_DIR" \
  "$@"

