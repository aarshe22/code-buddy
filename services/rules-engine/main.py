"""
Rules Engine - Manages coding standards and rules
"""
import os
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
import structlog

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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
RULES_PATH = os.getenv("RULES_PATH", "/app/rules")

app = FastAPI(
    title="Rules Engine",
    description="Coding Standards and Rules Management",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Rule(BaseModel):
    name: str
    description: str
    language: Optional[str] = None
    severity: str = "medium"  # low, medium, high, critical
    pattern: Optional[str] = None
    examples: Optional[List[str]] = None
    enabled: bool = True


class RulesManager:
    """Manages coding rules"""
    
    def __init__(self, rules_path: str):
        self.rules_path = Path(rules_path)
        self.rules_path.mkdir(parents=True, exist_ok=True)
        self.rules: Dict[str, List[Rule]] = {}
        self._load_rules()
    
    def _load_rules(self):
        """Load rules from YAML files"""
        logger.info("Loading rules", path=str(self.rules_path))
        
        # Load default rules
        default_rules_file = self.rules_path / "default.yaml"
        if default_rules_file.exists():
            self._load_rules_file(default_rules_file)
        
        # Load language-specific rules
        for rule_file in self.rules_path.glob("*.yaml"):
            if rule_file.name != "default.yaml":
                self._load_rules_file(rule_file)
        
        # Load language-specific rules from subdirectories
        for lang_dir in self.rules_path.iterdir():
            if lang_dir.is_dir():
                for rule_file in lang_dir.glob("*.yaml"):
                    self._load_rules_file(rule_file, language=lang_dir.name)
    
    def _load_rules_file(self, rule_file: Path, language: Optional[str] = None):
        """Load rules from a YAML file"""
        try:
            with open(rule_file, 'r') as f:
                data = yaml.safe_load(f)
            
            if not isinstance(data, dict):
                return
            
            rules_list = data.get("rules", [])
            if not rules_list:
                return
            
            # Determine language
            file_language = language or data.get("language") or "general"
            
            if file_language not in self.rules:
                self.rules[file_language] = []
            
            for rule_data in rules_list:
                rule = Rule(**rule_data)
                rule.language = rule.language or file_language
                self.rules[file_language].append(rule)
            
            logger.info("Loaded rules", file=str(rule_file), count=len(rules_list), language=file_language)
        except Exception as e:
            logger.error("Failed to load rules file", file=str(rule_file), error=str(e))
    
    def get_rules(self, language: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get rules for a language"""
        if language:
            rules = self.rules.get(language, []) + self.rules.get("general", [])
        else:
            # Return all rules
            rules = []
            for lang_rules in self.rules.values():
                rules.extend(lang_rules)
        
        # Filter enabled rules
        enabled_rules = [r for r in rules if r.enabled]
        
        return [rule.dict() for rule in enabled_rules]
    
    def add_rule(self, rule: Rule):
        """Add a new rule"""
        language = rule.language or "general"
        if language not in self.rules:
            self.rules[language] = []
        
        self.rules[language].append(rule)
        logger.info("Rule added", name=rule.name, language=language)
    
    def reload_rules(self):
        """Reload rules from files"""
        self.rules.clear()
        self._load_rules()


# Initialize rules manager
rules_manager = RulesManager(RULES_PATH)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "rules-engine"}


@app.get("/rules")
async def get_rules(language: Optional[str] = None):
    """Get coding rules"""
    rules = rules_manager.get_rules(language)
    return {"rules": rules, "count": len(rules)}


@app.post("/rules")
async def add_rule(rule: Rule):
    """Add a new rule"""
    rules_manager.add_rule(rule)
    return {"success": True, "rule": rule.dict()}


@app.post("/rules/reload")
async def reload_rules():
    """Reload rules from files"""
    rules_manager.reload_rules()
    return {"success": True, "message": "Rules reloaded"}


@app.get("/rules/{rule_name}")
async def get_rule(rule_name: str, language: Optional[str] = None):
    """Get a specific rule"""
    rules = rules_manager.get_rules(language)
    for rule in rules:
        if rule["name"] == rule_name:
            return rule
    
    raise HTTPException(status_code=404, detail="Rule not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

