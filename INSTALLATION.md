# Installation Guide

## System Requirements

### Minimum Requirements
- **OS**: Ubuntu 20.04+ or similar Linux distribution
- **CPU**: 8+ cores (64 cores recommended)
- **RAM**: 64GB (256GB recommended)
- **GPU**: NVIDIA GPU with 24GB+ VRAM (96GB recommended)
- **Storage**: 200GB+ free space (SSD recommended)
- **Docker**: 20.10+
- **Docker Compose**: 2.0+

### Your System
- ✅ **GPU**: NVIDIA RTX PRO 6000 Blackwell (96GB VRAM) - Excellent
- ✅ **CPU**: AMD Ryzen Threadripper PRO 7985WX (64 cores) - Excellent
- ✅ **RAM**: 256GB - Excellent
- ✅ **OS**: Ubuntu - Compatible

Your system exceeds all requirements and can run the largest models efficiently.

## Step-by-Step Installation

### 1. Prerequisites

#### Install Docker

```bash
# Remove old versions
sudo apt-get remove docker docker-engine docker.io containerd runc

# Install dependencies
sudo apt-get update
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Add Docker's official GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker compose-plugin

# Add user to docker group (logout/login required)
sudo usermod -aG docker $USER
```

#### Install NVIDIA Container Toolkit

```bash
# Add NVIDIA package repositories
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

# Install
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# Configure Docker
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# Verify
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
```

#### Install Ollama on Host

**Important**: Ollama runs natively on the Docker host, not in a container.

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Configure to listen on all interfaces (no API key required)
export OLLAMA_HOST=0.0.0.0:11434

# Create systemd service for auto-start
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

### 2. Clone/Setup Project

```bash
cd /home/aarshe/code-buddy

# Make scripts executable
chmod +x setup.sh scripts/*.sh

# Run system check
./scripts/check-system.sh
```

### 3. Configure Environment

```bash
# Copy example env file
cp env.example .env

# Edit configuration
nano .env
```

Required settings:
- `CODE_SERVER_PASSWORD`: Set a strong password

Optional settings:
- `GITHUB_TOKEN`: For GitHub integration
- `GITLAB_TOKEN`: For GitLab integration
- `OLLAMA_MODEL`: Default model (default: llama3.2:90b)

### 4. Build and Start Services

```bash
# Build all services
docker compose build

# Start services
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f
```

### 5. Pull Ollama Models (on Host)

```bash
# Pull recommended models for your hardware
ollama pull deepseek-coder:33b    # Coding model (~20GB)
ollama pull llama3.2:90b          # Reasoning model (~50GB)
ollama pull nomic-embed-text      # Embedding model (~2GB)

# This will take 10-30 minutes depending on internet speed
# Total size: ~72GB

# Verify installation
ollama list
```

See [MODEL_RECOMMENDATIONS.md](MODEL_RECOMMENDATIONS.md) for complete model recommendations.

### 6. Verify Installation

```bash
# Check all services
curl http://localhost/api/health

# Should return status of all services
```

### 7. Access the IDE

Open your browser:
- **Web IDE**: http://localhost
- **API**: http://localhost/api

Login with the password from `.env`.

## Post-Installation

### Install Code-Server Extensions

1. Open Code-Server (http://localhost)
2. Go to Extensions (Ctrl+Shift+X)
3. Install recommended extensions:
   - Python
   - Pylance
   - Prettier
   - ESLint
   - GitLens

### Setup GitHub/GitLab Tokens (Optional)

```bash
./scripts/setup-tokens.sh
```

Or manually edit `.env` and add:
```
GITHUB_TOKEN=your_token_here
GITLAB_TOKEN=your_token_here
```

Then restart services:
```bash
docker compose restart mcp-github mcp-gitlab
```

## Troubleshooting

### Docker Issues

```bash
# Check Docker status
sudo systemctl status docker

# Restart Docker
sudo systemctl restart docker

# Check Docker Compose
docker compose version
```

### GPU Issues

```bash
# Verify NVIDIA drivers
nvidia-smi

# Test GPU in Docker
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi

# If fails, reinstall NVIDIA Container Toolkit
```

### Port Conflicts

```bash
# Check what's using ports
sudo lsof -i :80
sudo lsof -i :8080

# Stop conflicting services or change ports in docker compose.yml
```

### Service Won't Start

```bash
# Check logs
docker compose logs <service-name>

# Rebuild service
docker compose build --no-cache <service-name>
docker compose up -d <service-name>
```

### Out of Memory

```bash
# Check memory usage
free -h
docker stats

# Use smaller models
ollama pull llama3.2:3b  # Run on host
```

## Uninstallation

```bash
# Stop and remove containers
docker compose down

# Remove volumes (WARNING: deletes all data)
docker compose down -v

# Remove images
docker compose down --rmi all
```

## Updating

```bash
# Pull latest code
git pull

# Rebuild services
docker compose build

# Restart services
docker compose up -d

# Update models
ollama pull llama3.2:90b  # Run on host
```

## Next Steps

1. Read [QUICKSTART.md](QUICKSTART.md) for usage examples
2. Read [MODELS.md](MODELS.md) for model recommendations
3. Read [ARCHITECTURE.md](ARCHITECTURE.md) for system details
4. Start coding with AI assistance!

## Support

For issues:
1. Check service logs: `docker compose logs <service>`
2. Check health: `curl http://localhost/api/health`
3. Review [README.md](README.md) troubleshooting section

