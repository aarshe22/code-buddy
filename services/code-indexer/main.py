"""
Code Indexer - Indexes codebase into Qdrant for RAG
"""
import os
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
import structlog
import httpx
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import hashlib

from code_parser import CodeParser
from embedding_generator import EmbeddingGenerator

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
WORKSPACE_PATH = os.getenv("WORKSPACE_PATH", "/app/workspace")
COLLECTION_NAME = "codebase"

# Initialize components
qdrant_host = QDRANT_HOST.replace("http://", "").split(":")[0]
qdrant_port = int(QDRANT_HOST.split(":")[-1]) if ":" in QDRANT_HOST and ":" in QDRANT_HOST.replace("http://", "") else 6333
qdrant_client = QdrantClient(host=qdrant_host, port=qdrant_port)
code_parser = CodeParser()
embedding_generator = EmbeddingGenerator(OLLAMA_HOST)

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(
    title="Code Indexer",
    description="Codebase Indexing Service for RAG",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class IndexRequest(BaseModel):
    project_path: Optional[str] = Field(default=None, description="Specific project path to index")
    force_reindex: bool = Field(default=False, description="Force reindexing even if already indexed")


class IndexStatus(BaseModel):
    status: str
    indexed_files: int
    total_files: int
    project_name: str


@app.on_event("startup")
async def startup():
    """Initialize Qdrant collection on startup"""
    try:
        # Check if collection exists
        collections = qdrant_client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        if COLLECTION_NAME not in collection_names:
            # Create collection with 768 dimensions (for nomic-embed-text model)
            # Adjust based on your embedding model
            qdrant_client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=768, distance=Distance.COSINE)
            )
            logger.info("Created Qdrant collection", collection=COLLECTION_NAME)
        else:
            logger.info("Qdrant collection already exists", collection=COLLECTION_NAME)
    except Exception as e:
        logger.error("Failed to initialize Qdrant", error=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        collections = qdrant_client.get_collections()
        return {
            "status": "healthy",
            "service": "code-indexer",
            "qdrant_connected": True,
            "collections": len(collections.collections)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "code-indexer",
            "error": str(e)
        }


@app.post("/index")
async def index_codebase(request: IndexRequest, background_tasks: BackgroundTasks):
    """Index codebase into Qdrant"""
    try:
        logger.info("Indexing requested", project_path=request.project_path, force=request.force_reindex)
        
        # Run indexing in background
        background_tasks.add_task(
            perform_indexing,
            request.project_path,
            request.force_reindex
        )
        
        return {
            "success": True,
            "message": "Indexing started in background",
            "project_path": request.project_path or "workspace"
        }
    except Exception as e:
        logger.error("Indexing failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/index/status")
async def get_index_status(project_path: Optional[str] = None):
    """Get indexing status"""
    try:
        workspace = Path(WORKSPACE_PATH)
        if project_path:
            workspace = workspace / project_path
        
        # Count files
        code_files = list(code_parser.find_code_files(workspace))
        total_files = len(code_files)
        
        # Count indexed files (simplified - in production, track this properly)
        # For now, return collection info
        collection_info = qdrant_client.get_collection(COLLECTION_NAME)
        indexed_count = collection_info.points_count if collection_info else 0
        
        return {
            "status": "indexed" if indexed_count > 0 else "not_indexed",
            "indexed_files": indexed_count,
            "total_files": total_files,
            "project_path": str(workspace.relative_to(Path(WORKSPACE_PATH))) if project_path else "workspace"
        }
    except Exception as e:
        logger.error("Failed to get status", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/index")
async def clear_index():
    """Clear all indexed code"""
    try:
        qdrant_client.delete_collection(COLLECTION_NAME)
        # Recreate collection
        qdrant_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE)
        )
        return {"success": True, "message": "Index cleared"}
    except Exception as e:
        logger.error("Failed to clear index", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


async def perform_indexing(project_path: Optional[str] = None, force_reindex: bool = False):
    """Perform the actual indexing"""
    try:
        workspace = Path(WORKSPACE_PATH)
        if project_path:
            workspace = workspace / project_path
        
        if not workspace.exists():
            logger.error("Workspace path does not exist", path=str(workspace))
            return
        
        logger.info("Starting indexing", workspace=str(workspace))
        
        # Find all code files
        code_files = list(code_parser.find_code_files(workspace))
        logger.info("Found code files", count=len(code_files))
        
        # Process files in batches
        batch_size = 10
        points = []
        
        for i, file_path in enumerate(code_files):
            try:
                # Parse code file
                chunks = code_parser.parse_file(file_path)
                
                for chunk in chunks:
                    # Generate embedding
                    embedding = await embedding_generator.generate_embedding(chunk["content"])
                    
                    # Create point ID from file path and chunk index
                    point_id = int(hashlib.md5(
                        f"{file_path}:{chunk['start_line']}:{chunk['end_line']}".encode()
                    ).hexdigest()[:8], 16)
                    
                    # Create point
                    point = PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload={
                            "file_path": str(file_path.relative_to(workspace)),
                            "content": chunk["content"],
                            "start_line": chunk["start_line"],
                            "end_line": chunk["end_line"],
                            "language": chunk.get("language", "unknown"),
                            "chunk_type": chunk.get("type", "code"),
                            "project_path": str(workspace.relative_to(Path(WORKSPACE_PATH))) if project_path else "workspace"
                        }
                    )
                    points.append(point)
                    
                    # Batch insert
                    if len(points) >= batch_size:
                        qdrant_client.upsert(collection_name=COLLECTION_NAME, points=points)
                        points = []
                        logger.info("Indexed batch", total=i+1, files=len(code_files))
                
            except Exception as e:
                logger.warning("Failed to index file", file=str(file_path), error=str(e))
                continue
        
        # Insert remaining points
        if points:
            qdrant_client.upsert(collection_name=COLLECTION_NAME, points=points)
        
        logger.info("Indexing complete", total_files=len(code_files))
        
    except Exception as e:
        logger.error("Indexing failed", error=str(e), exc_info=True)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)

