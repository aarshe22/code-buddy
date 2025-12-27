#!/bin/bash

# Install Code Buddy Recommended Extensions
# This script installs all recommended VS Code extensions

echo "=========================================="
echo "Installing Code Buddy Extensions"
echo "=========================================="
echo ""

EXTENSIONS=(
  "ms-python.python"
  "ms-python.vscode-pylance"
  "ms-python.black-formatter"
  "dbaeumer.vscode-eslint"
  "esbenp.prettier-vscode"
  "ms-vscode.vscode-typescript-next"
  "ms-vscode.vscode-json"
  "redhat.vscode-yaml"
  "eamodio.gitlens"
)

INSTALLED=0
FAILED=0

for ext in "${EXTENSIONS[@]}"; do
  echo -n "Installing $ext... "
  if code-server --install-extension "$ext" --force 2>/dev/null; then
    echo "✅"
    ((INSTALLED++))
  else
    echo "❌"
    ((FAILED++))
  fi
done

echo ""
echo "=========================================="
echo "Extension Installation Complete"
echo "=========================================="
echo "Installed: $INSTALLED"
echo "Failed: $FAILED"
echo ""

