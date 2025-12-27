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

# Copy settings.json from workspace if it exists, otherwise create minimal one
if [ ! -f "$CONFIG_FILE" ]; then
    # Check if workspace/.vscode/settings.json exists
    if [ -f "$WORKSPACE_DIR/.vscode/settings.json" ]; then
        cp "$WORKSPACE_DIR/.vscode/settings.json" "$CONFIG_FILE"
        echo "✅ Copied workspace settings"
    else
        cat > "$CONFIG_FILE" << 'EOF'
{
  "codeBuddy.apiGatewayUrl": "http://localhost/api",
  "codeBuddy.ollamaUrl": "http://localhost:11434",
  "codeBuddy.enabled": true
}
EOF
        echo "✅ Created workspace settings"
    fi
else
    echo "✅ Workspace settings already exist"
fi

# Copy extensions.json from workspace if it exists
EXTENSIONS_FILE="$CONFIG_DIR/extensions.json"
if [ ! -f "$EXTENSIONS_FILE" ]; then
    if [ -f "$WORKSPACE_DIR/.vscode/extensions.json" ]; then
        cp "$WORKSPACE_DIR/.vscode/extensions.json" "$EXTENSIONS_FILE"
        echo "✅ Copied extensions recommendations"
    else
        cat > "$EXTENSIONS_FILE" << 'EOF'
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-python.black-formatter",
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "ms-vscode.vscode-typescript-next",
    "ms-vscode.vscode-json",
    "redhat.vscode-yaml",
    "ms-azuretools.vscode-docker",
    "eamodio.gitlens"
  ]
}
EOF
        echo "✅ Created extensions recommendations"
    fi
fi

# Copy tasks.json from workspace if it exists, otherwise create it
TASKS_FILE="$CONFIG_DIR/tasks.json"
if [ ! -f "$TASKS_FILE" ]; then
    if [ -f "$WORKSPACE_DIR/.vscode/tasks.json" ]; then
        cp "$WORKSPACE_DIR/.vscode/tasks.json" "$TASKS_FILE"
        echo "✅ Copied VS Code tasks"
    else
        cat > "$TASKS_FILE" << 'EOF'
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Code Buddy: Test Connection",
      "type": "shell",
      "command": "${workspaceFolder}/.vscode/test-connection.sh",
      "problemMatcher": [],
      "presentation": {
        "reveal": "always",
        "panel": "new"
      }
    },
    {
      "label": "Code Buddy: Health Check",
      "type": "shell",
      "command": "curl -s http://localhost/api/health | python3 -m json.tool",
      "problemMatcher": [],
      "presentation": {
        "reveal": "always"
      }
    },
    {
      "label": "Code Buddy: List Models",
      "type": "shell",
      "command": "curl -s http://localhost/api/models | python3 -m json.tool",
      "problemMatcher": [],
      "presentation": {
        "reveal": "always"
      }
    },
    {
      "label": "Code Buddy: Index Workspace",
      "type": "shell",
      "command": "curl -X POST http://localhost/api/index",
      "problemMatcher": [],
      "presentation": {
        "reveal": "always",
        "panel": "new"
      }
    },
    {
      "label": "Code Buddy: Check Index Status",
      "type": "shell",
      "command": "curl -s http://localhost/api/index/status | python3 -m json.tool",
      "problemMatcher": [],
      "presentation": {
        "reveal": "always"
      }
    }
  ]
}
EOF
        echo "✅ Created VS Code tasks"
    fi
fi

# Copy test-connection.sh if it exists
TEST_SCRIPT="$CONFIG_DIR/test-connection.sh"
if [ ! -f "$TEST_SCRIPT" ] && [ -f "$WORKSPACE_DIR/.vscode/test-connection.sh" ]; then
    cp "$WORKSPACE_DIR/.vscode/test-connection.sh" "$TEST_SCRIPT"
    chmod +x "$TEST_SCRIPT"
    echo "✅ Copied test connection script"
fi

# Ensure test-connection.sh is executable
if [ -f "$TEST_SCRIPT" ]; then
    chmod +x "$TEST_SCRIPT"
fi

echo ""
echo "=========================================="
echo "Workspace Setup Complete!"
echo "=========================================="
echo ""
echo "Your workspace is now configured with:"
echo "  ✅ API Gateway connection"
echo "  ✅ Ollama connection"
echo "  ✅ VS Code tasks (Code Buddy: *)"
echo "  ✅ All AI features enabled"
echo ""
echo "You can start coding immediately!"
echo ""
