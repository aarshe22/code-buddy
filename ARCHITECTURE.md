# Architecture Documentation

## System Overview

The Dev Stack is a comprehensive, self-hosted AI development environment designed to run entirely on your local workstation. All components are containerized using Docker for isolation and portability.

## Component Architecture

### 1. Frontend Layer

#### Nginx Reverse Proxy
- **Purpose**: Routes traffic to appropriate services
- **Port**: 80 (HTTP)
- **Responsibilities**:
  - Route `/` to Code-Server (Web IDE)
  - Route `/api/*` to API Gateway
  - SSL termination (when configured)
  - Load balancing (future)

#### Code-Server (Web IDE)
- **Purpose**: Browser-based VS Code IDE
- **Port**: 8080 (internal), 80 (via Nginx), ${CODE_SERVER_PORT:-8080} (direct, all host IPs)
- **Features**:
  - Full VS Code functionality
  - Extension support
  - Terminal access
  - Git integration
  - File browser

### 2. API Layer

#### API Gateway
- **Purpose**: Unified API interface
- **Port**: 9000
- **Responsibilities**:
  - Route requests to appropriate services
  - Health checking
  - Request/response transformation
  - Rate limiting (future)
  - Authentication (future)

### 3. Core Services

#### Agent Orchestrator
- **Purpose**: Main AI agent coordination service
- **Port**: 8000
- **Components**:
  - **Code Generator Agent**: Generates code from natural language
  - **Code Reviewer Agent**: Reviews code for issues
  - **Debugger Agent**: Debugs code problems
  - **Refactorer Agent**: Refactors code for improvement
- **Capabilities**:
  - Natural language task understanding
  - Agent selection
  - Task execution
  - Result aggregation

#### Reasoning Engine
- **Purpose**: Advanced reasoning capabilities
- **Integration**: Embedded in Agent Orchestrator
- **Methods**:
  - Chain-of-Thought reasoning
  - Tree-of-Thought reasoning
  - Iterative refinement

#### Rules Engine
- **Purpose**: Coding standards management
- **Port**: 8001
- **Features**:
  - Rule storage and retrieval
  - Language-specific rules
  - Rule validation
  - Dynamic rule loading

### 4. MCP Servers

#### MCP GitHub Server
- **Purpose**: GitHub repository integration
- **Port**: 3001
- **Capabilities**:
  - Read repository information
  - Read file contents
  - Push changes
  - Pull repository contents
  - List repository structure

#### MCP GitLab Server
- **Purpose**: GitLab repository integration
- **Port**: 3002
- **Capabilities**:
  - Read repository information
  - Read file contents
  - Push changes
  - Pull repository contents
  - List repository structure

### 5. AI Layer

#### Ollama (Host-Native)
- **Purpose**: Local LLM inference
- **Deployment**: Runs natively on Docker host (not in container)
- **Port**: 11434 (listens on 0.0.0.0)
- **Security**: No API key required
- **Features**:
  - GPU acceleration (NVIDIA)
  - Multiple model support (coding, reasoning, embedding)
  - Model management
  - Streaming responses
  - Direct host access for optimal performance
- **Access**: Services connect via `host.docker.internal:11434`
- **Models**: Hosts coding models (deepseek-coder:33b), reasoning models (llama3.2:90b), and embedding models (nomic-embed-text)

## Data Flow

### Code Generation Request

```
User → Nginx → API Gateway → Agent Orchestrator
                                    ↓
                            Code Generator Agent
                                    ↓
                            Reasoning Engine (if complex)
                                    ↓
                            Ollama (LLM Inference)
                                    ↓
                            Rules Engine (validation)
                                    ↓
                            Workspace Manager (save file)
                                    ↓
                            Response → User
```

### Code Review Request

```
User → Nginx → API Gateway → Agent Orchestrator
                                    ↓
                            Code Reviewer Agent
                                    ↓
                            Workspace Manager (read file)
                                    ↓
                            Rules Engine (get rules)
                                    ↓
                            Ollama (analysis)
                                    ↓
                            Response → User
```

### Repository Context Request

```
Agent → MCP Client → MCP GitHub/GitLab Server
                            ↓
                    GitHub/GitLab API
                            ↓
                    Repository Data
                            ↓
                    Agent (context)
```

## Storage Architecture

### Volumes

1. **ollama-data**: Model storage and cache
2. **code-server-data**: Code-Server settings and extensions
3. **agent-data**: Agent state and cache
4. **mcp-data**: MCP server data
5. **rules-data**: Rules engine data
6. **workspace**: User code (bind mount)

### Workspace Structure

```
workspace/
├── user-code/          # Your projects
├── generated/          # AI-generated code
└── .git/               # Git repositories
```

## Network Architecture

### Docker Network

All services run on `dev-stack-network` (bridge network):
- Internal service-to-service communication
- Isolated from host network
- DNS resolution by service name

### Port Mapping

- **80**: Nginx (HTTP)
- **443**: Nginx (HTTPS, when configured)
- **8080**: Code-Server (direct access)
- **9000**: API Gateway (direct access)
- **11434**: Ollama (direct access)

Internal ports (not exposed):
- **8000**: Agent Orchestrator
- **8001**: Rules Engine
- **3001**: MCP GitHub
- **3002**: MCP GitLab

## Security Architecture

### Isolation

- Each service runs in its own container
- Network isolation via Docker network
- Volume isolation per service
- No root access required (except Docker)

### Secrets Management

- Environment variables in `.env` file
- Not committed to version control
- Tokens passed via environment variables
- No secrets in code

### Data Privacy

- All processing local
- No external API calls (except GitHub/GitLab when configured)
- Models run entirely on local GPU
- No telemetry or tracking

## Scalability

### Current Design

- Single-node deployment
- All services on one machine
- Vertical scaling (more GPU/RAM)

### Future Enhancements

- Multi-node deployment
- Service replication
- Load balancing
- Distributed model serving

## Performance Optimization

### GPU Utilization

- Ollama uses GPU for inference
- Models kept in GPU memory (keep_alive)
- Batch processing support

### Caching

- Model responses cached
- Repository context cached
- Rules cached in memory

### Resource Management

- Memory limits per container
- CPU limits per container
- GPU allocation per container

## Monitoring

### Health Checks

- Service health endpoints
- Docker health checks
- API Gateway health aggregation

### Logging

- Structured logging (JSON)
- Per-service logs
- Centralized log collection (future)

## Extension Points

### Adding New Agents

1. Create agent class extending `BaseAgent`
2. Implement `execute_task` method
3. Register in Agent Orchestrator
4. Add API endpoint

### Adding New MCP Servers

1. Create MCP server service
2. Implement MCP protocol
3. Add to docker-compose.yml
4. Update MCP Client

### Adding New Rules

1. Create YAML file in `rules/` directory
2. Define rules in YAML format
3. Rules Engine auto-loads

## Deployment Scenarios

### Development

- All services running
- Hot-reload for code changes
- Debug logging enabled

### Production

- Optimized builds
- Resource limits
- Health monitoring
- Backup strategies

## Dependencies

### External

- Docker & Docker Compose
- NVIDIA Container Toolkit (for GPU)
- Internet (for initial model download)

### Internal

- Python 3.11+ (services)
- Node.js 20+ (MCP servers)
- Ollama (AI inference)
- Nginx (reverse proxy)

## Future Enhancements

- [ ] Multi-model support (different models for different tasks)
- [ ] Fine-tuning interface
- [ ] Advanced codebase indexing
- [ ] Team collaboration
- [ ] Custom agent creation UI
- [ ] Performance monitoring dashboard
- [ ] Model fine-tuning pipeline
- [ ] Codebase semantic search
- [ ] Automated testing integration
- [ ] CI/CD integration

