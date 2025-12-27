#!/bin/bash

# Force reload tasks.json in VS Code workspace
# This ensures tasks are available

WORKSPACE_DIR="/home/coder/workspace"
TASKS_FILE="$WORKSPACE_DIR/.vscode/tasks.json"

echo "Ensuring tasks.json exists and is accessible..."

# Create .vscode directory if needed
mkdir -p "$WORKSPACE_DIR/.vscode"

# Copy tasks.json from host if it exists and container version doesn't
if [ -f "/workspace/.vscode/tasks.json" ] && [ ! -f "$TASKS_FILE" ]; then
    cp /workspace/.vscode/tasks.json "$TASKS_FILE"
    chmod 644 "$TASKS_FILE"
    echo "✅ Copied tasks.json from host"
fi

# Ensure file exists with correct content
if [ ! -f "$TASKS_FILE" ]; then
    cat > "$TASKS_FILE" << 'TASKS_EOF'
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
      "command": "curl -s http://nginx/api/health | python3 -m json.tool 2>/dev/null || curl -s http://nginx/api/health | jq . 2>/dev/null || curl -s http://nginx/api/health",
      "problemMatcher": [],
      "presentation": {
        "reveal": "always"
      }
    },
    {
      "label": "Code Buddy: List Models",
      "type": "shell",
      "command": "curl -s http://nginx/api/models | python3 -m json.tool 2>/dev/null || curl -s http://nginx/api/models | jq . 2>/dev/null || curl -s http://nginx/api/models",
      "problemMatcher": [],
      "presentation": {
        "reveal": "always"
      }
    },
    {
      "label": "Code Buddy: Index Workspace",
      "type": "shell",
      "command": "curl -X POST http://nginx/api/index",
      "problemMatcher": [],
      "presentation": {
        "reveal": "always",
        "panel": "new"
      }
    },
    {
      "label": "Code Buddy: Check Index Status",
      "type": "shell",
      "command": "curl -s http://nginx/api/index/status | python3 -m json.tool 2>/dev/null || curl -s http://nginx/api/index/status | jq . 2>/dev/null || curl -s http://nginx/api/index/status",
      "problemMatcher": [],
      "presentation": {
        "reveal": "always"
      }
    }
  ]
}
TASKS_EOF
    chmod 644 "$TASKS_FILE"
    echo "✅ Created tasks.json"
fi

# Ensure test-connection.sh exists and is executable
TEST_SCRIPT="$WORKSPACE_DIR/.vscode/test-connection.sh"
if [ ! -f "$TEST_SCRIPT" ] && [ -f "/workspace/.vscode/test-connection.sh" ]; then
    cp /workspace/.vscode/test-connection.sh "$TEST_SCRIPT"
    chmod +x "$TEST_SCRIPT"
    echo "✅ Copied test-connection.sh"
fi

echo ""
echo "✅ Tasks configuration complete!"
echo ""
echo "To see tasks in VS Code:"
echo "  1. Press Ctrl+Shift+P"
echo "  2. Type: 'Tasks: Reload Tasks' (to reload)"
echo "  3. Then: 'Tasks: Run Task'"
echo ""

