"""
Code Reviewer Agent - Reviews code for issues and improvements
"""
from typing import Dict, Any, List, Optional
import structlog

from agents.base_agent import BaseAgent

logger = structlog.get_logger()


class CodeReviewerAgent(BaseAgent):
    """Agent specialized in code review"""
    
    async def review(self, file_path: str, rules: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Review code for issues and improvements
        
        Args:
            file_path: Path to file to review
            rules: Specific rules to check (optional)
        """
        logger.info("Reviewing code", file_path=file_path)
        
        # Read the file
        code = await self.workspace_manager.read_file(file_path)
        if not code:
            raise ValueError(f"File not found: {file_path}")
        
        # Get language from file extension
        language = self._detect_language(file_path)
        
        # Get applicable rules
        all_rules = await self.get_rules(language)
        applicable_rules = all_rules
        if rules:
            applicable_rules = [r for r in all_rules if r.get("name") in rules]
        
        # Perform review
        system_prompt = f"""You are an expert code reviewer specializing in {language}.
Review code for:
- Bugs and errors
- Security vulnerabilities
- Performance issues
- Code quality and maintainability
- Best practices adherence
- Documentation quality
- Test coverage

Be thorough but constructive. Provide specific, actionable feedback.
"""
        
        rules_text = self._format_rules(applicable_rules)
        
        review_prompt = f"""Review this {language} code:

```{language}
{code}
```

Coding Rules to Check:
{rules_text}

Provide a comprehensive review with:
1. Critical issues (bugs, security)
2. Code quality issues
3. Performance concerns
4. Best practice violations
5. Suggestions for improvement

Format as JSON with:
- issues: array of issues with severity (critical/high/medium/low), type, description, line_number
- suggestions: array of improvement suggestions
- score: overall code quality score (0-100)
"""
        
        response = await self.call_ollama(
            prompt=review_prompt,
            system_prompt=system_prompt,
            temperature=0.2,
            max_tokens=4096
        )
        
        # Parse review results
        review_result = self._parse_review(response)
        
        return review_result
    
    async def execute_task(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a review task"""
        file_path = context.get("file_path") or task
        rules = context.get("rules")
        return await self.review(file_path, rules)
    
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
            ".c": "c",
            ".rb": "ruby",
            ".php": "php"
        }
        
        for ext, lang in ext_to_lang.items():
            if file_path.endswith(ext):
                return lang
        
        return "python"  # Default
    
    def _format_rules(self, rules: List[Dict[str, Any]]) -> str:
        """Format rules for prompt"""
        if not rules:
            return "No specific rules defined."
        
        return "\n".join([f"- {r.get('name')}: {r.get('description', '')}" for r in rules])
    
    def _parse_review(self, response: str) -> Dict[str, Any]:
        """Parse review response from LLM"""
        import json
        import re
        
        # Try to extract JSON
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except:
                pass
        
        # Fallback: parse structured text
        issues = []
        suggestions = []
        score = 75  # Default score
        
        lines = response.split("\n")
        current_section = None
        
        for line in lines:
            if "critical" in line.lower() or "bug" in line.lower():
                issues.append({
                    "severity": "critical",
                    "description": line,
                    "type": "bug"
                })
            elif "suggestion" in line.lower() or "improve" in line.lower():
                suggestions.append({"description": line})
            elif "score" in line.lower():
                score_match = re.search(r'\d+', line)
                if score_match:
                    score = int(score_match.group())
        
        return {
            "issues": issues,
            "suggestions": suggestions,
            "score": score
        }

