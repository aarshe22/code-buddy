#!/bin/bash

# Code-Server Entrypoint Script
# Ensures workspace is opened and configured on startup

set -e

WORKSPACE_DIR="/home/coder/workspace"

# Ensure workspace directory exists and has correct permissions
mkdir -p "$WORKSPACE_DIR/.vscode"
chown -R coder:coder "$WORKSPACE_DIR" 2>/dev/null || true
chmod -R 775 "$WORKSPACE_DIR" 2>/dev/null || true

# Start code-server with workspace opened
exec /usr/bin/code-server \
  --bind-addr 0.0.0.0:8080 \
  --open "$WORKSPACE_DIR" \
  "$@"

