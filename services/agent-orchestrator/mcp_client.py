"""
MCP Client - Client for communicating with MCP servers
"""
import httpx
from typing import Dict, Any, Optional, List
import structlog

logger = structlog.get_logger()


class MCPClient:
    """Client for MCP (Model Context Protocol) servers"""
    
    def __init__(self, github_url: str, gitlab_url: str):
        self.github_url = github_url
        self.gitlab_url = gitlab_url
    
    async def get_repository_context(self, repo_url: str, 
                                    include_files: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get repository context from GitHub or GitLab
        
        Args:
            repo_url: Repository URL
            include_files: Specific files to include (optional)
        """
        if "github.com" in repo_url or "github.io" in repo_url:
            return await self._get_github_context(repo_url, include_files)
        elif "gitlab.com" in repo_url or "gitlab" in repo_url:
            return await self._get_gitlab_context(repo_url, include_files)
        else:
            logger.warning("Unknown repository host", url=repo_url)
            return {}
    
    async def _get_github_context(self, repo_url: str, 
                                 include_files: Optional[List[str]]) -> Dict[str, Any]:
        """Get context from GitHub repository"""
        try:
            async with httpx.AsyncClient() as client:
                # Parse repo URL
                repo_path = self._parse_repo_url(repo_url)
                
                # Get repository info
                response = await client.get(
                    f"{self.github_url}/api/repo/info",
                    params={"repo": repo_path}
                )
                response.raise_for_status()
                repo_info = response.json()
                
                # Get file contents if specified
                files = {}
                if include_files:
                    for file_path in include_files:
                        file_response = await client.get(
                            f"{self.github_url}/api/repo/file",
                            params={"repo": repo_path, "path": file_path}
                        )
                        if file_response.status_code == 200:
                            files[file_path] = file_response.json().get("content", "")
                
                return {
                    "repository": repo_info,
                    "files": files,
                    "url": repo_url
                }
        except Exception as e:
            logger.error("Failed to get GitHub context", error=str(e))
            return {}
    
    async def _get_gitlab_context(self, repo_url: str,
                                 include_files: Optional[List[str]]) -> Dict[str, Any]:
        """Get context from GitLab repository"""
        try:
            async with httpx.AsyncClient() as client:
                # Parse repo URL
                repo_path = self._parse_repo_url(repo_url)
                
                # Get repository info
                response = await client.get(
                    f"{self.gitlab_url}/api/repo/info",
                    params={"repo": repo_path}
                )
                response.raise_for_status()
                repo_info = response.json()
                
                # Get file contents if specified
                files = {}
                if include_files:
                    for file_path in include_files:
                        file_response = await client.get(
                            f"{self.gitlab_url}/api/repo/file",
                            params={"repo": repo_path, "path": file_path}
                        )
                        if file_response.status_code == 200:
                            files[file_path] = file_response.json().get("content", "")
                
                return {
                    "repository": repo_info,
                    "files": files,
                    "url": repo_url
                }
        except Exception as e:
            logger.error("Failed to get GitLab context", error=str(e))
            return {}
    
    def _parse_repo_url(self, repo_url: str) -> str:
        """Parse repository URL to get owner/repo path"""
        # Remove protocol
        repo_url = repo_url.replace("https://", "").replace("http://", "")
        
        # Remove .git suffix
        if repo_url.endswith(".git"):
            repo_url = repo_url[:-4]
        
        # Extract owner/repo
        if "github.com" in repo_url:
            parts = repo_url.split("github.com/")
            if len(parts) > 1:
                return parts[1].split("/")[0] + "/" + parts[1].split("/")[1]
        elif "gitlab.com" in repo_url:
            parts = repo_url.split("gitlab.com/")
            if len(parts) > 1:
                return parts[1]
        
        return repo_url
    
    async def push_to_repo(self, repo_url: str, branch: str, 
                          files: Dict[str, str], commit_message: str) -> bool:
        """Push changes to repository"""
        if "github.com" in repo_url:
            return await self._push_to_github(repo_url, branch, files, commit_message)
        elif "gitlab.com" in repo_url or "gitlab" in repo_url:
            return await self._push_to_gitlab(repo_url, branch, files, commit_message)
        return False
    
    async def _push_to_github(self, repo_url: str, branch: str,
                             files: Dict[str, str], commit_message: str) -> bool:
        """Push to GitHub"""
        try:
            async with httpx.AsyncClient() as client:
                repo_path = self._parse_repo_url(repo_url)
                response = await client.post(
                    f"{self.github_url}/api/repo/push",
                    json={
                        "repo": repo_path,
                        "branch": branch,
                        "files": files,
                        "commit_message": commit_message
                    }
                )
                response.raise_for_status()
                return True
        except Exception as e:
            logger.error("Failed to push to GitHub", error=str(e))
            return False
    
    async def _push_to_gitlab(self, repo_url: str, branch: str,
                             files: Dict[str, str], commit_message: str) -> bool:
        """Push to GitLab"""
        try:
            async with httpx.AsyncClient() as client:
                repo_path = self._parse_repo_url(repo_url)
                response = await client.post(
                    f"{self.gitlab_url}/api/repo/push",
                    json={
                        "repo": repo_path,
                        "branch": branch,
                        "files": files,
                        "commit_message": commit_message
                    }
                )
                response.raise_for_status()
                return True
        except Exception as e:
            logger.error("Failed to push to GitLab", error=str(e))
            return False
    
    async def pull_from_repo(self, repo_url: str, branch: str = "main") -> Dict[str, Any]:
        """Pull from repository"""
        if "github.com" in repo_url:
            return await self._pull_from_github(repo_url, branch)
        elif "gitlab.com" in repo_url or "gitlab" in repo_url:
            return await self._pull_from_gitlab(repo_url, branch)
        return {}
    
    async def _pull_from_github(self, repo_url: str, branch: str) -> Dict[str, Any]:
        """Pull from GitHub"""
        try:
            async with httpx.AsyncClient() as client:
                repo_path = self._parse_repo_url(repo_url)
                response = await client.get(
                    f"{self.github_url}/api/repo/pull",
                    params={"repo": repo_path, "branch": branch}
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error("Failed to pull from GitHub", error=str(e))
            return {}
    
    async def _pull_from_gitlab(self, repo_url: str, branch: str) -> Dict[str, Any]:
        """Pull from GitLab"""
        try:
            async with httpx.AsyncClient() as client:
                repo_path = self._parse_repo_url(repo_url)
                response = await client.get(
                    f"{self.gitlab_url}/api/repo/pull",
                    params={"repo": repo_path, "branch": branch}
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error("Failed to pull from GitLab", error=str(e))
            return {}

