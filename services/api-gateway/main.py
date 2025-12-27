"""
API Gateway - Unified API interface for all services
"""
import os
from typing import Dict, Any, Optional
import structlog
import httpx

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Service URLs
AGENT_ORCHESTRATOR_URL = os.getenv("AGENT_ORCHESTRATOR_URL", "http://agent-orchestrator:8000")
RULES_ENGINE_URL = os.getenv("RULES_ENGINE_URL", "http://rules-engine:8001")
MCP_GITHUB_URL = os.getenv("MCP_GITHUB_URL", "http://mcp-github:3001")
MCP_GITLAB_URL = os.getenv("MCP_GITLAB_URL", "http://mcp-gitlab:3002")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")
CODE_INDEXER_URL = os.getenv("CODE_INDEXER_URL", "http://code-indexer:8002")
RAG_CHAT_URL = os.getenv("RAG_CHAT_URL", "http://rag-chat:8003")
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")
VSCODE_EXTENSION_URL = os.getenv("VSCODE_EXTENSION_URL", "http://vscode-extension-server:3003")
TERMINAL_AI_URL = os.getenv("TERMINAL_AI_URL", "http://terminal-ai:8004")

app = FastAPI(
    title="Dev Stack API Gateway",
    description="Unified API Gateway for AI Development Stack",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
@app.get("/api/health")
async def health_check():
    """Health check for all services"""
    services = {
        "api-gateway": "healthy",
        "agent-orchestrator": await check_service(f"{AGENT_ORCHESTRATOR_URL}/health"),
        "rules-engine": await check_service(f"{RULES_ENGINE_URL}/health"),
        "mcp-github": await check_service(f"{MCP_GITHUB_URL}/health"),
        "mcp-gitlab": await check_service(f"{MCP_GITLAB_URL}/health"),
        "ollama": await check_service(f"{OLLAMA_URL}/api/tags"),
        "code-indexer": await check_service(f"{CODE_INDEXER_URL}/health"),
        "rag-chat": await check_service(f"{RAG_CHAT_URL}/health"),
        "qdrant": await check_service(f"{QDRANT_URL}/"),
        "vscode-extension": await check_service(f"{VSCODE_EXTENSION_URL}/health"),
        "terminal-ai": await check_service(f"{TERMINAL_AI_URL}/health"),
    }
    
    all_healthy = all(status == "healthy" for status in services.values())
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "services": services
    }


async def check_service(url: str) -> str:
    """Check if a service is healthy"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            # Accept 200-299 status codes as healthy
            if 200 <= response.status_code < 300:
                return "healthy"
            return "unhealthy"
    except Exception as e:
        # Log the error for debugging (but don't fail the health check)
        logger.debug(f"Service check failed for {url}: {str(e)}")
        return "unreachable"


# Proxy endpoints for agent orchestrator
@app.post("/api/generate")
async def generate_code(request: Request):
    """Proxy to agent orchestrator generate endpoint"""
    body = await request.json()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{AGENT_ORCHESTRATOR_URL}/generate",
            json=body,
            timeout=300.0
        )
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code
        )


@app.post("/api/review")
async def review_code(request: Request):
    """Proxy to agent orchestrator review endpoint"""
    body = await request.json()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{AGENT_ORCHESTRATOR_URL}/review",
            json=body,
            timeout=120.0
        )
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code
        )


@app.post("/api/debug")
async def debug_code(request: Request):
    """Proxy to agent orchestrator debug endpoint"""
    body = await request.json()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{AGENT_ORCHESTRATOR_URL}/debug",
            json=body,
            timeout=300.0
        )
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code
        )


@app.post("/api/refactor")
async def refactor_code(request: Request):
    """Proxy to agent orchestrator refactor endpoint"""
    body = await request.json()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{AGENT_ORCHESTRATOR_URL}/refactor",
            json=body,
            timeout=300.0
        )
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code
        )


@app.post("/api/task")
async def execute_task(request: Request):
    """Proxy to agent orchestrator task endpoint"""
    body = await request.json()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{AGENT_ORCHESTRATOR_URL}/task",
            json=body,
            timeout=300.0
        )
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code
        )


# Rules engine endpoints
@app.get("/api/rules")
async def get_rules(language: Optional[str] = None):
    """Get coding rules"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{RULES_ENGINE_URL}/rules",
            params={"language": language} if language else {}
        )
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code
        )


# Ollama endpoints
@app.get("/api/models")
async def list_models():
    """List available Ollama models"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{OLLAMA_URL}/api/tags")
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code
        )


@app.post("/api/models/pull")
async def pull_model(request: Request):
    """Pull an Ollama model"""
    body = await request.json()
    model_name = body.get("model")
    if not model_name:
        raise HTTPException(status_code=400, detail="model parameter required")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{OLLAMA_URL}/api/pull",
            json={"name": model_name},
            timeout=3600.0  # Model pulls can take a long time
        )
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code
        )


# Code Indexing endpoints
@app.post("/api/index")
async def index_codebase(request: Request):
    """Index codebase into Qdrant"""
    body = await request.json()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{CODE_INDEXER_URL}/index",
            json=body,
            timeout=300.0
        )
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code
        )


@app.get("/api/index/status")
async def get_index_status(project_path: Optional[str] = None):
    """Get indexing status"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{CODE_INDEXER_URL}/index/status",
            params={"project_path": project_path} if project_path else {}
        )
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code
        )


@app.delete("/api/index")
async def clear_index():
    """Clear codebase index"""
    async with httpx.AsyncClient() as client:
        response = await client.delete(f"{CODE_INDEXER_URL}/index")
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code
        )


# RAG Chat endpoints
@app.post("/api/chat")
async def rag_chat(request: Request):
    """Chat with codebase using RAG"""
    body = await request.json()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{RAG_CHAT_URL}/chat",
            json=body,
            timeout=300.0
        )
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code
        )


@app.post("/api/search")
async def search_codebase(request: Request):
    """Search codebase"""
    body = await request.json()
    query = body.get("query")
    if not query:
        raise HTTPException(status_code=400, detail="query parameter required")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{RAG_CHAT_URL}/search",
            json=body
        )
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code
        )


# Code explanation endpoints
@app.post("/api/explain")
async def explain_code(request: Request):
    """Explain code in detail"""
    body = await request.json()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{AGENT_ORCHESTRATOR_URL}/explain",
            json=body,
            timeout=120.0
        )
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code
        )


# Test generation endpoints
@app.post("/api/generate-tests")
async def generate_tests(request: Request):
    """Generate unit tests for code"""
    body = await request.json()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{AGENT_ORCHESTRATOR_URL}/generate-tests",
            json=body,
            timeout=300.0
        )
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code
        )


# Documentation generation endpoints
@app.post("/api/generate-docs")
async def generate_docs(request: Request):
    """Generate documentation for code"""
    body = await request.json()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{AGENT_ORCHESTRATOR_URL}/generate-docs",
            json=body,
            timeout=300.0
        )
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code
        )


# VS Code Extension endpoints
@app.post("/api/completion")
async def code_completion(request: Request):
    """Get code completion suggestions"""
    body = await request.json()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{VSCODE_EXTENSION_URL}/api/completion",
            json=body,
            timeout=30.0
        )
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code
        )


@app.post("/api/inline-edit")
async def inline_edit(request: Request):
    """Inline code editing"""
    body = await request.json()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{VSCODE_EXTENSION_URL}/api/inline-edit",
            json=body,
            timeout=120.0
        )
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code
        )


@app.post("/api/explain-error")
async def explain_error(request: Request):
    """Explain error messages"""
    body = await request.json()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{VSCODE_EXTENSION_URL}/api/explain-error",
            json=body,
            timeout=120.0
        )
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code
        )


# Terminal AI endpoints
@app.post("/api/terminal/command")
async def suggest_command(request: Request):
    """Suggest terminal command"""
    body = await request.json()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{TERMINAL_AI_URL}/api/command",
            json=body,
            timeout=30.0
        )
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code
        )


@app.post("/api/terminal/explain")
async def explain_command(request: Request):
    """Explain terminal command"""
    body = await request.json()
    command = body.get("command")
    if not command:
        raise HTTPException(status_code=400, detail="command parameter required")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{TERMINAL_AI_URL}/api/explain-command",
            params={"command": command},
            timeout=30.0
        )
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code
        )


@app.post("/api/terminal/fix")
async def fix_command(request: Request):
    """Fix failed command"""
    body = await request.json()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{TERMINAL_AI_URL}/api/fix-command",
            json=body,
            timeout=30.0
        )
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)

