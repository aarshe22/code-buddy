# RAG (Retrieval Augmented Generation) Guide

## Overview

Code Buddy includes a complete RAG (Retrieval Augmented Generation) system powered by Qdrant vector database. This allows you to:

- **Index your entire codebase** for semantic search
- **Chat with your codebase** using natural language
- **Get relevant code context** automatically in agent operations
- **Search code semantically** instead of just text matching

## Architecture

```
Codebase → Code Indexer → Embeddings (Ollama) → Qdrant (Vector DB)
                                                         ↓
User Query → RAG Chat → Embedding → Qdrant Search → Context → LLM → Response
```

## Components

### 1. Qdrant Vector Database
- Stores code embeddings
- Enables semantic search
- Port: 6333 (HTTP), 6334 (gRPC)

### 2. Code Indexer
- Scans workspace for code files
- Parses code into semantic chunks
- Generates embeddings using Ollama
- Indexes into Qdrant
- Port: 8002

### 3. RAG Chat Service
- Handles codebase queries
- Retrieves relevant code context
- Generates responses with context
- Port: 8003

## Quick Start

### 1. Index Your Codebase

```bash
# Index entire workspace
curl -X POST http://localhost/api/index \
  -H "Content-Type: application/json" \
  -d '{}'

# Index specific project
curl -X POST http://localhost/api/index \
  -H "Content-Type: application/json" \
  -d '{"project_path": "my-project"}'

# Force reindex
curl -X POST http://localhost/api/index \
  -H "Content-Type: application/json" \
  -d '{"force_reindex": true}'
```

### 2. Check Indexing Status

```bash
# Check status
curl http://localhost/api/index/status

# Check specific project
curl "http://localhost/api/index/status?project_path=my-project"
```

### 3. Chat with Your Codebase

```bash
curl -X POST http://localhost/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How does authentication work in this codebase?",
    "project_path": "my-project",
    "max_results": 5
  }'
```

### 4. Search Codebase

```bash
curl -X POST http://localhost/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "user authentication function",
    "project_path": "my-project",
    "limit": 10
  }'
```

## Integration with Agents

The agents automatically use RAG for context retrieval:

### Code Generation

When generating code, agents automatically retrieve relevant code from your codebase:

```bash
curl -X POST http://localhost/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a new authentication endpoint",
    "language": "python",
    "context": {
      "project_path": "my-project"
    }
  }'
```

The agent will:
1. Search codebase for relevant authentication code
2. Use that context when generating new code
3. Ensure consistency with existing patterns

### Code Review

Reviewers can access relevant code context:

```bash
curl -X POST http://localhost/api/review \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "src/auth.py",
    "context": {
      "project_path": "my-project"
    }
  }'
```

### Debugging

Debuggers can find similar code patterns:

```bash
curl -X POST http://localhost/api/debug \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "src/main.py",
    "error_message": "Authentication failed",
    "context": {
      "project_path": "my-project"
    }
  }'
```

## How It Works

### 1. Code Parsing

The code indexer:
- Scans your workspace for code files
- Parses files into semantic chunks (functions, classes, modules)
- Extracts metadata (language, line numbers, type)

### 2. Embedding Generation

- Uses Ollama's `nomic-embed-text` model
- Generates 768-dimensional vectors
- Each code chunk gets an embedding

### 3. Vector Storage

- Embeddings stored in Qdrant
- Metadata stored as payload
- Enables fast similarity search

### 4. Query Processing

When you query:
1. Query is embedded using same model
2. Qdrant finds similar code chunks
3. Top results returned as context
4. LLM generates response with context

## Supported Languages

The code indexer supports:
- Python
- JavaScript/TypeScript
- Java
- Go
- Rust
- C/C++
- And more (generic parsing)

## Best Practices

### 1. Regular Reindexing

Index after significant changes:

```bash
# Reindex after major changes
curl -X POST http://localhost/api/index \
  -H "Content-Type: application/json" \
  -d '{"force_reindex": true}'
```

### 2. Project-Specific Indexing

Index projects separately for better results:

```bash
# Index each project separately
curl -X POST http://localhost/api/index \
  -H "Content-Type: application/json" \
  -d '{"project_path": "project-a"}'

curl -X POST http://localhost/api/index \
  -H "Content-Type: application/json" \
  -d '{"project_path": "project-b"}'
```

### 3. Query Optimization

- Be specific in queries
- Use project_path for multi-project workspaces
- Adjust max_results based on needs

### 4. Model Selection

For embeddings, the system uses `nomic-embed-text` which is:
- Good for code
- Fast inference
- 768 dimensions

You can change this in `code-indexer/embedding_generator.py` if needed.

## API Reference

### Index Endpoints

#### POST /api/index
Index codebase

**Request:**
```json
{
  "project_path": "optional-project-path",
  "force_reindex": false
}
```

**Response:**
```json
{
  "success": true,
  "message": "Indexing started in background",
  "project_path": "workspace"
}
```

#### GET /api/index/status
Get indexing status

**Query Parameters:**
- `project_path` (optional): Specific project

**Response:**
```json
{
  "status": "indexed",
  "indexed_files": 150,
  "total_files": 150,
  "project_path": "workspace"
}
```

#### DELETE /api/index
Clear index

**Response:**
```json
{
  "success": true,
  "message": "Index cleared"
}
```

### Chat Endpoints

#### POST /api/chat
Chat with codebase

**Request:**
```json
{
  "message": "How does authentication work?",
  "project_path": "my-project",
  "max_results": 5,
  "temperature": 0.7,
  "model": "llama3.2:90b"
}
```

**Response:**
```json
{
  "response": "Authentication works by...",
  "sources": [
    {
      "file_path": "src/auth.py",
      "start_line": 10,
      "end_line": 45,
      "language": "python",
      "score": 0.92
    }
  ],
  "context_used": true
}
```

### Search Endpoints

#### POST /api/search
Search codebase

**Request:**
```json
{
  "query": "authentication function",
  "project_path": "my-project",
  "limit": 10
}
```

**Response:**
```json
{
  "results": [
    {
      "file_path": "src/auth.py",
      "content": "def authenticate(...)",
      "start_line": 10,
      "end_line": 45,
      "language": "python",
      "score": 0.92
    }
  ],
  "count": 1
}
```

## Troubleshooting

### Indexing Takes Too Long

- Large codebases take time
- Runs in background
- Check status endpoint for progress

### Poor Search Results

- Ensure codebase is indexed
- Try more specific queries
- Increase max_results
- Reindex after code changes

### Embedding Model Not Found

Pull the embedding model on the host:

```bash
ollama pull nomic-embed-text
```

### Qdrant Connection Issues

Check Qdrant health:

```bash
curl http://localhost:6333/health
```

Check service logs:

```bash
docker compose logs qdrant
docker compose logs code-indexer
docker compose logs rag-chat
```

## Performance

### Indexing Performance

- ~100 files/second (depends on file size)
- Embedding generation: ~50ms per chunk
- Qdrant insertion: very fast

### Query Performance

- Embedding generation: ~50ms
- Qdrant search: <10ms
- LLM response: depends on model

### Storage

- Each embedding: ~3KB
- Metadata: ~1KB per chunk
- Total: ~4KB per code chunk

For 10,000 chunks: ~40MB storage

## Advanced Usage

### Custom Embedding Models

Edit `code-indexer/embedding_generator.py`:

```python
self.embedding_model = "your-model-name"
```

Note: Vector dimensions must match Qdrant collection (default: 768).

### Custom Chunking

Edit `code-indexer/code_parser.py` to customize how code is chunked.

### Filtering Results

Use Qdrant filters for advanced queries (requires direct Qdrant API access).

## Examples

### Example 1: Understanding a Codebase

```bash
curl -X POST http://localhost/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Explain the architecture of this codebase",
    "max_results": 10
  }'
```

### Example 2: Finding Similar Code

```bash
curl -X POST http://localhost/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "database connection pooling",
    "limit": 5
  }'
```

### Example 3: Code Generation with Context

```bash
curl -X POST http://localhost/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Add a new API endpoint similar to the existing user endpoints",
    "language": "python",
    "context": {
      "project_path": "my-api"
    }
  }'
```

The agent will automatically find similar endpoints and use them as context.

## Conclusion

The RAG system provides powerful codebase understanding and search capabilities. Combined with the AI agents, it enables context-aware code generation, review, and debugging.

For more information, see:
- [README.md](README.md) - Main documentation
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture

