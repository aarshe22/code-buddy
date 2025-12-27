"""
Embedding Generator - Generates embeddings using Ollama
"""
import httpx
from typing import List
import structlog

logger = structlog.get_logger()


class EmbeddingGenerator:
    """Generates embeddings for code chunks using Ollama"""
    
    def __init__(self, ollama_host: str):
        self.ollama_host = ollama_host
        self.embedding_model = "nomic-embed-text"  # Good for code embeddings
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        try:
            url = f"{self.ollama_host}/api/embeddings"
            
            payload = {
                "model": self.embedding_model,
                "prompt": text[:8192]  # Limit text length
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                result = response.json()
                return result.get("embedding", [])
        
        except Exception as e:
            logger.error("Failed to generate embedding", error=str(e))
            # Fallback: return zero vector (shouldn't happen in production)
            return [0.0] * 768
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        embeddings = []
        for text in texts:
            embedding = await self.generate_embedding(text)
            embeddings.append(embedding)
        return embeddings

