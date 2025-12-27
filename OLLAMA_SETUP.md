# Ollama Setup Guide

## Overview

Ollama runs **natively on the Docker host** (not in a container). This provides:
- Direct GPU access for optimal performance
- No container overhead
- Easier model management
- Better resource utilization

## Installation

### 1. Install Ollama

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Verify installation
ollama --version
```

### 2. Configure Ollama

Ollama must be configured to:
- Listen on all interfaces (0.0.0.0)
- No API key required
- Port 11434

#### Option A: Environment Variable (Temporary)

```bash
export OLLAMA_HOST=0.0.0.0:11434
ollama serve
```

#### Option B: Systemd Service (Recommended)

Create a systemd service for automatic startup:

```bash
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

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable ollama
sudo systemctl start ollama

# Verify
sudo systemctl status ollama
```

### 3. Verify Ollama is Running

```bash
# Check if Ollama is accessible
curl http://localhost:11434/api/tags

# List models (should be empty initially)
ollama list
```

## Model Installation

### Recommended Models for Your Hardware

For your NVIDIA RTX PRO 6000 Blackwell (96GB VRAM), AMD Ryzen Threadripper PRO 7985WX (64 cores), and 256GB RAM:

```bash
# Coding model
ollama pull deepseek-coder:33b

# Reasoning model
ollama pull llama3.2:90b

# Embedding model (required for RAG)
ollama pull nomic-embed-text
```

See [MODEL_RECOMMENDATIONS.md](MODEL_RECOMMENDATIONS.md) for complete recommendations.

### Verify Models

```bash
# List installed models
ollama list

# Show model details
ollama show deepseek-coder:33b
ollama show llama3.2:90b
ollama show nomic-embed-text
```

## Configuration for Docker Services

Docker services access Ollama via `host.docker.internal:11434`. This is configured in:

- `docker-compose.yml` - Environment variables
- `.env` file - OLLAMA_HOST and OLLAMA_URL

The default configuration uses `host.docker.internal:11434`, which Docker automatically resolves to the host machine.

## Testing Connection from Containers

```bash
# Test from a container
docker run --rm --add-host=host.docker.internal:host-gateway \
  curlimages/curl:latest \
  curl http://host.docker.internal:11434/api/tags
```

## Troubleshooting

### Ollama Not Accessible from Containers

1. **Check Ollama is running on host**:
   ```bash
   curl http://localhost:11434/api/tags
   ```

2. **Verify OLLAMA_HOST is set correctly**:
   ```bash
   echo $OLLAMA_HOST
   # Should output: 0.0.0.0:11434
   ```

3. **Check firewall**:
   ```bash
   sudo ufw status
   # If firewall is active, allow port 11434
   sudo ufw allow 11434/tcp
   ```

4. **Test host.docker.internal resolution**:
   ```bash
   docker run --rm --add-host=host.docker.internal:host-gateway \
     alpine ping -c 1 host.docker.internal
   ```

### Ollama Service Not Starting

```bash
# Check service status
sudo systemctl status ollama

# Check logs
journalctl -u ollama -f

# Restart service
sudo systemctl restart ollama
```

### GPU Not Detected

```bash
# Check GPU
nvidia-smi

# Verify Ollama can see GPU
ollama ps
```

### Models Not Loading

```bash
# Check available models
ollama list

# Pull missing models
ollama pull <model-name>

# Check model location
ls -lh ~/.ollama/models/
```

## Performance Optimization

### Keep Models Loaded

To keep models in memory for faster inference:

```bash
# Set keep-alive in systemd service
Environment="OLLAMA_KEEP_ALIVE=24h"
```

Or configure per-model:

```bash
# Keep model loaded
ollama run deepseek-coder:33b --keep-alive 24h
```

### Monitor Resource Usage

```bash
# Check GPU usage
nvidia-smi

# Check Ollama processes
ollama ps

# Check system resources
htop
```

## Security Considerations

- **No API Key**: Ollama runs without authentication by default
- **Network Access**: Listening on 0.0.0.0 allows access from containers
- **Firewall**: Consider restricting access if on a network
- **Local Only**: For maximum security, use firewall rules to restrict to localhost/containers only

## Backup Models

```bash
# Models are stored in ~/.ollama/models/
# Backup the entire directory
tar czf ollama-models-backup.tar.gz ~/.ollama/models/
```

## Update Ollama

```bash
# Update Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Restart service
sudo systemctl restart ollama
```

## Summary

1. Install Ollama on host: `curl -fsSL https://ollama.com/install.sh | sh`
2. Configure to listen on 0.0.0.0:11434
3. Set up systemd service for auto-start
4. Pull recommended models
5. Verify connection from containers
6. Start Docker stack

Ollama is now ready to serve the Dev Stack services!

