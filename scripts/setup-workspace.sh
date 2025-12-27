#!/bin/bash

# Setup Workspace Script
# Automatically configures the workspace on first login

WORKSPACE_DIR="/home/coder/workspace"
CONFIG_DIR="$WORKSPACE_DIR/.vscode"
CONFIG_FILE="$CONFIG_DIR/settings.json"

echo "=========================================="
echo "Code Buddy Workspace Setup"
echo "=========================================="
echo ""

# Create .vscode directory if it doesn't exist
mkdir -p "$CONFIG_DIR"

# Check if already configured
if [ -f "$CONFIG_FILE" ] && grep -q "codeBuddy.apiGatewayUrl" "$CONFIG_FILE" 2>/dev/null; then
    echo "✅ Workspace is already configured!"
    exit 0
fi

echo "Configuring workspace..."

# Create settings.json if it doesn't exist
if [ ! -f "$CONFIG_FILE" ]; then
    cat > "$CONFIG_FILE" << 'EOF'
{
  "codeBuddy.apiGatewayUrl": "http://localhost/api",
  "codeBuddy.ollamaUrl": "http://localhost:11434",
  "codeBuddy.enabled": true
}
EOF
    echo "✅ Created workspace settings"
else
    echo "✅ Workspace settings already exist"
fi

# Create extensions.json
EXTENSIONS_FILE="$CONFIG_DIR/extensions.json"
if [ ! -f "$EXTENSIONS_FILE" ]; then
    cat > "$EXTENSIONS_FILE" << 'EOF'
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode"
  ]
}
EOF
    echo "✅ Created extensions recommendations"
fi

# Create README if it doesn't exist
README_FILE="$WORKSPACE_DIR/README.md"
if [ ! -f "$README_FILE" ]; then
    echo "✅ Workspace README will be created by the setup"
fi

echo ""
echo "=========================================="
echo "Workspace Setup Complete!"
echo "=========================================="
echo ""
echo "Your workspace is now configured with:"
echo "  ✅ API Gateway connection"
echo "  ✅ Ollama connection"
echo "  ✅ All AI features enabled"
echo ""
echo "You can start coding immediately!"
echo ""

