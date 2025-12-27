# Quick Start Guide

## 0. Install and Configure Ollama on Host

**Important**: Ollama runs natively on the Docker host (not in a container).

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Configure to listen on all interfaces (no API key required)
export OLLAMA_HOST=0.0.0.0:11434

# Start Ollama (or configure as systemd service)
ollama serve

# Verify Ollama is running
curl http://localhost:11434/api/tags
```

## 1. Initial Setup

```bash
# Navigate to the project directory
cd /home/aarshe/code-buddy

# Run the setup script
./setup.sh
```

## 2. Configure Environment

Edit `.env` file:

```bash
nano .env
```

Set at minimum:
- `CODE_SERVER_PASSWORD` - Your password for the web IDE

Optional (for GitHub/GitLab integration):
- `GITHUB_TOKEN` - GitHub personal access token
- `GITLAB_TOKEN` - GitLab personal access token

## 3. Start Services

```bash
docker compose up -d
```

## 4. Pull Ollama Models (on Host)

For your 96GB VRAM system, recommended models:

```bash
# Coding model (recommended)
ollama pull deepseek-coder:33b

# Reasoning model (recommended)
ollama pull llama3.2:90b

# Embedding model (required for RAG)
ollama pull nomic-embed-text

# Verify installation
ollama list
```

See [MODEL_RECOMMENDATIONS.md](MODEL_RECOMMENDATIONS.md) for complete recommendations.

## 5. Access the IDE

Open your browser and navigate to:
- **Web IDE**: http://localhost
- **API Gateway**: http://localhost/api

Login with the password you set in `.env`.

## 6. Test the System

### Generate Code

```bash
curl -X POST http://localhost/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a Python function to calculate fibonacci numbers",
    "language": "python"
  }'
```

### Check Health

```bash
curl http://localhost/api/health
```

## Common Commands

```bash
# View logs
docker compose logs -f

# View logs for specific service
docker compose logs -f agent-orchestrator

# Restart services
docker compose restart

# Stop services
docker compose down

# Rebuild after code changes
docker compose build
docker compose up -d
```

## Troubleshooting

### Services won't start
```bash
# Check Docker status
docker ps
docker compose ps

# Check logs
docker compose logs
```

### GPU not working
```bash
# Test GPU access
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi

# If that fails, install NVIDIA Container Toolkit
```

### Out of memory
- Use smaller models (llama3.2:3b, codellama:7b)
- Reduce OLLAMA_KEEP_ALIVE time
- Close other GPU-intensive applications

## Next Steps

1. Install recommended extensions in Code-Server
2. Configure your coding rules in `rules/` directory
3. Set up GitHub/GitLab tokens for repository integration
4. Start coding with AI assistance!

For detailed documentation, see [README.md](README.md).

