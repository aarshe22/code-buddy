# Code Buddy Architecture Explained

## Overview

This document explains how all the components connect and communicate in the Code Buddy stack.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Your Browser                             │
│              (http://localhost:8081)                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ HTTP/WebSocket
                       │
┌──────────────────────▼──────────────────────────────────────┐
│              Code-Server Container                          │
│         (code-buddy-code-server)                             │
│  ┌────────────────────────────────────────────────────┐    │
│  │  VS Code IDE (Browser-based)                       │    │
│  │  - User types code                                  │    │
│  │  - User runs tasks (Ctrl+Shift+P)                   │    │
│  │  - Extensions make API calls                        │    │
│  └──────────────────┬─────────────────────────────────┘    │
│                     │                                        │
│                     │ HTTP Requests                         │
│                     │ (via Docker network)                  │
└─────────────────────┼──────────────────────────────────────┘
                      │
                      │
        ┌─────────────┴─────────────┐
        │                           │
┌───────▼────────┐        ┌─────────▼──────────┐
│   Nginx        │        │  Direct Service    │
│  (Port 80)     │        │   Access           │
│                │        │                    │
│  Routes:       │        │  - api-gateway:9000│
│  / → code-server│       │  - nginx:80        │
│  /api → gateway│        │                    │
└───────┬────────┘        └────────────────────┘
        │
        │
┌───────▼──────────────────────────────────────┐
│         API Gateway (Port 9000)               │
│    (code-buddy-api-gateway)                   │
│                                               │
│  Unified entry point for all services        │
│  - /api/health                               │
│  - /api/generate → Agent Orchestrator        │
│  - /api/chat → RAG Chat                      │
│  - /api/index → Code Indexer                 │
│  - /api/models → Ollama                      │
└───────┬───────────────────────────────────────┘
        │
        │ Routes requests to appropriate services
        │
    ┌───┴───┬──────────┬──────────┬──────────┐
    │       │          │          │          │
┌───▼───┐ ┌─▼────┐ ┌──▼────┐ ┌──▼────┐ ┌───▼────┐
│ Agent │ │ Rules│ │ Code  │ │ RAG   │ │Terminal│
│Orch.  │ │Engine│ │Indexer│ │ Chat  │ │  AI   │
│:8000  │ │:8001 │ │:8002  │ │:8003  │ │:8004  │
└───┬───┘ └──────┘ └───┬───┘ └───┬───┘ └───────┘
    │                  │         │
    │                  │         │
    │            ┌─────▼─────────▼─────┐
    │            │   Qdrant Vector DB  │
    │            │   (Port 6333)       │
    │            │   - Stores code     │
    │            │     embeddings      │
    │            └─────────────────────┘
    │
    │ (via host.docker.internal)
    │
┌───▼──────────────────────────────────────┐
│      Ollama (Host-Native)                 │
│      (Port 11434)                         │
│                                           │
│  Runs on Docker HOST, not in container   │
│  - deepseek-coder:33b (coding)           │
│  - qwen2.5:72b (reasoning)               │
│  - nomic-embed-text (embeddings)         │
│                                           │
│  Accessible via:                          │
│  http://host.docker.internal:11434       │
└───────────────────────────────────────────┘
```

## Connection Flow Examples

### Example 1: User Runs "Code Buddy: Test Connection" Task

```
1. User in Browser (VS Code)
   ↓
2. Presses Ctrl+Shift+P → "Tasks: Run Task" → "Code Buddy: Test Connection"
   ↓
3. VS Code executes: bash .vscode/test-connection.sh
   ↓
4. Script runs in code-server container
   ↓
5. Script makes HTTP requests:
   - curl http://nginx/api/health
   - curl http://api-gateway:9000/health
   - curl http://host.docker.internal:11434/api/tags
   ↓
6. Requests go through Docker network:
   - nginx → api-gateway → services
   - host.docker.internal → Ollama on host
   ↓
7. Results displayed in VS Code terminal
```

### Example 2: User Asks RAG Chat a Question

```
1. User types in VS Code terminal:
   curl -X POST http://nginx/api/chat -d '{"message": "How does auth work?"}'
   ↓
2. Request goes to Nginx (port 80)
   ↓
3. Nginx routes /api/chat → API Gateway (port 9000)
   ↓
4. API Gateway routes to RAG Chat service (port 8003)
   ↓
5. RAG Chat service:
   a. Embeds the question using Ollama (host.docker.internal:11434)
   b. Searches Qdrant for similar code
   c. Gets relevant code context
   d. Sends question + context to Ollama for answer
   ↓
6. Response flows back:
   RAG Chat → API Gateway → Nginx → code-server → User
```

### Example 3: Code Generation Request

```
1. User runs task: "Code Buddy: Generate Code"
   ↓
2. Task executes: curl -X POST http://nginx/api/generate ...
   ↓
3. Request → Nginx → API Gateway
   ↓
4. API Gateway → Agent Orchestrator (port 8000)
   ↓
5. Agent Orchestrator:
   a. Optionally uses RAG to get codebase context
   b. Sends prompt + context to Ollama (host.docker.internal:11434)
   c. Gets generated code from Ollama
   d. Returns code
   ↓
6. Response → API Gateway → Nginx → code-server → User
```

## Key Concepts

### 1. Docker Network Communication

All containers are on the same Docker network (`code-buddy-network`). They can reach each other using service names:

- `http://nginx` → Nginx container
- `http://api-gateway:9000` → API Gateway
- `http://agent-orchestrator:8000` → Agent Orchestrator
- `http://qdrant:6333` → Qdrant database

### 2. Host-Native Ollama

Ollama runs **on the Docker host**, not in a container. Containers access it via:

- `http://host.docker.internal:11434`

This special hostname is automatically resolved by Docker to the host machine's IP.

### 3. API Gateway Pattern

All services are accessed through the API Gateway:
- **External access**: `http://nginx/api/*` (port 80)
- **Internal access**: `http://api-gateway:9000/*` (port 9000)

The API Gateway:
- Routes requests to the right service
- Handles health checks
- Provides unified interface

### 4. RAG (Retrieval Augmented Generation) Flow

```
Code Indexer:
  1. Scans workspace for code files
  2. Parses code into chunks (functions, classes)
  3. Sends chunks to Ollama for embedding
  4. Stores embeddings in Qdrant

RAG Chat:
  1. User asks question
  2. Embeds question using Ollama
  3. Searches Qdrant for similar code
  4. Gets top matches as context
  5. Sends question + context to Ollama
  6. Returns answer with code references
```

## Service URLs from Code-Server Container

When you're inside the code-server container, use these URLs:

| Service | URL | Purpose |
|---------|-----|---------|
| API Gateway (via Nginx) | `http://nginx/api` | Main entry point |
| API Gateway (direct) | `http://api-gateway:9000` | Direct access |
| Ollama | `http://host.docker.internal:11434` | LLM inference |
| Qdrant | `http://qdrant:6333` | Vector database |

## Network Isolation

- **External ports** (exposed to host):
  - Port 80: Nginx (HTTP)
  - Port 443: Nginx (HTTPS, when configured)
  - Port ${CODE_SERVER_PORT}: Code-Server direct access

- **Internal ports** (Docker network only):
  - All other services use `expose` instead of `ports`
  - Only accessible from within Docker network
  - More secure, no port conflicts

## Data Flow Summary

```
User Action
    ↓
Code-Server Container
    ↓
Docker Network
    ↓
Nginx (reverse proxy)
    ↓
API Gateway (router)
    ↓
Specific Service (Agent/RAG/Indexer)
    ↓
Ollama (on host) or Qdrant (in container)
    ↓
Response flows back through same path
```

## Why This Architecture?

1. **Security**: Services not exposed to host network
2. **Isolation**: Each service in its own container
3. **Scalability**: Easy to add more services
4. **Simplicity**: Single entry point (API Gateway)
5. **Performance**: Ollama on host gets direct GPU access

## Troubleshooting Connections

### From Code-Server Container:

```bash
# Test API Gateway via Nginx
curl http://nginx/api/health

# Test API Gateway directly
curl http://api-gateway:9000/health

# Test Ollama
curl http://host.docker.internal:11434/api/tags

# Test Qdrant
curl http://qdrant:6333/collections
```

### From Host:

```bash
# Test via Nginx
curl http://localhost/api/health

# Test Code-Server directly
curl http://localhost:8081
```

## Summary

- **Code-Server** = Your IDE (browser-based VS Code)
- **Nginx** = Reverse proxy (routes traffic)
- **API Gateway** = Central hub (routes to services)
- **Services** = Agent Orchestrator, RAG Chat, Code Indexer, etc.
- **Ollama** = LLM server (runs on host, not in container)
- **Qdrant** = Vector database (stores code embeddings)

All communication happens via HTTP over the Docker network, with Ollama accessed through `host.docker.internal`.

