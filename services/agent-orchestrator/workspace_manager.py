"""
Workspace Manager - Manages file operations in the workspace
"""
import os
import aiofiles
from pathlib import Path
from typing import Optional, List, Dict, Any
import structlog

logger = structlog.get_logger()


class WorkspaceManager:
    """Manages workspace file operations"""
    
    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)
        self.workspace_path.mkdir(parents=True, exist_ok=True)
    
    async def initialize(self):
        """Initialize workspace"""
        logger.info("Initializing workspace", path=str(self.workspace_path))
        self.workspace_path.mkdir(parents=True, exist_ok=True)
    
    async def read_file(self, file_path: str) -> Optional[str]:
        """Read a file from workspace"""
        full_path = self.workspace_path / file_path.lstrip("/")
        
        if not full_path.exists():
            logger.warning("File not found", path=str(full_path))
            return None
        
        if not full_path.is_file():
            logger.warning("Path is not a file", path=str(full_path))
            return None
        
        try:
            async with aiofiles.open(full_path, 'r', encoding='utf-8') as f:
                return await f.read()
        except Exception as e:
            logger.error("Failed to read file", path=str(full_path), error=str(e))
            return None
    
    async def write_file(self, file_path: str, content: str) -> bool:
        """Write a file to workspace"""
        full_path = self.workspace_path / file_path.lstrip("/")
        
        # Create parent directories
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            async with aiofiles.open(full_path, 'w', encoding='utf-8') as f:
                await f.write(content)
            logger.info("File written", path=str(full_path))
            return True
        except Exception as e:
            logger.error("Failed to write file", path=str(full_path), error=str(e))
            return False
    
    async def list_files(self, directory: str = "", recursive: bool = False) -> List[str]:
        """List files in workspace"""
        dir_path = self.workspace_path / directory.lstrip("/")
        
        if not dir_path.exists():
            return []
        
        files = []
        if recursive:
            for file_path in dir_path.rglob("*"):
                if file_path.is_file():
                    files.append(str(file_path.relative_to(self.workspace_path)))
        else:
            for file_path in dir_path.iterdir():
                if file_path.is_file():
                    files.append(str(file_path.relative_to(self.workspace_path)))
        
        return files
    
    async def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get file information"""
        full_path = self.workspace_path / file_path.lstrip("/")
        
        if not full_path.exists():
            return None
        
        stat = full_path.stat()
        return {
            "path": file_path,
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "is_file": full_path.is_file(),
            "is_directory": full_path.is_dir()
        }
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete a file"""
        full_path = self.workspace_path / file_path.lstrip("/")
        
        if not full_path.exists():
            return False
        
        try:
            if full_path.is_file():
                full_path.unlink()
            else:
                # For directories, use shutil
                import shutil
                shutil.rmtree(full_path)
            logger.info("File deleted", path=str(full_path))
            return True
        except Exception as e:
            logger.error("Failed to delete file", path=str(full_path), error=str(e))
            return False

