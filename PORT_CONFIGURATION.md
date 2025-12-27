# Port Configuration Summary

## External Ports (Exposed to Host OS)

**3 ports** are exposed to the host operating system:

| Port | Service | Purpose | Required |
|------|---------|---------|----------|
| **80** | Nginx | HTTP access to web IDE and API | ✅ Yes |
| **443** | Nginx | HTTPS access (when configured) | ⚠️ Optional |
| **${CODE_SERVER_PORT:-8080}** | Code-Server | Direct access to web IDE (all host IPs) | ⚠️ Optional (default: 8080) |

## Internal Ports (Docker Network Only)

All other services use `expose` (not `ports`), making them accessible **only** on the internal Docker network:

| Service | Internal Port | Access Method |
|---------|---------------|---------------|
| Code-Server | 8080 | Via Nginx (port 80) or direct on port ${CODE_SERVER_PORT:-8080} (all host IPs) |
| API Gateway | 9000 | Via Nginx (port 80/api) |
| Agent Orchestrator | 8000 | Via API Gateway |
| Rules Engine | 8001 | Via API Gateway |
| Code Indexer | 8002 | Via API Gateway |
| RAG Chat | 8003 | Via API Gateway |
| Terminal AI | 8004 | Via API Gateway |
| MCP GitHub | 3001 | Via API Gateway |
| MCP GitLab | 3002 | Via API Gateway |
| VS Code Extension Server | 3003 (HTTP), 3004 (WebSocket) | Via API Gateway |
| Qdrant | 6333 (HTTP), 6334 (gRPC) | Via Code Indexer/RAG Chat |

## Benefits

1. **No Port Conflicts**: Only 2 ports exposed (80, 443)
2. **Security**: Services not accessible from host network
3. **Isolation**: All inter-service communication on internal network
4. **Clean Architecture**: Single entry point (Nginx)

## Access Patterns

### From Browser/Host
```
http://localhost          → Nginx:80 → Code-Server:8080 (internal)
http://localhost/api      → Nginx:80 → API Gateway:9000 (internal)
```

### Between Services (Internal Network)
```
API Gateway → Agent Orchestrator:8000 (internal)
API Gateway → Rules Engine:8001 (internal)
Agent Orchestrator → MCP GitHub:3001 (internal)
Code Indexer → Qdrant:6333 (internal)
RAG Chat → Qdrant:6333 (internal)
```

## Service Discovery

Services find each other using Docker's internal DNS:
- `http://agent-orchestrator:8000` (not `localhost:8000`)
- `http://qdrant:6333` (not `localhost:6333`)
- `http://mcp-github:3001` (not `localhost:3001`)

## Configuration

All environment variables use internal service names:
- `AGENT_ORCHESTRATOR_URL=http://agent-orchestrator:8000`
- `QDRANT_URL=http://qdrant:6333`
- `MCP_GITHUB_URL=http://mcp-github:3001`

This ensures all communication stays on the internal network.

## Port Conflict Prevention

If port 80 or 443 conflicts with other services:

### Change Nginx Ports

Edit `docker-compose.yml`:

```yaml
nginx:
  ports:
    - "8080:80"    # Change from 80:80
    - "8443:443"   # Change from 443:443
```

Then access via:
- `http://localhost:8080`
- `https://localhost:8443`

### All Other Ports

All other services are internal-only and **will not conflict** with host services.

## Verification

Check exposed ports:
```bash
# List only externally exposed ports
docker-compose ps --format json | jq -r '.[] | select(.Ports != "") | "\(.Name): \(.Ports)"'

# Should only show:
# - nginx: 0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
```

## Summary

✅ **Only 2 ports exposed** (80, 443)  
✅ **All other services internal-only**  
✅ **No port conflicts** with host services  
✅ **Secure** - services not accessible from host  
✅ **Clean** - single entry point via Nginx  

