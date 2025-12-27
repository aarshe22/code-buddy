#!/bin/bash

# Code Buddy Setup Script
# This script sets up the complete AI development stack
# Usage: ./setup.sh [options]
# Options:
#   -clean    Clean up leftover artifacts from failed builds

set -e

# Cleanup function
cleanup_artifacts() {
    echo "=========================================="
    echo "Code Buddy Cleanup"
    echo "=========================================="
    echo ""
    
    # Stop and remove containers
    echo "Stopping and removing containers..."
    docker compose down --remove-orphans 2>/dev/null || true
    
    # Remove code-buddy containers (in case compose down didn't catch them)
    CONTAINERS=$(docker ps -a --filter "name=code-buddy-" --format "{{.Names}}" 2>/dev/null || true)
    if [ ! -z "$CONTAINERS" ]; then
        echo "$CONTAINERS" | while read container; do
            if [ ! -z "$container" ]; then
                echo "  Removing container: $container"
                docker rm -f "$container" 2>/dev/null || true
            fi
        done
    else
        echo "  No code-buddy containers found"
    fi
    
    # Remove code-buddy images
    echo ""
    echo "Removing code-buddy images..."
    
    # Get project name from directory or docker-compose
    PROJECT_NAME=$(basename "$(pwd)" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g')
    
    # Find images by container names (more reliable)
    IMAGE_IDS=$(docker ps -a --filter "name=code-buddy-" --format "{{.Image}}" 2>/dev/null | sort -u || true)
    
    # Also find images by project name pattern (docker compose naming)
    COMPOSE_IMAGES=$(docker images --format "{{.Repository}}:{{.Tag}}" | grep -E "^${PROJECT_NAME}_|^code-buddy-" 2>/dev/null || true)
    
    # Combine and deduplicate
    ALL_IMAGES=$(echo -e "$IMAGE_IDS\n$COMPOSE_IMAGES" | grep -v "^$" | sort -u)
    
    if [ ! -z "$ALL_IMAGES" ]; then
        echo "$ALL_IMAGES" | while read image; do
            if [ ! -z "$image" ] && [ "$image" != "<none>:<none>" ]; then
                # Check if image exists
                if docker image inspect "$image" &>/dev/null; then
                    echo "  Removing image: $image"
                    docker rmi -f "$image" 2>/dev/null || true
                fi
            fi
        done
    else
        echo "  No code-buddy images found"
    fi
    
    # Also remove any images tagged with code-buddy service names
    SERVICE_IMAGES=$(docker images --format "{{.Repository}}:{{.Tag}}" | grep -E "code-buddy-(agent-orchestrator|mcp-github|mcp-gitlab|code-indexer|rag-chat|rules-engine|api-gateway|vscode-extension|terminal-ai)" 2>/dev/null || true)
    if [ ! -z "$SERVICE_IMAGES" ]; then
        echo "$SERVICE_IMAGES" | while read image; do
            if [ ! -z "$image" ] && [ "$image" != "<none>:<none>" ]; then
                if docker image inspect "$image" &>/dev/null; then
                    echo "  Removing image: $image"
                    docker rmi -f "$image" 2>/dev/null || true
                fi
            fi
        done
    fi
    
    # Remove code-buddy network
    echo ""
    echo "Removing code-buddy network..."
    if docker network ls | grep -q "code-buddy-network"; then
        docker network rm code-buddy-network 2>/dev/null || true
        echo "  Network removed"
    else
        echo "  Network not found"
    fi
    
    # Clean up build cache (optional - can be large)
    echo ""
    read -p "Remove Docker build cache? This can free up significant space (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Cleaning build cache..."
        docker builder prune -f
        echo "  Build cache cleaned"
    else
        echo "  Skipping build cache cleanup"
    fi
    
    # Remove dangling images
    echo ""
    echo "Removing dangling images..."
    DANGLING=$(docker images -f "dangling=true" -q 2>/dev/null || true)
    if [ ! -z "$DANGLING" ]; then
        docker rmi -f $DANGLING 2>/dev/null || true
        echo "  Dangling images removed"
    else
        echo "  No dangling images found"
    fi
    
    docker system prune -a --volumes
    
    echo ""
    echo "=========================================="
    echo "Cleanup Complete!"
    echo "=========================================="
    echo ""
    echo "Removed:"
    echo "  - Stopped containers"
    echo "  - Code-buddy images"
    echo "  - Code-buddy network"
    echo "  - Dangling images"
    echo ""
    echo "Note: Volumes were NOT removed to preserve your data."
    echo "      To remove volumes, use: docker volume rm <volume-name>"
    echo ""
    exit 0
}

# Check for cleanup flag
if [ "$1" = "-clean" ] || [ "$1" = "--clean" ] || [ "$1" = "clean" ]; then
    cleanup_artifacts
fi

echo "=========================================="
echo "Code Buddy Setup"
echo "=========================================="

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first."
    exit 1
fi

# Check for Docker Compose
if ! docker compose version &> /dev/null; then
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
docker compose build

# Start services
echo "Starting services..."
docker compose up -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 10

# Check service health
echo "Checking service health..."
docker compose ps

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
# Load CODE_SERVER_PORT from .env if it exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | grep CODE_SERVER_PORT | xargs) 2>/dev/null || true
fi
CODE_SERVER_PORT=${CODE_SERVER_PORT:-8080}
echo "Services are running:"
echo "  - Web IDE (via Nginx): http://localhost"
echo "  - Web IDE (direct): http://localhost:${CODE_SERVER_PORT}"
echo "  - API Gateway: http://localhost/api"
echo ""
echo "Note: Code-Server is accessible on all host IP addresses on port ${CODE_SERVER_PORT}"
echo ""
echo "To view logs: docker compose logs -f"
echo "To stop services: docker compose down"
echo "To restart services: docker compose restart"
echo "To cleanup failed builds: ./setup.sh -clean"
echo ""
echo "Next steps:"
echo "1. Open http://localhost in your browser"
echo "2. Login with password from .env file"
echo "3. Install recommended extensions in Code Server"
echo "4. Start coding with AI assistance!"
echo ""

