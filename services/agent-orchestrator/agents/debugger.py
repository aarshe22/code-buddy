"""
Debugger Agent - Debugs code issues
"""
from typing import Dict, Any, List, Optional
import structlog
import json
import re

from agents.base_agent import BaseAgent

logger = structlog.get_logger()


class DebuggerAgent(BaseAgent):
    """Agent specialized in debugging"""
    
    async def debug(self, file_path: str, error_message: Optional[str] = None,
                   test_cases: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Debug code issues
        
        Args:
            file_path: Path to file with bug
            error_message: Error message or description
            test_cases: Failing test cases
        """
        logger.info("Debugging code", file_path=file_path, error=error_message)
        
        # Read the file
        code = await self.workspace_manager.read_file(file_path)
        if not code:
            raise ValueError(f"File not found: {file_path}")
        
        # Use reasoning engine to analyze the problem
        problem_description = error_message or "Code is not working as expected"
        reasoning_result = await self.reasoning_engine.reason(
            f"Debug this code issue: {problem_description}",
            context={
                "code": code[:2000],  # Limit context size
                "test_cases": test_cases or []
            },
            reasoning_type="iterative"
        )
        
        # Generate debug analysis
        language = self._detect_language(file_path)
        
        system_prompt = f"""You are an expert debugger specializing in {language}.
Analyze code systematically:
1. Understand the problem
2. Identify root cause
3. Propose fixes
4. Verify the fix

Be thorough and methodical.
"""
        
        debug_prompt = f"""Debug this {language} code:

```{language}
{code}
```

Problem: {problem_description}

Reasoning Analysis:
{json.dumps(reasoning_result, indent=2)}

{"Test Cases:" if test_cases else ""}
{json.dumps(test_cases, indent=2) if test_cases else ""}

Provide:
1. Root cause analysis
2. Specific fixes with explanations
3. Fixed code
4. Verification steps

Format as JSON with:
- root_cause: description of the root cause
- fixes: array of fixes with description, line_number, old_code, new_code
- fixed_code: complete fixed code
- explanation: detailed explanation
"""
        
        response = await self.call_ollama(
            prompt=debug_prompt,
            system_prompt=system_prompt,
            temperature=0.2,
            max_tokens=8192
        )
        
        # Parse debug results
        debug_result = self._parse_debug_response(response, code)
        
        # Apply fixes if provided
        if debug_result.get("fixed_code"):
            fixed_code = debug_result["fixed_code"]
            await self.workspace_manager.write_file(file_path, fixed_code)
            logger.info("Fixed code saved", file_path=file_path)
        
        return debug_result
    
    async def execute_task(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a debug task"""
        file_path = context.get("file_path") or task
        error_message = context.get("error_message")
        test_cases = context.get("test_cases")
        return await self.debug(file_path, error_message, test_cases)
    
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
    
    def _parse_debug_response(self, response: str, original_code: str) -> Dict[str, Any]:
        """Parse debug response from LLM"""
        import re
        
        # Try to extract JSON
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group())
                # Ensure fixed_code is present
                if not result.get("fixed_code"):
                    result["fixed_code"] = self._extract_code(response)
                return result
            except:
                pass
        
        # Fallback: extract code and create structured response
        fixed_code = self._extract_code(response) or original_code
        
        return {
            "root_cause": self._extract_section(response, "root cause"),
            "fixes": [{"description": "See fixed code", "code": fixed_code}],
            "fixed_code": fixed_code,
            "explanation": response[:1000]
        }
    
    def _extract_code(self, response: str) -> str:
        """Extract code from response"""
        code_blocks = re.findall(r'```(?:\w+)?\n(.*?)```', response, re.DOTALL)
        if code_blocks:
            return code_blocks[-1].strip()
        return ""
    
    def _extract_section(self, response: str, section: str) -> str:
        """Extract a section from response"""
        pattern = f"{section}[:\\s]+(.*?)(?=\\n\\n|$)"
        match = re.search(pattern, response, re.IGNORECASE | re.DOTALL)
        return match.group(1).strip() if match else ""

