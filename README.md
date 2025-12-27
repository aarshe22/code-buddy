# Code Buddy - AI Development Stack

A complete, self-hosted AI development environment built around Ollama, providing code generation, debugging, refactoring, and intelligent code assistance - all running locally on your workstation.

## Features

- **Local-First**: All processing happens on your machine - no data leaves your workstation
- **Web-Based IDE**: Code-Server (VS Code in browser) with Cursor-like functionality
- **AI Agents**: Specialized agents for code generation, review, debugging, and refactoring
- **Advanced Reasoning**: Chain-of-thought and tree-of-thought reasoning capabilities
- **RAG (Retrieval Augmented Generation)**: Full codebase indexing with semantic search
- **Codebase Chat**: Chat with your codebase using natural language
- **Code Explanation**: Explain code in detail with examples
- **Test Generation**: Auto-generate comprehensive unit tests
- **Documentation Generation**: Auto-generate code documentation
- **Terminal AI**: AI assistance in terminal/command line
- **Error Explanation**: Inline error explanations and fixes
- **MCP Integration**: Native GitHub and GitLab integration via Model Context Protocol
- **Rules Engine**: Enforce coding standards and best practices
- **Docker-Based**: Clean, isolated, and portable deployment

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Nginx Reverse Proxy                  │
│                    (Port 80/443)                         │
└──────────────┬──────────────────────────────────────────┘
               │
    ┌──────────┴──────────┐
    │                     │
┌───▼────────┐    ┌───────▼────────┐
│ Code Server│    │  API Gateway   │
│  (Port 8080)│    │   (Port 9000)   │
└────────────┘    └───────┬────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
┌───────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
│   Agent      │  │   Rules     │  │   Qdrant   │
│ Orchestrator │  │   Engine    │  │  (Vector DB)│
│  (Port 8000) │  │  (Port 8001) │  │  (Port 6333)│
└───────┬──────┘  └──────────────┘  └──────┬──────┘
        │                                  │
        │ (via host.docker.internal)       │
        │                                  │
┌───────▼──────────────┐          ┌────────▼──────┐
│   Ollama (Host)      │          │ Code Indexer │
│   (Port 11434)       │          │  (Port 8002) │
│   No API Key         │          └──────────────┘
└──────────────────────┘
        │
    ┌───┴────┬──────────────┐
    │        │              │
┌───▼───┐ ┌──▼────┐  ┌──────▼────┐
│ MCP   │ │ MCP   │  │ Reasoning │
│GitHub │ │GitLab │  │  Engine   │
│:3001  │ │:3002  │  └───────────┘
└───────┘ └───────┘
```

## Components

### 1. Ollama (Host-Native)
**Ollama runs natively on the Docker host** (not in a container). It must be installed and running on the host system, listening on `0.0.0.0:11434` with no API key required. Services access Ollama via `host.docker.internal:11434`.

- Supports GPU acceleration (NVIDIA)
- Hosts coding, reasoning, and embedding models
- No API key required
- Listens on all interfaces (0.0.0.0)

### 2. Code-Server
Web-based VS Code IDE. Accessible via browser, fully functional code editor. Accessible on all host IP addresses via configurable port (default: 8080).

### 3. Agent Orchestrator
Main service coordinating AI agents:
- **Code Generator**: Generate code from natural language
- **Code Reviewer**: Review code for issues and improvements
- **Debugger**: Debug code issues systematically
- **Refactorer**: Refactor code for better quality

### 4. Reasoning Engine
Advanced reasoning capabilities:
- Chain-of-Thought reasoning
- Tree-of-Thought reasoning
- Iterative refinement

### 5. MCP Servers
Model Context Protocol servers for:
- GitHub integration (read repos, push/pull)
- GitLab integration (read repos, push/pull)

### 6. Qdrant Vector Database
Vector database for code embeddings:
- Semantic code search
- Fast similarity queries
- Persistent storage

### 7. Code Indexer
Indexes codebase into Qdrant:
- Parses code into semantic chunks
- Generates embeddings using Ollama
- Indexes for RAG retrieval

### 8. RAG Chat Service
Codebase-aware chat:
- Natural language queries
- Semantic code search
- Context-aware responses

### 9. Rules Engine
Coding standards and rules management:
- Language-specific rules
- Custom rule definitions
- Rule enforcement

### 10. API Gateway
Unified API interface for all services.

## Prerequisites

### System Requirements

- **OS**: Ubuntu 20.04+ or similar Linux distribution
- **CPU**: 8+ cores (64 cores recommended)
- **RAM**: 64GB (256GB recommended)
- **GPU**: NVIDIA GPU with 24GB+ VRAM (96GB recommended)
- **Storage**: 200GB+ free space (SSD recommended)
- **Docker**: 20.10+
- **Docker Compose**: 2.0+

### Required Software

1. **Docker and Docker Compose**
   ```bash
   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   
   # Install Docker Compose plugin
   sudo apt-get update
   sudo apt-get install docker-compose-plugin
   ```

2. **NVIDIA Container Toolkit** (for GPU support)
   ```bash
   distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
   curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
   curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
   sudo apt-get update
   sudo apt-get install -y nvidia-container-toolkit
   sudo nvidia-ctk runtime configure --runtime=docker
   sudo systemctl restart docker
   ```

3. **Ollama** (must be installed on host, not in container)
   ```bash
   # Install Ollama
   curl -fsSL https://ollama.com/install.sh | sh
   
   # Configure to listen on all interfaces
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
   
   sudo systemctl daemon-reload
   sudo systemctl enable ollama
   sudo systemctl start ollama
   
   # Verify
   curl http://localhost:11434/api/tags
   ```

## Installation

### 1. Clone and Setup

```bash
cd /home/aarshe/code-buddy
chmod +x setup.sh
./setup.sh
```

### 2. Configure Environment

Edit `.env` file:

```bash
nano .env
```

Required settings:
- `CODE_SERVER_PASSWORD`: Set a strong password for web IDE
- `CODE_SERVER_PORT`: Port for direct Code-Server access (default: 8080)

Optional settings:
- `GITHUB_TOKEN`: GitHub personal access token (for GitHub integration)
- `GITLAB_TOKEN`: GitLab personal access token (for GitLab integration)
- `OLLAMA_CODING_MODEL`: Coding model (default: deepseek-coder:33b)
- `OLLAMA_REASONING_MODEL`: Reasoning model (default: qwen2.5:72b)
- `OLLAMA_EMBEDDING_MODEL`: Embedding model (default: nomic-embed-text)

### 3. Build and Start Services

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

### 4. Pull Ollama Models (on Host)

For systems with 96GB VRAM, recommended models:

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

**Model Recommendations by Hardware:**

- **96GB VRAM**: `deepseek-coder:33b`, `qwen2.5:72b`, `nomic-embed-text`
- **48GB VRAM**: `codellama:34b`, `llama3.1:70b`, `nomic-embed-text`
- **24GB VRAM**: `codellama:13b`, `llama3.1:8b`, `nomic-embed-text`
- **12GB VRAM**: `codellama:7b`, `llama3.1:3b`, `nomic-embed-text`

### 5. Access the IDE

- **Via Nginx** (recommended): `http://<host-ip>` (port 80)
- **Direct access**: `http://<host-ip>:${CODE_SERVER_PORT:-8080}` (default port 8080)
- **Accessible on all host IP addresses**

Login with your password from the `.env` file.

## Usage

### Index Your Codebase (RAG)

Before using RAG features, index your codebase:

```bash
# Index entire workspace
curl -X POST http://localhost/api/index \
  -H "Content-Type: application/json" \
  -d '{}'

# Index specific project
curl -X POST http://localhost/api/index \
  -H "Content-Type: application/json" \
  -d '{"project_path": "my-project"}'

# Check indexing status
curl http://localhost/api/index/status

# Force reindex
curl -X POST http://localhost/api/index \
  -H "Content-Type: application/json" \
  -d '{"force_reindex": true}'
```

### Chat with Your Codebase

Ask questions about your code:

```bash
curl -X POST http://localhost/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How does authentication work in this codebase?",
    "project_path": "my-project",
    "max_results": 5
  }'
```

### Search Codebase

Semantically search your code:

```bash
curl -X POST http://localhost/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "user authentication function",
    "project_path": "my-project",
    "limit": 10
  }'
```

### Code Generation

Generate code from natural language (automatically uses RAG for context):

```bash
curl -X POST http://localhost/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a REST API endpoint for user authentication",
    "language": "python",
    "output_path": "api/auth.py",
    "context": {
      "project_path": "my-project"
    }
  }'
```

### Code Review

Review code for issues:

```bash
curl -X POST http://localhost/api/review \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "src/main.py",
    "context": {
      "project_path": "my-project"
    }
  }'
```

### Debug Code

Debug code issues:

```bash
curl -X POST http://localhost/api/debug \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "src/main.py",
    "error_message": "IndexError: list index out of range",
    "context": {
      "project_path": "my-project"
    }
  }'
```

### Refactor Code

Refactor code for improvement:

```bash
curl -X POST http://localhost/api/refactor \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "src/main.py",
    "refactor_type": "extract_function",
    "target": "complex_function",
    "context": {
      "project_path": "my-project"
    }
  }'
```

### General Task

Execute a general task (auto-selects appropriate agent):

```bash
curl -X POST http://localhost/api/task \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Add error handling to the authentication function",
    "context": {
      "file_path": "api/auth.py",
      "project_path": "my-project"
    }
  }'
```

## GitHub/GitLab Integration

### Setup

1. Create a GitHub personal access token with `repo` scope
2. Create a GitLab personal access token with `api` scope
3. Add tokens to `.env` file:
   ```
   GITHUB_TOKEN=your_token_here
   GITLAB_TOKEN=your_token_here
   ```
4. Restart services:
   ```bash
   docker compose restart mcp-github mcp-gitlab
   ```

### Usage

The agents automatically use repository context when you provide a `repository_url`:

```json
{
  "prompt": "Add a new feature based on the existing codebase",
  "repository_url": "https://github.com/owner/repo",
  "context_files": ["src/main.py", "src/utils.py"]
}
```

## Rules Engine

### Default Rules

The system includes default rules for:
- Security (no hardcoded secrets)
- Error handling
- Code quality
- Documentation

### Custom Rules

Add custom rules in `rules/` directory:

```yaml
# rules/custom.yaml
language: python
rules:
  - name: "custom_rule"
    description: "Your custom rule description"
    severity: "high"
    enabled: true
```

### Managing Rules

```bash
# Get all rules
curl http://localhost/api/rules

# Get rules for specific language
curl http://localhost/api/rules?language=python

# Reload rules
curl -X POST http://localhost/api/rules/reload
```

## Network & Security

### Port Configuration

**External Ports (Exposed to Host):**
- **Port 80**: Nginx (HTTP access to web IDE and API)
- **Port 443**: Nginx (HTTPS access, when configured)
- **Port ${CODE_SERVER_PORT:-8080}**: Code-Server direct access (all host IPs)

**Internal Ports (Docker Network Only):**
All other services use internal Docker network for communication:
- API Gateway: 9000
- Agent Orchestrator: 8000
- Rules Engine: 8001
- Code Indexer: 8002
- RAG Chat: 8003
- Terminal AI: 8004
- MCP GitHub: 3001
- MCP GitLab: 3002
- Qdrant: 6333, 6334

### Security Features

- All services run in isolated Docker containers
- Internal services not exposed to host network
- No external network access required (except for model downloads)
- GitHub/GitLab tokens stored in `.env` (not in code)
- Workspace isolated from host system
- Password authentication for Code-Server

## Data Persistence

All configuration and ephemeral data is persisted in Docker named volumes:

- **Ollama**: Models stored in `~/.ollama/` on host
- **Code-Server**: Extensions, settings, and logs preserved
- **Agent Data**: Agent state, cache, and logs persist
- **Qdrant**: Vector database and indexes persist
- **All Services**: Logs, cache, and state data persist

### Backup & Restore

```bash
# Backup all volumes
./scripts/backup-volumes.sh

# Restore from backup
./scripts/restore-volumes.sh backups/20240101_120000

# List volumes
./scripts/list-volumes.sh
```

## Troubleshooting

### GPU Not Detected

```bash
# Check NVIDIA runtime
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi

# Install NVIDIA Container Toolkit
# See: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html
```

### Ollama Not Accessible from Containers

1. Verify Ollama is running on host:
   ```bash
   curl http://localhost:11434/api/tags
   ```

2. Check OLLAMA_HOST is set:
   ```bash
   echo $OLLAMA_HOST
   # Should output: 0.0.0.0:11434
   ```

3. Test from container:
   ```bash
   docker run --rm --add-host=host.docker.internal:host-gateway \
     curlimages/curl:latest \
     curl http://host.docker.internal:11434/api/tags
   ```

### Out of Memory

- Use smaller models
- Reduce `OLLAMA_KEEP_ALIVE` in `.env`
- Limit concurrent requests
- Check GPU memory: `nvidia-smi`

### Services Not Starting

```bash
# Check logs
docker compose logs

# Restart services
docker compose restart

# Rebuild images
docker compose build --no-cache
```

### Port Conflicts

```bash
# Check what's using ports
sudo lsof -i :80
sudo lsof -i :8080

# Change ports in .env or docker-compose.yml
```

## Performance Tuning

### For High-End Systems (96GB VRAM)

1. **Model Selection**: Use 70B-90B parameter models
2. **Batch Size**: Increase in Ollama config
3. **Keep Alive**: Set to 24h to keep models loaded
4. **Concurrent Requests**: Can handle multiple simultaneous requests

### Optimization Tips

- Keep models loaded in memory (`OLLAMA_KEEP_ALIVE=24h`)
- Use quantized models for faster inference
- Enable GPU acceleration
- Use SSD storage for workspace
- Monitor GPU usage: `nvidia-smi`

## Development

### Project Structure

```
code-buddy/
├── docker-compose.yml          # Service orchestration
├── services/
│   ├── agent-orchestrator/    # Main agent service
│   ├── mcp-github/            # GitHub MCP server
│   ├── mcp-gitlab/            # GitLab MCP server
│   ├── rules-engine/          # Rules management
│   ├── api-gateway/           # API gateway
│   ├── code-indexer/          # Code indexing service
│   ├── rag-chat/              # RAG chat service
│   ├── terminal-ai/           # Terminal AI assistant
│   └── vscode-extension-server/ # VS Code extension server
├── nginx/                      # Reverse proxy config
├── rules/                      # Coding rules
├── workspace/                  # Your code workspace
└── code-server-config/        # Code-Server settings
```

### Adding New Agents

1. Create agent class in `services/agent-orchestrator/agents/`
2. Extend `BaseAgent` class
3. Register in `main.py`

### Adding New MCP Servers

1. Create new service in `services/`
2. Implement MCP protocol
3. Add to `docker-compose.yml`

## License

All components are open source and free:
- Ollama: MIT
- Code-Server: MIT
- FastAPI: MIT
- All custom code: MIT

## Support

For issues, check:
1. Service logs: `docker compose logs <service-name>`
2. Health endpoint: `http://localhost/api/health`
3. Ollama status: `ollama list` (on host)

## Roadmap

- [x] Advanced codebase indexing (RAG)
- [x] Multi-model support
- [ ] Fine-tuning interface
- [ ] Team collaboration features
- [ ] Custom agent creation UI
- [ ] Performance monitoring dashboard
