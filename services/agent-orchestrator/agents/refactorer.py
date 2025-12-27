"""
Refactorer Agent - Refactors code for improvement
"""
from typing import Dict, Any, Optional
import structlog
import json
import re

from agents.base_agent import BaseAgent

logger = structlog.get_logger()


class RefactorerAgent(BaseAgent):
    """Agent specialized in code refactoring"""
    
    async def refactor(self, file_path: str, refactor_type: str,
                     target: Optional[str] = None) -> Dict[str, Any]:
        """
        Refactor code
        
        Args:
            file_path: Path to file to refactor
            refactor_type: Type of refactoring (extract, rename, simplify, optimize, etc.)
            target: Specific target for refactoring (function name, variable, etc.)
        """
        logger.info("Refactoring code", file_path=file_path, refactor_type=refactor_type)
        
        # Read the file
        code = await self.workspace_manager.read_file(file_path)
        if not code:
            raise ValueError(f"File not found: {file_path}")
        
        # Use reasoning engine to plan refactoring
        reasoning_result = await self.reasoning_engine.reason(
            f"Refactor code: {refactor_type}",
            context={
                "code": code[:2000],
                "target": target,
                "refactor_type": refactor_type
            },
            reasoning_type="tree_of_thought"
        )
        
        language = self._detect_language(file_path)
        
        # Get rules for the language
        rules = await self.get_rules(language)
        
        system_prompt = f"""You are an expert code refactoring specialist in {language}.
Refactor code to improve:
- Readability
- Maintainability
- Performance
- Adherence to best practices
- Code organization

Preserve functionality while improving code quality.
"""
        
        refactor_prompt = f"""Refactor this {language} code:

```{language}
{code}
```

Refactoring Type: {refactor_type}
{"Target: " + target if target else ""}

Reasoning Plan:
{json.dumps(reasoning_result, indent=2)}

Coding Rules:
{self._format_rules(rules)}

Provide:
1. Refactored code
2. List of changes made
3. Explanation of improvements

Format as JSON with:
- refactored_code: complete refactored code
- changes: array of changes with description, before, after
- explanation: detailed explanation of improvements
"""
        
        response = await self.call_ollama(
            prompt=refactor_prompt,
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=8192
        )
        
        # Parse refactoring results
        refactor_result = self._parse_refactor_response(response, code)
        
        # Save refactored code
        if refactor_result.get("refactored_code"):
            await self.workspace_manager.write_file(file_path, refactor_result["refactored_code"])
            logger.info("Refactored code saved", file_path=file_path)
        
        return refactor_result
    
    async def execute_task(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a refactoring task"""
        file_path = context.get("file_path") or task
        refactor_type = context.get("refactor_type", "improve")
        target = context.get("target")
        return await self.refactor(file_path, refactor_type, target)
    
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension"""
        ext_to_lang = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".java": "java",
            ".go": "go",
            ".rs": "rust",
            ".cpp": "cpp",
            ".c": "c"
        }
        
        for ext, lang in ext_to_lang.items():
            if file_path.endswith(ext):
                return lang
        
        return "python"
    
    def _format_rules(self, rules: list) -> str:
        """Format rules for prompt"""
        if not rules:
            return "No specific rules defined."
        
        return "\n".join([f"- {r.get('name')}: {r.get('description', '')}" for r in rules])
    
    def _parse_refactor_response(self, response: str, original_code: str) -> Dict[str, Any]:
        """Parse refactoring response from LLM"""
        import re
        
        # Try to extract JSON
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group())
                # Ensure refactored_code is present
                if not result.get("refactored_code"):
                    result["refactored_code"] = self._extract_code(response) or original_code
                return result
            except:
                pass
        
        # Fallback: extract code and create structured response
        refactored_code = self._extract_code(response) or original_code
        
        return {
            "refactored_code": refactored_code,
            "changes": [{"description": "See refactored code"}],
            "explanation": response[:1000]
        }
    
    def _extract_code(self, response: str) -> str:
        """Extract code from response"""
        code_blocks = re.findall(r'```(?:\w+)?\n(.*?)```', response, re.DOTALL)
        if code_blocks:
            return code_blocks[-1].strip()
        return ""

