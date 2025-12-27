# Network Security & Port Configuration

## Port Strategy

All services use the internal Docker network (`code-buddy-network`) for inter-service communication. Only essential ports are exposed to the host.

## External Ports (Exposed to Host)

Only these ports are exposed externally:

| Port | Service | Purpose | Required |
|------|---------|---------|----------|
| **80** | Nginx | HTTP access to web IDE and API | ✅ Yes |
| **443** | Nginx | HTTPS access (when configured) | ⚠️ Optional |

## Internal Ports (Docker Network Only)

All other services use `expose` instead of `ports`, making them accessible only on the internal Docker network:

| Service | Internal Port | Access Method |
|---------|---------------|---------------|
| Code-Server | 8080 | Via Nginx (port 80) or direct on port ${CODE_SERVER_PORT:-8080} (all host IPs) |
| API Gateway | 9000 | Via Nginx (port 80) |
| Agent Orchestrator | 8000 | Via API Gateway |
| Rules Engine | 8001 | Via API Gateway |
| Code Indexer | 8002 | Via API Gateway |
| RAG Chat | 8003 | Via API Gateway |
| Terminal AI | 8004 | Via API Gateway |
| MCP GitHub | 3001 | Via API Gateway |
| MCP GitLab | 3002 | Via API Gateway |
| VS Code Extension Server | 3003, 3004 | Via API Gateway |
| Qdrant | 6333, 6334 | Via Code Indexer/RAG Chat |

## Access Patterns

### External Access (from host/browser)
```
User → localhost:80 (Nginx) → Code-Server:8080 (internal)
User → localhost:80/api (Nginx) → API Gateway:9000 (internal)
```

### Internal Communication (between services)
```
Agent Orchestrator → MCP GitHub:3001 (internal network)
Agent Orchestrator → MCP GitLab:3002 (internal network)
Agent Orchestrator → Qdrant:6333 (internal network)
Code Indexer → Qdrant:6333 (internal network)
RAG Chat → Qdrant:6333 (internal network)
API Gateway → Agent Orchestrator:8000 (internal network)
API Gateway → Rules Engine:8001 (internal network)
```

## Benefits

1. **Security**: Services not exposed to host network
2. **No Conflicts**: Won't conflict with other services on host
3. **Isolation**: All inter-service communication isolated
4. **Clean Architecture**: Single entry point (Nginx)

## Service Discovery

Services discover each other using Docker's internal DNS:
- Service name resolves to container IP
- Example: `http://agent-orchestrator:8000`
- No need for IP addresses or external ports

## Testing Internal Services

To test internal services from host (for debugging):

```bash
# Access via Nginx (recommended)
curl http://localhost/api/health

# Direct access to internal service (for debugging only)
docker exec code-buddy-agent-orchestrator curl http://agent-orchestrator:8000/health
```

## Port Conflict Prevention

If you need to run other services on the host:

- **Port 80**: Change Nginx mapping to `"8080:80"` or another port
- **Port 443**: Change Nginx mapping to `"8443:443"` or another port
- All other ports are internal-only and won't conflict

## Network Isolation

All services communicate via:
- **Internal Network**: `code-buddy-network` (bridge)
- **Service Names**: Docker DNS resolution
- **No External Exposure**: Except Nginx ports

This ensures:
- No port conflicts with host services
- Better security (services not exposed)
- Cleaner architecture
- Easier management

## Configuration

All service URLs in environment variables use internal service names:
- `http://agent-orchestrator:8000` (not `localhost:8000`)
- `http://qdrant:6333` (not `localhost:6333`)
- `http://mcp-github:3001` (not `localhost:3001`)

This ensures all communication stays on the internal network.

