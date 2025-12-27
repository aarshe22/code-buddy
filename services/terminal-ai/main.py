"""
Terminal AI Assistant - AI assistance in terminal/command line
"""
import os
from typing import Dict, Any, Optional
import structlog
import httpx

from fastapi import FastAPI, HTTPException
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
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")
AGENT_ORCHESTRATOR_URL = os.getenv("AGENT_ORCHESTRATOR_URL", "http://agent-orchestrator:8000")

app = FastAPI(
    title="Terminal AI Assistant",
    description="AI assistance for terminal/command line operations",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CommandRequest(BaseModel):
    user_intent: str = Field(..., description="What the user wants to do")
    current_directory: Optional[str] = Field(default=None, description="Current working directory")
    command_history: Optional[list] = Field(default=None, description="Recent command history")
    error_message: Optional[str] = Field(default=None, description="Error message if command failed")


class CommandResponse(BaseModel):
    command: str
    explanation: str
    alternatives: Optional[list] = None
    safety_warning: Optional[str] = None


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "terminal-ai"}


@app.post("/api/command", response_model=CommandResponse)
async def suggest_command(request: CommandRequest):
    """Suggest command based on user intent"""
    try:
        logger.info("Command suggestion requested", intent=request.user_intent)
        
        # Build context
        context = f"User wants to: {request.user_intent}"
        if request.current_directory:
            context += f"\nCurrent directory: {request.current_directory}"
        if request.command_history:
            context += f"\nRecent commands: {', '.join(request.command_history[-5:])}"
        if request.error_message:
            context += f"\nError: {request.error_message}"
        
        # Call Ollama for command suggestion
        url = f"{OLLAMA_HOST}/api/generate"
        payload = {
            "model": "llama3.2:90b",
            "prompt": f"""You are a helpful terminal assistant. The user wants to: {request.user_intent}

{context}

Provide a safe, appropriate command. Consider:
- Safety (avoid destructive commands unless explicitly requested)
- Best practices
- Cross-platform compatibility (Linux/Unix)

Respond in JSON format:
{{
  "command": "the command to run",
  "explanation": "brief explanation",
  "alternatives": ["alternative commands if applicable"],
  "safety_warning": "warning if command is potentially destructive"
}}""",
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_predict": 500
            }
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            
            # Parse response
            import json
            import re
            response_text = result.get("response", "")
            
            # Try to extract JSON
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    parsed = json.loads(json_match.group())
                    return CommandResponse(**parsed)
                except:
                    pass
            
            # Fallback
            return CommandResponse(
                command=response_text.split('\n')[0].strip(),
                explanation=response_text[:200]
            )
    
    except Exception as e:
        logger.error("Command suggestion failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/explain-command")
async def explain_command(command: str):
    """Explain what a command does"""
    try:
        url = f"{OLLAMA_HOST}/api/generate"
        payload = {
            "model": "llama3.2:90b",
            "prompt": f"Explain what this command does in detail: {command}\n\nInclude:\n- What it does\n- Each flag/option\n- Common use cases\n- Safety considerations",
            "stream": False,
            "options": {
                "temperature": 0.2,
                "num_predict": 1000
            }
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            
            return {
                "command": command,
                "explanation": result.get("response", "")
            }
    
    except Exception as e:
        logger.error("Command explanation failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/fix-command")
async def fix_command(command: str, error_message: str):
    """Fix a command that failed"""
    try:
        url = f"{OLLAMA_HOST}/api/generate"
        payload = {
            "model": "llama3.2:90b",
            "prompt": f"""The user ran this command and got an error:

Command: {command}
Error: {error_message}

Provide:
1. The corrected command
2. Explanation of what was wrong
3. Alternative solutions if applicable

Format as JSON:
{{
  "fixed_command": "corrected command",
  "explanation": "what was wrong",
  "alternatives": ["alternative solutions"]
}}""",
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_predict": 500
            }
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            
            import json
            import re
            response_text = result.get("response", "")
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    pass
            
            return {
                "fixed_command": response_text.split('\n')[0].strip(),
                "explanation": response_text[:200]
            }
    
    except Exception as e:
        logger.error("Command fix failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)

