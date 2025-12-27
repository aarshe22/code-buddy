# AI Development Stack

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

**See [COMPARISON.md](COMPARISON.md) for feature comparison with Cursor AI and Claude Code.**

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Nginx Reverse Proxy                  │
│                    (Port 80/443)                        │
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
┌───────▼──────┐  ┌──────▼──────┐
│   Agent      │  │   Rules     │
│ Orchestrator │  │   Engine    │
│  (Port 8000) │  │  (Port 8001) │
└───────┬──────┘  └──────────────┘
        │
        │ (via host.docker.internal)
        │
┌───────▼──────────────┐
│   Ollama (Host)      │
│   (Port 11434)       │
│   No API Key         │
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

See [MODEL_RECOMMENDATIONS.md](MODEL_RECOMMENDATIONS.md) for recommended models for your hardware.

### 2. Code-Server
Web-based VS Code IDE. Accessible via browser, fully functional code editor.

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

- Ubuntu Linux (tested on 22.04+)
- **Ollama installed and running on the host** (listening on 0.0.0.0:11434)
- Docker and Docker Compose
- NVIDIA GPU with drivers (for GPU acceleration)
- At least 100GB free disk space
- 256GB RAM (recommended for large models)

### Installing Ollama on Host

See [OLLAMA_SETUP.md](OLLAMA_SETUP.md) for complete setup instructions.

Quick setup:
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Configure to listen on all interfaces (no API key required)
export OLLAMA_HOST=0.0.0.0:11434

# Start Ollama service (or configure as systemd service)
ollama serve
```

Ensure Ollama is running and accessible before starting the Docker stack.

## Quick Start

1. **Clone and setup**:
```bash
cd /home/aarshe/dev-stack
chmod +x setup.sh
./setup.sh
```

2. **Configure environment**:
Edit `.env` file and set:
- `CODE_SERVER_PASSWORD`: Password for web IDE
- `GITHUB_TOKEN`: GitHub personal access token (optional)
- `GITLAB_TOKEN`: GitLab personal access token (optional)

3. **Start services**:
```bash
docker compose up -d
```

4. **Pull Ollama models** (on the host):
```bash
# Pull recommended models for your hardware
ollama pull deepseek-coder:33b    # Coding model
ollama pull llama3.2:90b          # Reasoning model
ollama pull nomic-embed-text      # Embedding model

# Verify installation
ollama list
```

See [MODEL_RECOMMENDATIONS.md](MODEL_RECOMMENDATIONS.md) for complete model recommendations.

5. **Access the IDE**:
- Via Nginx (recommended): `http://<host-ip>` (port 80)
- Direct access: `http://<host-ip>:${CODE_SERVER_PORT:-8080}` (default port 8080)
- Accessible on all host IP addresses

Login with your password from the `.env` file.

## Usage

### Index Your Codebase (RAG)

Before using RAG features, index your codebase:

```bash
# Index entire workspace
curl -X POST http://localhost/api/index \
  -H "Content-Type: application/json" \
  -d '{}'

# Check indexing status
curl http://localhost/api/index/status
```

### Chat with Your Codebase

Ask questions about your code:

```bash
curl -X POST http://localhost/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How does authentication work in this codebase?",
    "project_path": "my-project"
  }'
```

### Search Codebase

Semantically search your code:

```bash
curl -X POST http://localhost/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "user authentication function",
    "limit": 10
  }'
```

See [RAG_GUIDE.md](RAG_GUIDE.md) for complete RAG documentation.

### Code Generation

Generate code from natural language (automatically uses RAG for context):

```bash
curl -X POST http://localhost/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a REST API endpoint for user authentication",
    "language": "python",
    "output_path": "api/auth.py"
  }'
```

### Code Review

Review code for issues:

```bash
curl -X POST http://localhost/api/review \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "src/main.py"
  }'
```

### Debug Code

Debug code issues:

```bash
curl -X POST http://localhost/api/debug \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "src/main.py",
    "error_message": "IndexError: list index out of range"
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
    "target": "complex_function"
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
      "file_path": "api/auth.py"
    }
  }'
```

## GitHub/GitLab Integration

### Setup

1. Create a GitHub personal access token with `repo` scope
2. Create a GitLab personal access token with `api` scope
3. Add tokens to `.env` file

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

## Model Selection

With 96GB VRAM, you can run large models:

### Recommended Models

- **llama3.2:90b** - Best quality, requires ~50GB VRAM
- **llama3.2:70b** - High quality, requires ~40GB VRAM
- **codellama:34b** - Code-focused, requires ~20GB VRAM
- **deepseek-coder:33b** - Excellent for code, requires ~20GB VRAM

### Pulling Models

```bash
ollama pull <model-name>  # Run on host
```

### Changing Model

Edit `services/agent-orchestrator/agents/base_agent.py` and change the `model` variable.

## Development

### Project Structure

```
dev-stack/
├── docker compose.yml          # Service orchestration
├── services/
│   ├── agent-orchestrator/    # Main agent service
│   ├── mcp-github/            # GitHub MCP server
│   ├── mcp-gitlab/            # GitLab MCP server
│   ├── rules-engine/          # Rules management
│   └── api-gateway/           # API gateway
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
3. Add to `docker compose.yml`

## Troubleshooting

### GPU Not Detected

```bash
# Check NVIDIA runtime
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi

# Install NVIDIA Container Toolkit
# See: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html
```

### Out of Memory

- Use smaller models
- Reduce `OLLAMA_KEEP_ALIVE` in `.env`
- Limit concurrent requests

### Services Not Starting

```bash
# Check logs
docker compose logs

# Restart services
docker compose restart

# Rebuild images
docker compose build --no-cache
```

## Performance Tuning

### For 96GB VRAM System

1. **Model Selection**: Use 70B-90B parameter models
2. **Batch Size**: Increase in Ollama config
3. **Keep Alive**: Set to 24h to keep models loaded
4. **Concurrent Requests**: Can handle multiple simultaneous requests

### Optimization Tips

- Keep models loaded in memory (`OLLAMA_KEEP_ALIVE=24h`)
- Use quantized models for faster inference
- Enable GPU acceleration
- Use SSD storage for workspace

## Data Persistence

All configuration and ephemeral data is persisted in Docker named volumes:

- **Models & Cache**: Ollama models and cache persist across rebuilds
- **Code-Server**: Extensions, settings, and logs are preserved
- **Agent Data**: Agent state, cache, and logs persist
- **Qdrant**: Vector database and indexes persist
- **All Services**: Logs, cache, and state data persist

See [PERSISTENCE.md](PERSISTENCE.md) for complete details.

### Backup & Restore

```bash
# Backup all volumes
./scripts/backup-volumes.sh

# Restore from backup
./scripts/restore-volumes.sh backups/20240101_120000

# List volumes
./scripts/list-volumes.sh
```

## Security

- All services run in isolated Docker containers
- No external network access required (except for model downloads)
- GitHub/GitLab tokens stored in `.env` (not in code)
- Workspace isolated from host system

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

## RAG Features

The stack includes a complete RAG system:

- **Codebase Indexing**: Automatically index your entire codebase
- **Semantic Search**: Find code by meaning, not just keywords
- **Context-Aware Agents**: Agents automatically use codebase context
- **Codebase Chat**: Ask questions about your code in natural language

See [RAG_GUIDE.md](RAG_GUIDE.md) for detailed documentation.

## Roadmap

- [x] Advanced codebase indexing (RAG)
- [ ] Multi-model support (run different models for different tasks)
- [ ] Fine-tuning interface
- [ ] Team collaboration features
- [ ] Custom agent creation UI
- [ ] Performance monitoring dashboard

