"""
Agent Orchestrator - Main service for coordinating AI agents
"""
import os
import asyncio
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional
import structlog

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import httpx

from agents.code_generator import CodeGeneratorAgent
from agents.code_reviewer import CodeReviewerAgent
from agents.debugger import DebuggerAgent
from agents.refactorer import RefactorerAgent
from agents.reasoning_engine import ReasoningEngine
from mcp_client import MCPClient
from workspace_manager import WorkspaceManager

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
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
WORKSPACE_PATH = os.getenv("WORKSPACE_PATH", "/app/workspace")
MCP_GITHUB_URL = os.getenv("MCP_GITHUB_URL", "http://mcp-github:3001")
MCP_GITLAB_URL = os.getenv("MCP_GITLAB_URL", "http://mcp-gitlab:3002")
RULES_ENGINE_URL = os.getenv("RULES_ENGINE_URL", "http://rules-engine:8001")

# Initialize components
workspace_manager = WorkspaceManager(WORKSPACE_PATH)
mcp_client = MCPClient(MCP_GITHUB_URL, MCP_GITLAB_URL)
reasoning_engine = ReasoningEngine(OLLAMA_HOST)

# Initialize agents
code_generator = CodeGeneratorAgent(OLLAMA_HOST, workspace_manager, mcp_client, reasoning_engine)
code_reviewer = CodeReviewerAgent(OLLAMA_HOST, workspace_manager, mcp_client, reasoning_engine)
debugger = DebuggerAgent(OLLAMA_HOST, workspace_manager, mcp_client, reasoning_engine)
refactorer = RefactorerAgent(OLLAMA_HOST, workspace_manager, mcp_client, reasoning_engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic"""
    logger.info("Starting Agent Orchestrator")
    await workspace_manager.initialize()
    yield
    logger.info("Shutting down Agent Orchestrator")


app = FastAPI(
    title="Agent Orchestrator",
    description="AI Agent Orchestration Service",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class GenerateCodeRequest(BaseModel):
    prompt: str = Field(..., description="Description of code to generate")
    language: str = Field(default="python", description="Programming language")
    context_files: Optional[List[str]] = Field(default=None, description="Relevant files for context")
    repository_url: Optional[str] = Field(default=None, description="GitHub/GitLab repo URL for context")
    output_path: Optional[str] = Field(default=None, description="Where to save generated code")


class CodeReviewRequest(BaseModel):
    file_path: str = Field(..., description="Path to file to review")
    rules: Optional[List[str]] = Field(default=None, description="Specific rules to check")


class DebugRequest(BaseModel):
    file_path: str = Field(..., description="Path to file with bug")
    error_message: Optional[str] = Field(default=None, description="Error message or description")
    test_cases: Optional[List[Dict[str, Any]]] = Field(default=None, description="Failing test cases")


class RefactorRequest(BaseModel):
    file_path: str = Field(..., description="Path to file to refactor")
    refactor_type: str = Field(..., description="Type of refactoring (extract, rename, simplify, etc.)")
    target: Optional[str] = Field(default=None, description="Specific target for refactoring")


class ExplainRequest(BaseModel):
    code: str = Field(..., description="Code to explain")
    language: str = Field(default="python", description="Programming language")
    file_path: Optional[str] = Field(default=None, description="Path to file")


class GenerateTestsRequest(BaseModel):
    file_path: str = Field(..., description="Path to file to generate tests for")
    test_framework: Optional[str] = Field(default=None, description="Test framework to use")
    coverage: Optional[float] = Field(default=0.8, description="Target test coverage")


class GenerateDocsRequest(BaseModel):
    file_path: str = Field(..., description="Path to file to generate docs for")
    doc_format: Optional[str] = Field(default="docstring", description="Documentation format")
    include_examples: bool = Field(default=True, description="Include usage examples")


class AgentTaskRequest(BaseModel):
    task: str = Field(..., description="Natural language task description")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")
    agent_type: Optional[str] = Field(default="auto", description="Specific agent or 'auto' for selection")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "agent-orchestrator"}


@app.post("/generate")
async def generate_code(request: GenerateCodeRequest, background_tasks: BackgroundTasks):
    """Generate code based on natural language description"""
    try:
        logger.info("Code generation requested", prompt=request.prompt, language=request.language)
        
        # Get context from repository if provided
        context = {}
        if request.repository_url:
            context = await mcp_client.get_repository_context(request.repository_url)
        
        # Add file context if provided
        if request.context_files:
            for file_path in request.context_files:
                content = await workspace_manager.read_file(file_path)
                context[file_path] = content
        
        # Generate code
        result = await code_generator.generate(
            prompt=request.prompt,
            language=request.language,
            context=context,
            output_path=request.output_path
        )
        
        return {
            "success": True,
            "code": result["code"],
            "file_path": result.get("file_path"),
            "explanation": result.get("explanation")
        }
    except Exception as e:
        logger.error("Code generation failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/review")
async def review_code(request: CodeReviewRequest):
    """Review code for issues and improvements"""
    try:
        logger.info("Code review requested", file_path=request.file_path)
        
        result = await code_reviewer.review(
            file_path=request.file_path,
            rules=request.rules
        )
        
        return {
            "success": True,
            "issues": result["issues"],
            "suggestions": result["suggestions"],
            "score": result.get("score")
        }
    except Exception as e:
        logger.error("Code review failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/debug")
async def debug_code(request: DebugRequest):
    """Debug code issues"""
    try:
        logger.info("Debug requested", file_path=request.file_path)
        
        result = await debugger.debug(
            file_path=request.file_path,
            error_message=request.error_message,
            test_cases=request.test_cases
        )
        
        return {
            "success": True,
            "fixes": result["fixes"],
            "explanation": result["explanation"],
            "fixed_code": result.get("fixed_code")
        }
    except Exception as e:
        logger.error("Debug failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/refactor")
async def refactor_code(request: RefactorRequest):
    """Refactor code"""
    try:
        logger.info("Refactor requested", file_path=request.file_path, refactor_type=request.refactor_type)
        
        result = await refactorer.refactor(
            file_path=request.file_path,
            refactor_type=request.refactor_type,
            target=request.target
        )
        
        return {
            "success": True,
            "refactored_code": result["refactored_code"],
            "changes": result["changes"],
            "explanation": result["explanation"]
        }
    except Exception as e:
        logger.error("Refactor failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/task")
async def execute_task(request: AgentTaskRequest):
    """Execute a general task using appropriate agent"""
    try:
        logger.info("Task execution requested", task=request.task, agent_type=request.agent_type)
        
        # Auto-select agent based on task
        if request.agent_type == "auto":
            agent = await select_agent(request.task)
        else:
            agent = get_agent_by_type(request.agent_type)
        
        result = await agent.execute_task(request.task, request.context or {})
        
        return {
            "success": True,
            "result": result,
            "agent_used": agent.__class__.__name__
        }
    except Exception as e:
        logger.error("Task execution failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/explain")
async def explain_code(request: ExplainRequest):
    """Explain code in detail"""
    try:
        logger.info("Code explanation requested", language=request.language)
        
        system_prompt = f"""You are an expert {request.language} developer. Explain code clearly and comprehensively.
Explain:
- What the code does
- How it works
- Key concepts and patterns
- Potential issues or improvements
- Usage examples if applicable"""
        
        prompt = f"""Explain this {request.language} code in detail:

```{request.language}
{request.code}
```

Provide a comprehensive explanation."""
        
        response = await code_generator.call_ollama(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.2,
            max_tokens=2048
        )
        
        return {
            "success": True,
            "explanation": response,
            "language": request.language
        }
    except Exception as e:
        logger.error("Code explanation failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate-tests")
async def generate_tests(request: GenerateTestsRequest):
    """Generate unit tests for code"""
    try:
        logger.info("Test generation requested", file_path=request.file_path)
        
        # Read the file
        code = await workspace_manager.read_file(request.file_path)
        if not code:
            raise ValueError(f"File not found: {request.file_path}")
        
        # Detect language from file extension
        ext_to_lang = {
            '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
            '.java': 'java', '.go': 'go', '.rs': 'rust', '.cpp': 'cpp', '.c': 'c'
        }
        language = 'python'  # default
        for ext, lang in ext_to_lang.items():
            if request.file_path.endswith(ext):
                language = lang
                break
        
        test_framework = request.test_framework or {
            "python": "pytest",
            "javascript": "jest",
            "typescript": "jest",
            "java": "junit",
            "go": "testing"
        }.get(language, "pytest")
        
        # Get codebase context for better tests
        codebase_context = await code_generator.get_codebase_context(
            query=f"test examples for {language} using {test_framework}",
            max_results=3
        )
        
        context = {"code": code, "codebase": codebase_context}
        
        prompt = f"""Generate comprehensive unit tests for this {language} code using {test_framework}.

Requirements:
- Cover all functions/methods
- Include edge cases
- Test error handling
- Target coverage: {request.coverage * 100}%
- Follow {test_framework} best practices

Code to test:
```{language}
{code}
```"""
        
        result = await code_generator.generate(
            prompt=prompt,
            language=language,
            context=context,
            output_path=request.file_path.replace(f".{language}", f"_test.{language}")
        )
        
        return {
            "success": True,
            "tests": result["code"],
            "file_path": result["file_path"],
            "test_framework": test_framework,
            "explanation": result.get("explanation")
        }
    except Exception as e:
        logger.error("Test generation failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate-docs")
async def generate_docs(request: GenerateDocsRequest):
    """Generate documentation for code"""
    try:
        logger.info("Documentation generation requested", file_path=request.file_path)
        
        # Read the file
        code = await workspace_manager.read_file(request.file_path)
        if not code:
            raise ValueError(f"File not found: {request.file_path}")
        
        # Detect language from file extension
        ext_to_lang = {
            '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
            '.java': 'java', '.go': 'go', '.rs': 'rust', '.cpp': 'cpp', '.c': 'c'
        }
        language = 'python'  # default
        for ext, lang in ext_to_lang.items():
            if request.file_path.endswith(ext):
                language = lang
                break
        
        doc_format = request.doc_format
        if language == "python" and doc_format == "docstring":
            doc_format = "google"  # Google-style docstrings for Python
        
        system_prompt = f"""You are an expert technical writer specializing in {language} documentation.
Generate clear, comprehensive documentation following {doc_format} format.
Include:
- Function/class descriptions
- Parameter documentation
- Return value documentation
- Usage examples
- Error conditions"""
        
        prompt = f"""Generate {doc_format} documentation for this {language} code:

```{language}
{code}
```

{"Include usage examples." if request.include_examples else ""}

Provide complete documentation."""
        
        response = await code_generator.call_ollama(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.2,
            max_tokens=4096
        )
        
        return {
            "success": True,
            "documentation": response,
            "format": doc_format,
            "language": language
        }
    except Exception as e:
        logger.error("Documentation generation failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def select_agent(task: str) -> Any:
    """Select appropriate agent based on task description"""
    task_lower = task.lower()
    
    if any(word in task_lower for word in ["generate", "create", "write", "implement", "build"]):
        return code_generator
    elif any(word in task_lower for word in ["review", "check", "analyze", "audit"]):
        return code_reviewer
    elif any(word in task_lower for word in ["debug", "fix", "error", "bug", "issue"]):
        return debugger
    elif any(word in task_lower for word in ["refactor", "improve", "optimize", "clean"]):
        return refactorer
    else:
        # Default to code generator for general tasks
        return code_generator


def get_agent_by_type(agent_type: str) -> Any:
    """Get agent by type name"""
    agents = {
        "generator": code_generator,
        "reviewer": code_reviewer,
        "debugger": debugger,
        "refactorer": refactorer
    }
    return agents.get(agent_type.lower(), code_generator)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

