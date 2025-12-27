"""
RAG Chat Service - Codebase-aware chat with Retrieval Augmented Generation
"""
import os
from typing import List, Dict, Any, Optional
import structlog
import httpx
from qdrant_client import QdrantClient

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

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

# Configuration
QDRANT_HOST = os.getenv("QDRANT_HOST", "http://localhost:6333")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
COLLECTION_NAME = "codebase"

# Initialize Qdrant client
qdrant_host = QDRANT_HOST.replace("http://", "").split(":")[0]
qdrant_port = int(QDRANT_HOST.split(":")[-1]) if ":" in QDRANT_HOST else 6333
qdrant_client = QdrantClient(host=qdrant_host, port=qdrant_port)

app = FastAPI(
    title="RAG Chat",
    description="Codebase-aware Chat with RAG",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str = Field(..., description="User message")
    project_path: Optional[str] = Field(default=None, description="Specific project to query")
    max_results: int = Field(default=5, description="Maximum number of code chunks to retrieve")
    temperature: float = Field(default=0.7, description="LLM temperature")
    model: Optional[str] = Field(default=None, description="Ollama model to use")


class ChatResponse(BaseModel):
    response: str
    sources: List[Dict[str, Any]]
    context_used: bool


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        collections = qdrant_client.get_collections()
        return {
            "status": "healthy",
            "service": "rag-chat",
            "qdrant_connected": True
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "rag-chat",
            "error": str(e)
        }


@app.post("/chat")
async def chat(request: ChatRequest):
    """Chat with codebase using RAG"""
    try:
        logger.info("Chat request", message=request.message[:100], project=request.project_path)
        
        # Generate embedding for query
        query_embedding = await generate_query_embedding(request.message)
        
        # Search Qdrant for relevant code
        search_results = qdrant_client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_embedding,
            limit=request.max_results,
            query_filter={"must": [{"key": "project_path", "match": {"value": request.project_path}}]} if request.project_path else None
        )
        
        # Build context from search results
        context_chunks = []
        sources = []
        
        for result in search_results:
            payload = result.payload
            context_chunks.append({
                "file": payload.get("file_path", "unknown"),
                "content": payload.get("content", ""),
                "lines": f"{payload.get('start_line', 0)}-{payload.get('end_line', 0)}"
            })
            sources.append({
                "file_path": payload.get("file_path", "unknown"),
                "start_line": payload.get("start_line", 0),
                "end_line": payload.get("end_line", 0),
                "language": payload.get("language", "unknown"),
                "score": result.score
            })
        
        # Build prompt with context
        context_text = "\n\n".join([
            f"File: {chunk['file']} (lines {chunk['lines']})\n{chunk['content']}"
            for chunk in context_chunks
        ])
        
        system_prompt = """You are an expert code assistant with access to the codebase context.
Answer questions about the code, explain how things work, and help with development tasks.
Use the provided code context to give accurate, specific answers.
If the context doesn't contain relevant information, say so."""
        
        user_prompt = f"""Context from codebase:

{context_text}

User question: {request.message}

Provide a helpful answer based on the codebase context."""
        
        # Call Ollama for response
        model = request.model or "llama3.2:90b"
        response_text = await call_ollama(
            prompt=user_prompt,
            system_prompt=system_prompt,
            model=model,
            temperature=request.temperature
        )
        
        return {
            "response": response_text,
            "sources": sources,
            "context_used": len(sources) > 0
        }
    
    except Exception as e:
        logger.error("Chat failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search")
async def search_code(request: Request):
    """Search codebase for relevant code"""
    try:
        body = await request.json()
        query = body.get("query")
        project_path = body.get("project_path")
        limit = int(body.get("limit", 10))
        
        if not query:
            raise HTTPException(status_code=400, detail="query parameter required")
    """Search codebase for relevant code"""
    try:
        # Generate embedding for query
        query_embedding = await generate_query_embedding(query)
        
        # Search Qdrant
        search_results = qdrant_client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_embedding,
            limit=limit,
            query_filter={"must": [{"key": "project_path", "match": {"value": project_path}}]} if project_path else None
        )
        
        results = []
        for result in search_results:
            payload = result.payload
            results.append({
                "file_path": payload.get("file_path", "unknown"),
                "content": payload.get("content", ""),
                "start_line": payload.get("start_line", 0),
                "end_line": payload.get("end_line", 0),
                "language": payload.get("language", "unknown"),
                "score": result.score
            })
        
        return {"results": results, "count": len(results)}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Search failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def generate_query_embedding(text: str) -> List[float]:
    """Generate embedding for query text"""
    try:
        url = f"{OLLAMA_HOST}/api/embeddings"
        payload = {
            "model": "nomic-embed-text",
            "prompt": text[:8192]
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            return result.get("embedding", [])
    except Exception as e:
        logger.error("Failed to generate query embedding", error=str(e))
        raise


async def call_ollama(prompt: str, system_prompt: str, model: str, temperature: float = 0.7) -> str:
    """Call Ollama API"""
    try:
        url = f"{OLLAMA_HOST}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": 4096
            }
        }
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
    except Exception as e:
        logger.error("Ollama API call failed", error=str(e))
        raise


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)

