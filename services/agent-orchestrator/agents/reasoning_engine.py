"""
Reasoning Engine - Advanced reasoning capabilities for agents
"""
from typing import Dict, Any, List, Optional
import httpx
import structlog
import json

logger = structlog.get_logger()


class ReasoningEngine:
    """Advanced reasoning engine using chain-of-thought and tree-of-thought"""
    
    def __init__(self, ollama_host: str):
        self.ollama_host = ollama_host
        self.model = "qwen2.5:72b"
    
    async def reason(self, problem: str, context: Optional[Dict[str, Any]] = None,
                    reasoning_type: str = "chain_of_thought") -> Dict[str, Any]:
        """
        Perform reasoning on a problem
        
        Args:
            problem: The problem to reason about
            context: Additional context
            reasoning_type: Type of reasoning (chain_of_thought, tree_of_thought, iterative)
        """
        if reasoning_type == "chain_of_thought":
            return await self._chain_of_thought(problem, context)
        elif reasoning_type == "tree_of_thought":
            return await self._tree_of_thought(problem, context)
        else:
            return await self._iterative_reasoning(problem, context)
    
    async def _chain_of_thought(self, problem: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Chain of Thought reasoning"""
        system_prompt = """You are an advanced reasoning system. Break down problems step by step.
Think through each step carefully before proceeding to the next.
Provide clear reasoning at each step."""
        
        prompt = f"""Problem: {problem}

Context: {json.dumps(context or {}, indent=2)}

Please solve this problem using chain-of-thought reasoning:
1. Break down the problem into steps
2. Analyze each step
3. Consider alternatives
4. Reach a conclusion
5. Verify your reasoning

Format your response as JSON with:
- steps: array of reasoning steps
- conclusion: final answer
- confidence: confidence level (0-1)
"""
        
        url = f"{self.ollama_host}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_predict": 4096
            }
        }
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            response_text = result.get("response", "")
            
            # Try to parse JSON from response
            try:
                # Extract JSON from markdown code blocks if present
                if "```json" in response_text:
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()
                elif "```" in response_text:
                    json_start = response_text.find("```") + 3
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()
                
                return json.loads(response_text)
            except:
                # Fallback to structured text parsing
                return {
                    "reasoning": response_text,
                    "conclusion": self._extract_conclusion(response_text),
                    "confidence": 0.7
                }
    
    async def _tree_of_thought(self, problem: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Tree of Thought reasoning - explore multiple solution paths"""
        system_prompt = """You are an advanced reasoning system using tree-of-thought.
Explore multiple solution paths, evaluate each, and select the best approach."""
        
        prompt = f"""Problem: {problem}

Context: {json.dumps(context or {}, indent=2)}

Use tree-of-thought reasoning:
1. Generate multiple solution approaches
2. Evaluate each approach
3. Select the best approach
4. Refine the selected approach
5. Provide final solution

Format as JSON with:
- approaches: array of different approaches considered
- evaluations: evaluation of each approach
- selected_approach: the chosen approach
- solution: final solution
"""
        
        url = f"{self.ollama_host}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 6144
            }
        }
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            response_text = result.get("response", "")
            
            try:
                if "```json" in response_text:
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()
                
                return json.loads(response_text)
            except:
                return {
                    "reasoning": response_text,
                    "solution": self._extract_conclusion(response_text)
                }
    
    async def _iterative_reasoning(self, problem: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Iterative reasoning - refine solution through iterations"""
        system_prompt = """You are an advanced reasoning system using iterative refinement.
Start with an initial solution, identify issues, and iteratively improve."""
        
        iterations = []
        current_solution = None
        
        for i in range(3):  # 3 iterations
            prompt = f"""Problem: {problem}

Context: {json.dumps(context or {}, indent=2)}

Previous iterations: {json.dumps(iterations, indent=2) if iterations else "None"}

{"Refine the solution from previous iteration" if current_solution else "Provide initial solution"}:
1. Analyze the problem
2. {"Identify issues with current solution" if current_solution else "Propose initial solution"}
3. {"Improve the solution" if current_solution else "Consider edge cases"}
4. Provide updated solution
"""
            
            url = f"{self.ollama_host}/api/generate"
            payload = {
                "model": self.model,
                "prompt": prompt,
                "system": system_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.5,
                    "num_predict": 4096
                }
            }
            
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                result = response.json()
                response_text = result.get("response", "")
                
                iterations.append({
                    "iteration": i + 1,
                    "reasoning": response_text
                })
                current_solution = self._extract_conclusion(response_text)
        
        return {
            "iterations": iterations,
            "final_solution": current_solution
        }
    
    def _extract_conclusion(self, text: str) -> str:
        """Extract conclusion from reasoning text"""
        # Simple extraction - look for conclusion markers
        markers = ["conclusion:", "solution:", "answer:", "result:"]
        text_lower = text.lower()
        
        for marker in markers:
            idx = text_lower.find(marker)
            if idx != -1:
                return text[idx + len(marker):].strip()[:500]
        
        # Return last paragraph as conclusion
        paragraphs = text.split("\n\n")
        return paragraphs[-1].strip()[:500] if paragraphs else text[:500]

