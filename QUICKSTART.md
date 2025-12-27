# Quick Start Guide

Get Code Buddy up and running in minutes!

## Prerequisites

- Ubuntu Linux (20.04+)
- Docker and Docker Compose installed
- NVIDIA GPU with drivers (for GPU acceleration)
- Ollama installed on host (see step 0)

## 0. Install and Configure Ollama on Host

**Important**: Ollama runs natively on the Docker host (not in a container).

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Configure to listen on all interfaces (no API key required)
export OLLAMA_HOST=0.0.0.0:11434

# Create systemd service for auto-start (recommended)
sudo tee /etc/systemd/system/ollama.service > /dev/null <<EOF
[Unit]
Description=Ollama Service
After=network.target

[Service]
Type=simple
User=$USER
Environment="OLLAMA_HOST=0.0.0.0:11434"
ExecStart=/usr/local/bin/ollama serve
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Enable and start Ollama
sudo systemctl daemon-reload
sudo systemctl enable ollama
sudo systemctl start ollama

# Verify Ollama is running
curl http://localhost:11434/api/tags
ollama list
```

## 1. Initial Setup

```bash
# Navigate to the project directory
cd /home/aarshe/code-buddy

# Run the setup script
chmod +x setup.sh
./setup.sh
```

## 2. Configure Environment

Edit `.env` file:

```bash
nano .env
```

Set at minimum:
- `CODE_SERVER_PASSWORD` - Your password for the web IDE
- `CODE_SERVER_PORT` - Port for direct Code-Server access (default: 8080)

Optional (for GitHub/GitLab integration):
- `GITHUB_TOKEN` - GitHub personal access token
- `GITLAB_TOKEN` - GitLab personal access token

## 3. Start Services

```bash
docker compose up -d
```

Wait for services to start (30-60 seconds), then check status:

```bash
docker compose ps
```

## 4. Pull Ollama Models (on Host)

For your 96GB VRAM system, recommended models:

```bash
# Coding model (recommended)
ollama pull deepseek-coder:33b

# Reasoning model (recommended)
ollama pull qwen2.5:72b

# Embedding model (required for RAG)
ollama pull nomic-embed-text

# Verify installation
ollama list
```

**Note**: Model downloads can take 10-30 minutes depending on internet speed.

## 5. Access the IDE

Open your browser and navigate to:
- **Web IDE (via Nginx)**: http://localhost
- **Web IDE (direct)**: http://localhost:8080 (or your configured port)
- **API Gateway**: http://localhost/api

Login with the password you set in `.env`.

## 6. Test the System

### Health Check

```bash
curl http://localhost/api/health | python3 -m json.tool
```

### Generate Code

```bash
curl -X POST http://localhost/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a Python function to calculate fibonacci numbers",
    "language": "python"
  }'
```

### Index Your Codebase (for RAG)

```bash
# Index entire workspace
curl -X POST http://localhost/api/index

# Check status
curl http://localhost/api/index/status
```

### Chat with Your Codebase

```bash
curl -X POST http://localhost/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What files are in this workspace?"
  }'
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

# Check service status
docker compose ps
```

## Troubleshooting

### Services won't start

```bash
# Check Docker status
docker ps
docker compose ps

# Check logs
docker compose logs

# Check if Ollama is running
curl http://localhost:11434/api/tags
```

### GPU not working

```bash
# Test GPU access
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi

# If that fails, install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

### Ollama not accessible

```bash
# Check if Ollama is running
sudo systemctl status ollama

# Check Ollama logs
journalctl -u ollama -f

# Verify OLLAMA_HOST
echo $OLLAMA_HOST
# Should output: 0.0.0.0:11434

# Test from container
docker run --rm --add-host=host.docker.internal:host-gateway \
  curlimages/curl:latest \
  curl http://host.docker.internal:11434/api/tags
```

### Out of memory

- Use smaller models (llama3.1:8b, codellama:7b)
- Reduce OLLAMA_KEEP_ALIVE time
- Close other GPU-intensive applications
- Check memory: `free -h` and `nvidia-smi`

### Port conflicts

```bash
# Check what's using ports
sudo lsof -i :80
sudo lsof -i :8080

# Change CODE_SERVER_PORT in .env
```

## Next Steps

1. **Index your codebase** - Run the index command to enable RAG features
2. **Install extensions** - Open Code-Server and install recommended extensions
3. **Configure rules** - Set up coding rules in `rules/` directory
4. **Set up tokens** - Add GitHub/GitLab tokens for repository integration
5. **Start coding** - Everything is ready!

## Model Recommendations

### For 96GB VRAM (Your System)

```bash
ollama pull deepseek-coder:33b    # Coding (~20GB VRAM)
ollama pull qwen2.5:72b          # Reasoning (~47GB VRAM)
ollama pull nomic-embed-text      # Embeddings (~2GB VRAM)
```

**Total**: ~72GB VRAM (leaves 24GB headroom)

### For 48GB VRAM

```bash
ollama pull codellama:34b         # Coding (~20GB VRAM)
ollama pull llama3.1:70b          # Reasoning (~40GB VRAM)
ollama pull nomic-embed-text      # Embeddings (~2GB VRAM)
```

### For 24GB VRAM

```bash
ollama pull codellama:13b         # Coding (~8GB VRAM)
ollama pull llama3.1:8b           # Reasoning (~5GB VRAM)
ollama pull nomic-embed-text      # Embeddings (~2GB VRAM)
```

### For 12GB VRAM

```bash
ollama pull codellama:7b          # Coding (~4GB VRAM)
ollama pull llama3.1:3b            # Reasoning (~2GB VRAM)
ollama pull nomic-embed-text      # Embeddings (~2GB VRAM)
```

## Access Methods

### Via Nginx (Recommended)
- **URL**: http://localhost or http://<host-ip>
- **Port**: 80
- **Benefits**: Single entry point, SSL support (when configured)

### Direct Access
- **URL**: http://localhost:8080 or http://<host-ip>:8080
- **Port**: Configurable via `CODE_SERVER_PORT` in `.env`
- **Benefits**: Direct access, bypasses Nginx

**Note**: Code-Server is accessible on all host IP addresses.

## Getting Help

For detailed documentation, see [README.md](README.md).

For issues:
1. Check service logs: `docker compose logs <service-name>`
2. Check health: `curl http://localhost/api/health`
3. Verify Ollama: `ollama list` (on host)
