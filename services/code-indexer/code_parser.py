"""
Code Parser - Parses code files into chunks for indexing
"""
from pathlib import Path
from typing import List, Dict, Any, Iterator
import structlog

logger = structlog.get_logger()


class CodeParser:
    """Parses code files into semantic chunks"""
    
    # Supported file extensions
    CODE_EXTENSIONS = {
        '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rs',
        '.cpp', '.c', '.h', '.hpp', '.cs', '.rb', '.php', '.swift',
        '.kt', '.scala', '.clj', '.sh', '.bash', '.zsh', '.yaml', '.yml',
        '.json', '.toml', '.ini', '.cfg', '.conf', '.md', '.rst'
    }
    
    # Files/directories to ignore
    IGNORE_PATTERNS = {
        '.git', '.svn', '.hg', '__pycache__', 'node_modules', '.venv',
        'venv', 'env', '.env', 'dist', 'build', '.pytest_cache',
        '.mypy_cache', '.ruff_cache', 'target', 'bin', 'obj', '.idea',
        '.vscode', '.vs', '*.pyc', '*.pyo', '*.pyd', '*.so', '*.egg'
    }
    
    def find_code_files(self, root: Path) -> Iterator[Path]:
        """Find all code files in directory"""
        if not root.exists() or not root.is_dir():
            return
        
        for item in root.rglob('*'):
            # Skip ignored patterns
            if any(pattern in str(item) for pattern in self.IGNORE_PATTERNS):
                continue
            
            # Check if it's a code file
            if item.is_file() and item.suffix in self.CODE_EXTENSIONS:
                yield item
    
    def parse_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parse a code file into chunks"""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            language = self._detect_language(file_path)
            
            # Parse based on language
            if language == 'python':
                return self._parse_python(content, file_path)
            elif language in ['javascript', 'typescript']:
                return self._parse_javascript(content, file_path, language)
            elif language == 'java':
                return self._parse_java(content, file_path)
            elif language == 'go':
                return self._parse_go(content, file_path)
            elif language == 'rust':
                return self._parse_rust(content, file_path)
            else:
                # Generic parsing for other languages
                return self._parse_generic(content, file_path, language)
        
        except Exception as e:
            logger.warning("Failed to parse file", file=str(file_path), error=str(e))
            return []
    
    def _detect_language(self, file_path: Path) -> str:
        """Detect programming language from file extension"""
        ext_to_lang = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.go': 'go',
            '.rs': 'rust',
            '.cpp': 'cpp',
            '.c': 'c',
            '.h': 'c',
            '.hpp': 'cpp',
            '.cs': 'csharp',
            '.rb': 'ruby',
            '.php': 'php',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.clj': 'clojure',
            '.sh': 'bash',
            '.bash': 'bash',
            '.zsh': 'bash',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.json': 'json',
            '.toml': 'toml',
            '.md': 'markdown',
            '.rst': 'rst'
        }
        return ext_to_lang.get(file_path.suffix, 'unknown')
    
    def _parse_python(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        """Parse Python file into functions, classes, and modules"""
        chunks = []
        lines = content.split('\n')
        
        current_chunk = None
        current_indent = 0
        chunk_start = 0
        
        for i, line in enumerate(lines, 1):
            stripped = line.lstrip()
            if not stripped or stripped.startswith('#'):
                continue
            
            indent = len(line) - len(stripped)
            
            # Function or class definition
            if stripped.startswith(('def ', 'class ', 'async def ')):
                # Save previous chunk
                if current_chunk:
                    chunks.append({
                        'content': '\n'.join(lines[chunk_start-1:i-1]),
                        'start_line': chunk_start,
                        'end_line': i-1,
                        'type': current_chunk,
                        'language': 'python'
                    })
                
                # Start new chunk
                current_chunk = 'function' if 'def' in stripped else 'class'
                chunk_start = i
                current_indent = indent
            
            # End of chunk (dedent)
            elif current_chunk and indent <= current_indent and stripped:
                if current_chunk:
                    chunks.append({
                        'content': '\n'.join(lines[chunk_start-1:i]),
                        'start_line': chunk_start,
                        'end_line': i,
                        'type': current_chunk,
                        'language': 'python'
                    })
                current_chunk = None
        
        # Add remaining chunk
        if current_chunk:
            chunks.append({
                'content': '\n'.join(lines[chunk_start-1:]),
                'start_line': chunk_start,
                'end_line': len(lines),
                'type': current_chunk,
                'language': 'python'
            })
        
        # If no chunks found, add entire file
        if not chunks:
            chunks.append({
                'content': content,
                'start_line': 1,
                'end_line': len(lines),
                'type': 'file',
                'language': 'python'
            })
        
        return chunks
    
    def _parse_javascript(self, content: str, file_path: Path, language: str) -> List[Dict[str, Any]]:
        """Parse JavaScript/TypeScript file"""
        chunks = []
        lines = content.split('\n')
        
        # Simple parsing: look for function/class definitions
        current_chunk = None
        chunk_start = 0
        brace_count = 0
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Function or class definition
            if any(keyword in stripped for keyword in ['function ', 'class ', 'const ', 'let ', 'export ', 'async function']):
                if current_chunk:
                    chunks.append({
                        'content': '\n'.join(lines[chunk_start-1:i-1]),
                        'start_line': chunk_start,
                        'end_line': i-1,
                        'type': current_chunk,
                        'language': language
                    })
                
                current_chunk = 'function' if 'function' in stripped else 'class' if 'class' in stripped else 'variable'
                chunk_start = i
                brace_count = stripped.count('{') - stripped.count('}')
            
            # Track braces
            brace_count += line.count('{') - line.count('}')
            
            # End of chunk
            if current_chunk and brace_count == 0 and '{' in line:
                chunks.append({
                    'content': '\n'.join(lines[chunk_start-1:i]),
                    'start_line': chunk_start,
                    'end_line': i,
                    'type': current_chunk,
                    'language': language
                })
                current_chunk = None
        
        # Add remaining
        if current_chunk:
            chunks.append({
                'content': '\n'.join(lines[chunk_start-1:]),
                'start_line': chunk_start,
                'end_line': len(lines),
                'type': current_chunk,
                'language': language
            })
        
        if not chunks:
            chunks.append({
                'content': content,
                'start_line': 1,
                'end_line': len(lines),
                'type': 'file',
                'language': language
            })
        
        return chunks
    
    def _parse_java(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        """Parse Java file"""
        return self._parse_generic(content, file_path, 'java')
    
    def _parse_go(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        """Parse Go file"""
        return self._parse_generic(content, file_path, 'go')
    
    def _parse_rust(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        """Parse Rust file"""
        return self._parse_generic(content, file_path, 'rust')
    
    def _parse_generic(self, content: str, file_path: Path, language: str) -> List[Dict[str, Any]]:
        """Generic parsing for any language"""
        # Split into chunks by functions/classes if possible
        # Otherwise, split by lines with a max chunk size
        lines = content.split('\n')
        max_chunk_size = 100  # lines per chunk
        
        chunks = []
        for i in range(0, len(lines), max_chunk_size):
            chunk_lines = lines[i:i+max_chunk_size]
            chunks.append({
                'content': '\n'.join(chunk_lines),
                'start_line': i + 1,
                'end_line': min(i + max_chunk_size, len(lines)),
                'type': 'code',
                'language': language
            })
        
        return chunks

