#!/bin/bash

# GitHub/GitLab Token Setup Script

echo "=========================================="
echo "GitHub/GitLab Token Setup"
echo "=========================================="
echo ""

if [ ! -f .env ]; then
    echo "Error: .env file not found. Please run setup.sh first."
    exit 1
fi

# GitHub Token
echo "GitHub Integration (optional)"
echo "To create a GitHub token:"
echo "1. Go to https://github.com/settings/tokens"
echo "2. Click 'Generate new token (classic)'"
echo "3. Select 'repo' scope"
echo "4. Copy the token"
echo ""
read -p "Enter GitHub token (or press Enter to skip): " GITHUB_TOKEN

if [ ! -z "$GITHUB_TOKEN" ]; then
    # Update .env file
    if grep -q "^GITHUB_TOKEN=" .env; then
        sed -i "s|^GITHUB_TOKEN=.*|GITHUB_TOKEN=$GITHUB_TOKEN|" .env
    else
        echo "GITHUB_TOKEN=$GITHUB_TOKEN" >> .env
    fi
    echo "✓ GitHub token saved"
else
    echo "⚠ Skipping GitHub token"
fi

echo ""

# GitLab Token
echo "GitLab Integration (optional)"
echo "To create a GitLab token:"
echo "1. Go to https://gitlab.com/-/user_settings/personal_access_tokens"
echo "2. Create token with 'api' scope"
echo "3. Copy the token"
echo ""
read -p "Enter GitLab token (or press Enter to skip): " GITLAB_TOKEN

if [ ! -z "$GITLAB_TOKEN" ]; then
    # Update .env file
    if grep -q "^GITLAB_TOKEN=" .env; then
        sed -i "s|^GITLAB_TOKEN=.*|GITLAB_TOKEN=$GITLAB_TOKEN|" .env
    else
        echo "GITLAB_TOKEN=$GITLAB_TOKEN" >> .env
    fi
    echo "✓ GitLab token saved"
else
    echo "⚠ Skipping GitLab token"
fi

echo ""
echo "=========================================="
echo "Token Setup Complete"
echo "=========================================="
echo ""
echo "To apply changes, restart services:"
echo "  docker compose restart mcp-github mcp-gitlab"
echo ""

