"""
Base Agent Class - Foundation for all AI agents
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import httpx
import structlog

logger = structlog.get_logger()


class BaseAgent(ABC):
    """Base class for all AI agents"""
    
    def __init__(self, ollama_host: str, workspace_manager, mcp_client, reasoning_engine):
        self.ollama_host = ollama_host
        self.workspace_manager = workspace_manager
        self.mcp_client = mcp_client
        self.reasoning_engine = reasoning_engine
        self.model = "llama3.2:90b"  # Default model, can be overridden
        
    async def call_ollama(self, prompt: str, system_prompt: Optional[str] = None, 
                         model: Optional[str] = None, temperature: float = 0.7,
                         max_tokens: int = 8192) -> str:
        """Call Ollama API"""
        model = model or self.model
        url = f"{self.ollama_host}/api/generate"
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                result = response.json()
                return result.get("response", "")
        except Exception as e:
            logger.error("Ollama API call failed", error=str(e), model=model)
            raise
    
    async def get_rules(self, language: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get coding rules from rules engine"""
        try:
            rules_engine_url = "http://rules-engine:8001"
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{rules_engine_url}/rules",
                    params={"language": language} if language else {}
                )
                response.raise_for_status()
                return response.json().get("rules", [])
        except Exception as e:
            logger.warning("Failed to fetch rules", error=str(e))
            return []
    
    async def get_codebase_context(self, query: str, project_path: Optional[str] = None,
                                  max_results: int = 5) -> List[Dict[str, Any]]:
        """Get relevant code context from Qdrant using RAG"""
        try:
            rag_chat_url = "http://rag-chat:8003"
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{rag_chat_url}/search",
                    params={
                        "query": query,
                        "project_path": project_path,
                        "limit": max_results
                    }
                )
                response.raise_for_status()
                result = response.json()
                return result.get("results", [])
        except Exception as e:
            logger.warning("Failed to get codebase context", error=str(e))
            return []
    
    @abstractmethod
    async def execute_task(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task - must be implemented by subclasses"""
        pass

