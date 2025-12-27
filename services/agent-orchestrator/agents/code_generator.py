"""
Code Generator Agent - Generates code from natural language descriptions
"""
from typing import Dict, Any, List, Optional
import structlog
import json

from agents.base_agent import BaseAgent

logger = structlog.get_logger()


class CodeGeneratorAgent(BaseAgent):
    """Agent specialized in generating code"""
    
    async def generate(self, prompt: str, language: str = "python",
                      context: Optional[Dict[str, Any]] = None,
                      output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate code from natural language description
        
        Args:
            prompt: Natural language description of code to generate
            language: Programming language
            context: Additional context (files, repository info, etc.)
            output_path: Where to save the generated code
        """
        logger.info("Generating code", prompt=prompt[:100], language=language)
        
        # Get coding rules for the language
        rules = await self.get_rules(language)
        
        # Get relevant codebase context from Qdrant
        project_path = context.get("project_path") if context else None
        codebase_context = await self.get_codebase_context(
            query=prompt,
            project_path=project_path,
            max_results=5
        )
        
        # Add codebase context to context dict
        if codebase_context and context:
            context["codebase"] = codebase_context
        elif codebase_context:
            context = {"codebase": codebase_context}
        
        # Build context string
        context_str = self._build_context_string(context, rules)
        
        # Use reasoning engine for complex tasks
        if self._is_complex_task(prompt):
            reasoning_result = await self.reasoning_engine.reason(
                f"Generate {language} code: {prompt}",
                context={"language": language, "rules": rules},
                reasoning_type="tree_of_thought"
            )
            prompt = f"{prompt}\n\nReasoning: {json.dumps(reasoning_result, indent=2)}"
        
        # Generate code
        system_prompt = f"""You are an expert {language} developer. Generate clean, efficient, well-documented code.
Follow best practices and coding standards for {language}.
Always include:
- Proper error handling
- Type hints/annotations where applicable
- Docstrings/comments
- Tests if appropriate

Coding Rules:
{self._format_rules(rules)}
"""
        
        code_prompt = f"""Generate {language} code based on this description:

{prompt}

{context_str}

Provide the complete code implementation. Include all necessary imports and dependencies.
If tests are needed, include them as well.
"""
        
        response = await self.call_ollama(
            prompt=code_prompt,
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=8192
        )
        
        # Extract code from response
        code = self._extract_code(response, language)
        
        # Save to file if path provided
        file_path = output_path
        if file_path:
            await self.workspace_manager.write_file(file_path, code)
            logger.info("Code saved", file_path=file_path)
        else:
            # Generate default path
            file_path = await self._generate_file_path(language, prompt)
            await self.workspace_manager.write_file(file_path, code)
        
        return {
            "code": code,
            "file_path": file_path,
            "explanation": self._extract_explanation(response),
            "language": language
        }
    
    async def execute_task(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a general task"""
        language = context.get("language", "python")
        output_path = context.get("output_path")
        return await self.generate(task, language, context, output_path)
    
    def _build_context_string(self, context: Optional[Dict[str, Any]], 
                             rules: List[Dict[str, Any]]) -> str:
        """Build context string from context dict"""
        if not context:
            return ""
        
        parts = []
        
        # Add codebase context from Qdrant (RAG)
        if "codebase" in context:
            parts.append("Relevant code from codebase:")
            for code_chunk in context["codebase"][:5]:  # Limit to 5 chunks
                file_path = code_chunk.get("file_path", "unknown")
                content = code_chunk.get("content", "")
                start_line = code_chunk.get("start_line", 0)
                end_line = code_chunk.get("end_line", 0)
                parts.append(f"\n--- {file_path} (lines {start_line}-{end_line}) ---\n{content[:1500]}")
        
        # Add file context
        if "files" in context:
            parts.append("Relevant files:")
            for file_path, content in context["files"].items():
                parts.append(f"\n--- {file_path} ---\n{content[:2000]}")
        
        # Add repository context
        if "repository" in context:
            repo_info = context["repository"]
            parts.append(f"\nRepository: {repo_info.get('url', 'N/A')}")
            if "structure" in repo_info:
                parts.append(f"Structure: {json.dumps(repo_info['structure'], indent=2)}")
        
        return "\n".join(parts)
    
    def _format_rules(self, rules: List[Dict[str, Any]]) -> str:
        """Format rules for prompt"""
        if not rules:
            return "No specific rules defined."
        
        formatted = []
        for rule in rules:
            formatted.append(f"- {rule.get('name', 'Rule')}: {rule.get('description', '')}")
            if rule.get("examples"):
                formatted.append(f"  Examples: {rule.get('examples')}")
        
        return "\n".join(formatted)
    
    def _is_complex_task(self, prompt: str) -> bool:
        """Determine if task is complex enough to warrant reasoning"""
        complex_keywords = ["system", "architecture", "design", "framework", "multiple", "complex"]
        return any(keyword in prompt.lower() for keyword in complex_keywords)
    
    def _extract_code(self, response: str, language: str) -> str:
        """Extract code from LLM response"""
        # Look for code blocks
        code_block_markers = [
            f"```{language}",
            f"```{language.lower()}",
            "```python",
            "```javascript",
            "```typescript",
            "```java",
            "```go",
            "```rust",
            "```cpp",
            "```c",
            "```"
        ]
        
        for marker in code_block_markers:
            if marker in response:
                start_idx = response.find(marker) + len(marker)
                end_idx = response.find("```", start_idx)
                if end_idx != -1:
                    return response[start_idx:end_idx].strip()
        
        # If no code block, return response as-is (might be plain code)
        return response.strip()
    
    def _extract_explanation(self, response: str) -> str:
        """Extract explanation from response"""
        # Look for explanation before or after code
        explanation_markers = ["explanation:", "note:", "description:"]
        
        for marker in explanation_markers:
            idx = response.lower().find(marker)
            if idx != -1:
                return response[idx + len(marker):].strip()[:500]
        
        return "Code generated successfully."
    
    async def _generate_file_path(self, language: str, prompt: str) -> str:
        """Generate a default file path based on language and prompt"""
        extensions = {
            "python": ".py",
            "javascript": ".js",
            "typescript": ".ts",
            "java": ".java",
            "go": ".go",
            "rust": ".rs",
            "cpp": ".cpp",
            "c": ".c"
        }
        
        ext = extensions.get(language.lower(), ".txt")
        
        # Simple filename generation
        filename = "generated_code"
        if "class" in prompt.lower():
            filename = "generated_class"
        elif "function" in prompt.lower() or "func" in prompt.lower():
            filename = "generated_function"
        elif "api" in prompt.lower() or "endpoint" in prompt.lower():
            filename = "generated_api"
        
        return f"{filename}{ext}"

