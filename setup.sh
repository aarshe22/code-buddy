#!/bin/bash

# Dev Stack Setup Script
# This script sets up the complete AI development stack

set -e

echo "=========================================="
echo "Dev Stack Setup"
echo "=========================================="

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first."
    exit 1
fi

# Check for Docker Compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "Error: Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check for NVIDIA Docker runtime
if ! docker info | grep -q nvidia; then
    echo "Warning: NVIDIA Docker runtime not detected. GPU acceleration may not work."
    echo "Install nvidia-container-toolkit if you want GPU support."
fi

# Check for Ollama on host
if ! command -v ollama &> /dev/null; then
    echo "Error: Ollama is not installed on the host system."
    echo "Please install Ollama first:"
    echo "  curl -fsSL https://ollama.com/install.sh | sh"
    echo ""
    echo "Then configure it to listen on all interfaces:"
    echo "  export OLLAMA_HOST=0.0.0.0:11434"
    echo "  ollama serve"
    exit 1
fi

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "Warning: Ollama is not running or not accessible on localhost:11434"
    echo "Please start Ollama:"
    echo "  export OLLAMA_HOST=0.0.0.0:11434"
    echo "  ollama serve"
    echo ""
    read -p "Press Enter to continue anyway (or Ctrl+C to exit)..."
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from env.example..."
    cp env.example .env
    echo ""
    echo "Please edit .env file and set your:"
    echo "  - CODE_SERVER_PASSWORD"
    echo "  - GITHUB_TOKEN (optional, for GitHub integration)"
    echo "  - GITLAB_TOKEN (optional, for GitLab integration)"
    echo ""
    read -p "Press Enter to continue after editing .env (or Ctrl+C to exit)..."
fi

# Create workspace directory
mkdir -p workspace
mkdir -p rules

# Create necessary directories
mkdir -p code-server-config
mkdir -p nginx/conf.d

# Build custom images
echo "Building custom service images..."
docker-compose build

# Start services
echo "Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 10

# Check service health
echo "Checking service health..."
docker-compose ps

# Check for recommended Ollama models
echo ""
echo "=========================================="
echo "Checking Ollama models..."
echo "=========================================="
if ollama list | grep -q "deepseek-coder:33b\|llama3.2:90b\|nomic-embed-text"; then
    echo "Some recommended models are already installed."
else
    echo "Recommended models not found. Please install them:"
    echo "  ollama pull deepseek-coder:33b    # Coding model"
    echo "  ollama pull llama3.2:90b          # Reasoning model"
    echo "  ollama pull nomic-embed-text      # Embedding model"
    echo ""
    echo "See MODEL_RECOMMENDATIONS.md for complete recommendations."
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Services are running:"
echo "  - Web IDE: http://localhost"
echo "  - API Gateway: http://localhost/api"
echo "  - Code Server: http://localhost:8080 (direct)"
echo ""
echo "To view logs: docker-compose logs -f"
echo "To stop services: docker-compose down"
echo "To restart services: docker-compose restart"
echo ""
echo "Next steps:"
echo "1. Open http://localhost in your browser"
echo "2. Login with password from .env file"
echo "3. Install recommended extensions in Code Server"
echo "4. Start coding with AI assistance!"
echo ""

