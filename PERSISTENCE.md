# Data Persistence Guide

This document explains how data persistence is configured in Code Buddy to ensure no information is lost when containers are rebuilt.

## Volume Strategy

All persistent data is stored in **Docker named volumes**, which survive container rebuilds, updates, and restarts. Configuration files are mounted as read-only where appropriate to prevent accidental modification.

## Persistent Data by Service

### Ollama (Host-Native)
- **Note**: Ollama runs natively on the Docker host, not in a container
- **Location**: `~/.ollama/` on host system
- **Contains**:
  - Downloaded models
  - Model cache
  - Configuration
- **Backup**: Backup the `~/.ollama/` directory on the host

### Code-Server
- **Volumes**:
  - `code-server-data`: User data and settings
  - `code-server-config`: Configuration files
  - `code-server-extensions`: Installed extensions
  - `code-server-logs`: Application logs
- **Locations**:
  - `/home/coder` - User home directory
  - `/home/coder/.config` - Configuration
  - `/home/coder/.local/share/code-server/extensions` - Extensions
  - `/home/coder/.local/share/code-server/logs` - Logs
- **Note**: Settings file is mounted read-only from host

### Agent Orchestrator
- **Volumes**:
  - `agent-data`: Persistent data
  - `agent-cache`: Cache files
  - `agent-logs`: Application logs
  - `agent-state`: Agent state and history
- **Locations**:
  - `/app/data` - Data directory
  - `/app/.cache` - Cache directory
  - `/app/logs` - Log directory
  - `/app/state` - State directory

### MCP GitHub Server
- **Volumes**:
  - `mcp-github-data`: Persistent data
  - `mcp-github-cache`: Cache files
  - `mcp-github-logs`: Application logs
  - `mcp-github-node_modules`: Node.js dependencies
- **Locations**:
  - `/app/data` - Data directory
  - `/app/.cache` - Cache directory
  - `/app/logs` - Log directory
  - `/app/node_modules` - Dependencies

### MCP GitLab Server
- **Volumes**:
  - `mcp-gitlab-data`: Persistent data
  - `mcp-gitlab-cache`: Cache files
  - `mcp-gitlab-logs`: Application logs
  - `mcp-gitlab-node_modules`: Node.js dependencies
- **Locations**:
  - `/app/data` - Data directory
  - `/app/.cache` - Cache directory
  - `/app/logs` - Log directory
  - `/app/node_modules` - Dependencies

### Qdrant
- **Volumes**:
  - `qdrant-data`: Vector database storage
  - `qdrant-config`: Configuration files
  - `qdrant-logs`: Application logs
- **Locations**:
  - `/qdrant/storage` - Database files
  - `/qdrant/config` - Configuration
  - `/qdrant/logs` - Logs

### Code Indexer
- **Volumes**:
  - `indexer-data`: Persistent data
  - `indexer-cache`: Cache files
  - `indexer-logs`: Application logs
  - `indexer-state`: Indexing state
- **Locations**:
  - `/app/data` - Data directory
  - `/app/.cache` - Cache directory
  - `/app/logs` - Log directory
  - `/app/state` - Indexing state

### RAG Chat
- **Volumes**:
  - `rag-chat-data`: Persistent data
  - `rag-chat-cache`: Cache files
  - `rag-chat-logs`: Application logs
- **Locations**:
  - `/app/data` - Data directory
  - `/app/.cache` - Cache directory
  - `/app/logs` - Log directory

### Rules Engine
- **Volumes**:
  - `rules-data`: Persistent data
  - `rules-cache`: Cache files
  - `rules-logs`: Application logs
- **Locations**:
  - `/app/data` - Data directory
  - `/app/.cache` - Cache directory
  - `/app/logs` - Log directory
- **Note**: Rules directory is mounted read-only from host

### API Gateway
- **Volumes**:
  - `api-gateway-data`: Persistent data
  - `api-gateway-cache`: Cache files
  - `api-gateway-logs`: Application logs
- **Locations**:
  - `/app/data` - Data directory
  - `/app/.cache` - Cache directory
  - `/app/logs` - Log directory

### Nginx
- **Volumes**:
  - `nginx-logs`: Access and error logs
  - `nginx-cache`: Proxy cache
- **Locations**:
  - `/var/log/nginx` - Log files
  - `/var/cache/nginx` - Cache files
- **Note**: Configuration files are mounted read-only from host

## Workspace

The workspace directory (`./workspace`) is mounted as a bind mount to allow direct access from the host. This is your code workspace and is not stored in a Docker volume.

## Backup and Restore

### Backup All Volumes

```bash
# Create backup directory
mkdir -p backups/$(date +%Y%m%d)

# Backup all volumes
docker run --rm \
  -v code-buddy_ollama-data:/data \
  -v $(pwd)/backups/$(date +%Y%m%d):/backup \
  alpine tar czf /backup/ollama-data.tar.gz -C /data .

# Repeat for each volume...
```

Or use a script:

```bash
#!/bin/bash
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

for volume in $(docker volume ls -q | grep code-buddy); do
  echo "Backing up $volume..."
  docker run --rm \
    -v "$volume":/data \
    -v "$(pwd)/$BACKUP_DIR":/backup \
    alpine tar czf "/backup/${volume}.tar.gz" -C /data .
done

echo "Backup complete: $BACKUP_DIR"
```

### Restore Volume

```bash
# Restore a volume
docker run --rm \
  -v code-buddy_ollama-data:/data \
  -v $(pwd)/backups/20240101:/backup \
  alpine sh -c "cd /data && tar xzf /backup/ollama-data.tar.gz"
```

### List All Volumes

```bash
docker volume ls | grep code-buddy
```

### Inspect Volume

```bash
docker volume inspect code-buddy_ollama-data
```

### Remove Volume (WARNING: Deletes Data)

```bash
docker volume rm code-buddy_ollama-data
```

## Data Locations on Host

Docker volumes are stored in Docker's data directory:
- **Linux**: `/var/lib/docker/volumes/`
- **macOS/Windows**: Docker Desktop manages volumes

To find a specific volume:

```bash
docker volume inspect code-buddy_ollama-data | grep Mountpoint
```

## Migration

### Moving to New Host

1. **Backup volumes** (see above)
2. **Copy backup files** to new host
3. **Start services** on new host (creates volumes)
4. **Restore volumes** (see above)

### Upgrading Stack

Volumes persist through upgrades:

```bash
# Pull latest code
git pull

# Rebuild and restart (volumes persist)
docker compose build
docker compose up -d
```

## Environment Variables

Services use environment variables to configure data directories:

- `DATA_DIR`: Persistent data directory
- `CACHE_DIR`: Cache directory
- `LOG_DIR`: Log directory
- `STATE_DIR`: State directory (where applicable)

These are set in `docker-compose.yml` and point to mounted volumes.

## Best Practices

1. **Regular Backups**: Set up automated backups of critical volumes
2. **Monitor Volume Size**: Check volume sizes regularly
3. **Clean Old Data**: Periodically clean cache volumes if needed
4. **Document Custom Data**: If you add custom data locations, document them
5. **Test Restores**: Periodically test restore procedures

## Troubleshooting

### Volume Not Persisting

1. Check volume exists: `docker volume ls | grep code-buddy`
2. Check volume mount: `docker inspect <container> | grep -A 10 Mounts`
3. Verify volume is named (not anonymous)

### Out of Disk Space

1. Check volume sizes: `docker system df -v`
2. Clean unused volumes: `docker volume prune`
3. Clean old logs: Remove old log files from log volumes

### Permission Issues

1. Check volume ownership: `docker exec <container> ls -la /app/data`
2. Fix permissions: `docker exec <container> chown -R <user>:<group> /app/data`

## Summary

All persistent data is stored in Docker named volumes that survive:
- Container rebuilds
- Container updates
- Stack restarts
- Host reboots (if Docker daemon persists)

Only the workspace directory uses a bind mount for direct host access. All other data is isolated in Docker volumes for better portability and management.

