"""
GitHub API client with authentication, caching, and rate limiting.

Provides methods for:
- Token validation
- Repository and branch operations
- File read/write operations
- Rate limiting and retry logic
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta

import aiohttp
from github import Github, GithubException, RateLimitExceededException
from github.Repository import Repository as GithubRepository
from github.Branch import Branch as GithubBranch
from github.ContentFile import ContentFile

from src.models.github import Repository, Branch, Commit, Feature
from src.models.auth import User, TokenScope
from src.services.storage import storage

logger = logging.getLogger(__name__)


class GitHubAPIError(Exception):
    """Base exception for GitHub API errors."""
    pass


class GitHubAuthenticationError(GitHubAPIError):
    """Raised when GitHub authentication fails."""
    pass


class GitHubRateLimitError(GitHubAPIError):
    """Raised when GitHub rate limit is exceeded."""
    pass


class GitHubClient:
    """
    Client for GitHub API operations with caching and rate limiting.
    
    Uses PyGithub for API operations and implements:
    - Token validation
    - Exponential backoff for rate limits
    - Response caching with TTL
    - Optimistic locking via file SHA
    """
    
    # Cache TTL values
    CACHE_TTL_REPOSITORIES = 300  # 5 minutes
    CACHE_TTL_BRANCHES = 60  # 1 minute
    CACHE_TTL_FILES = 30  # 30 seconds
    
    # Rate limit retry settings
    MAX_RETRIES = 3
    INITIAL_RETRY_DELAY = 1  # seconds
    MAX_RETRY_DELAY = 60  # seconds
    
    def __init__(self, token: str):
        """
        Initialize GitHub client with personal access token.
        
        Args:
            token: GitHub personal access token
        """
        self.token = token
        self._github = Github(token)
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session for async operations."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Accept": "application/vnd.github.v3+json"
                }
            )
        return self._session
    
    async def close(self):
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def _retry_with_backoff(self, func, *args, **kwargs):
        """
        Execute function with exponential backoff retry logic.
        
        Handles rate limiting (429) and transient errors (5xx).
        """
        delay = self.INITIAL_RETRY_DELAY
        
        for attempt in range(self.MAX_RETRIES):
            try:
                return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            
            except RateLimitExceededException as e:
                # GitHub rate limit exceeded
                if attempt == self.MAX_RETRIES - 1:
                    logger.error(f"Rate limit exceeded after {self.MAX_RETRIES} retries")
                    raise GitHubRateLimitError(f"GitHub rate limit exceeded: {str(e)}")
                
                # Get reset time from rate limit
                rate_limit = self._github.get_rate_limit()
                reset_time = rate_limit.core.reset
                wait_seconds = (reset_time - datetime.utcnow()).total_seconds()
                
                # Wait until rate limit resets (or max delay)
                wait_seconds = min(wait_seconds, self.MAX_RETRY_DELAY)
                logger.warning(f"Rate limit exceeded, waiting {wait_seconds}s until reset")
                await asyncio.sleep(wait_seconds)
            
            except GithubException as e:
                # Handle 5xx errors with exponential backoff
                if e.status >= 500:
                    if attempt == self.MAX_RETRIES - 1:
                        logger.error(f"GitHub API error after {self.MAX_RETRIES} retries: {e}")
                        raise GitHubAPIError(f"GitHub API error: {str(e)}")
                    
                    logger.warning(f"GitHub API error (attempt {attempt + 1}), retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
                    delay = min(delay * 2, self.MAX_RETRY_DELAY)
                else:
                    # 4xx errors are not retryable
                    raise GitHubAPIError(f"GitHub API error: {str(e)}")
            
            except Exception as e:
                logger.error(f"Unexpected error in GitHub API call: {e}")
                raise GitHubAPIError(f"Unexpected error: {str(e)}")
        
        raise GitHubAPIError(f"Failed after {self.MAX_RETRIES} retries")
    
    # ========================================================================
    # Authentication Operations
    # ========================================================================
    
    async def validate_token(self) -> Tuple[bool, Optional[User]]:
        """
        Validate GitHub token and get user information.
        
        Returns:
            Tuple of (is_valid, user_data)
        
        Raises:
            GitHubAuthenticationError: If token is invalid
            GitHubAPIError: If API call fails
        """
        try:
            async def _validate():
                github_user = self._github.get_user()
                
                # Attempt to fetch user data to validate token
                user_data = User(
                    id=github_user.id,
                    login=github_user.login,
                    name=github_user.name or github_user.login,
                    email=github_user.email,
                    avatar_url=github_user.avatar_url,
                    html_url=github_user.html_url,
                    type=github_user.type,
                    site_admin=github_user.site_admin,
                    public_repos=github_user.public_repos,
                    followers=github_user.followers,
                    following=github_user.following,
                    created_at=github_user.created_at
                )
                
                return True, user_data
            
            return await self._retry_with_backoff(_validate)
        
        except GithubException as e:
            if e.status == 401:
                logger.warning("Invalid GitHub token")
                raise GitHubAuthenticationError("Invalid GitHub token")
            raise GitHubAPIError(f"Failed to validate token: {str(e)}")
    
    def get_token_scopes(self) -> List[TokenScope]:
        """
        Get scopes associated with the token.
        
        Returns:
            List of TokenScope enums
        """
        # PyGithub doesn't expose OAuth scopes directly
        # We'll verify minimum required scopes through capability checks
        scopes = []
        
        try:
            # Check repo scope
            user = self._github.get_user()
            repos = user.get_repos(affiliation="owner", max_results=1)
            list(repos)  # Force evaluation
            scopes.append(TokenScope.REPO)
        except:
            pass
        
        try:
            # Check user scope
            user = self._github.get_user()
            _ = user.email
            scopes.append(TokenScope.USER)
        except:
            pass
        
        return scopes
    
    # ========================================================================
    # Repository Operations
    # ========================================================================
    
    async def get_repositories(
        self,
        visibility: Optional[str] = None,
        sort: str = "updated",
        page: int = 1,
        per_page: int = 30,
        use_cache: bool = True
    ) -> List[Repository]:
        """
        Get user's repositories with caching.
        
        Args:
            visibility: Filter by "public", "private", or None for all
            sort: Sort by "created", "updated", "pushed", "full_name"
            page: Page number (1-indexed)
            per_page: Results per page (max 100)
            use_cache: Whether to use cached results
        
        Returns:
            List of Repository models
        """
        cache_key = f"repos:{visibility}:{sort}:{page}:{per_page}"
        
        # Check cache
        if use_cache:
            cached = storage.cache_get(cache_key)
            if cached:
                logger.debug(f"Cache hit for repositories: {cache_key}")
                return cached
        
        async def _get_repos():
            user = self._github.get_user()
            
            # Get repositories
            # Note: PyGithub uses 'type' parameter, not 'visibility'
            github_repos = user.get_repos(
                type=visibility or "all",
                sort=sort
            )
            
            # Convert to Repository models (paginated)
            repos = []
            for i, repo in enumerate(github_repos):
                # Manual pagination
                if i < (page - 1) * per_page:
                    continue
                if i >= page * per_page:
                    break
                
                repos.append(self._convert_repository(repo))
            
            return repos
        
        repos = await self._retry_with_backoff(_get_repos)
        
        # Cache results
        storage.cache_set(cache_key, repos, ttl_seconds=self.CACHE_TTL_REPOSITORIES)
        
        return repos
    
    def _convert_repository(self, github_repo: GithubRepository) -> Repository:
        """Convert PyGithub Repository to our Repository model."""
        return Repository(
            id=github_repo.id,
            node_id=github_repo.node_id,
            name=github_repo.name,
            full_name=github_repo.full_name,
            owner={
                "login": github_repo.owner.login,
                "id": github_repo.owner.id,
                "avatar_url": github_repo.owner.avatar_url,
                "type": github_repo.owner.type
            },
            private=github_repo.private,
            description=github_repo.description,
            html_url=github_repo.html_url,
            clone_url=github_repo.clone_url,
            git_url=github_repo.git_url,
            ssh_url=github_repo.ssh_url,
            default_branch=github_repo.default_branch,
            created_at=github_repo.created_at,
            updated_at=github_repo.updated_at,
            pushed_at=github_repo.pushed_at,
            size=github_repo.size,
            stargazers_count=github_repo.stargazers_count,
            watchers_count=github_repo.watchers_count,
            forks_count=github_repo.forks_count,
            open_issues_count=github_repo.open_issues_count,
            has_issues=github_repo.has_issues,
            has_projects=getattr(github_repo, "has_projects", False),
            has_wiki=github_repo.has_wiki,
            has_pages=getattr(github_repo, "has_pages", False),
            has_downloads=getattr(github_repo, "has_downloads", False),
            archived=github_repo.archived,
            disabled=getattr(github_repo, "disabled", False),
            visibility=getattr(github_repo, "visibility", "private" if github_repo.private else "public"),
            permissions=getattr(github_repo, "permissions", None),
            language=github_repo.language,
            topics=github_repo.get_topics() if hasattr(github_repo, "get_topics") else []
        )
    
    # ========================================================================
    # Branch Operations
    # ========================================================================
    
    async def get_branches(self, repo_full_name: str, use_cache: bool = True) -> List[Branch]:
        """
        Get branches for a repository.
        
        Args:
            repo_full_name: Repository full name (owner/repo)
            use_cache: Whether to use cached results
        
        Returns:
            List of Branch models
        """
        cache_key = f"branches:{repo_full_name}"
        
        # Check cache
        if use_cache:
            cached = storage.cache_get(cache_key)
            if cached:
                logger.debug(f"Cache hit for branches: {cache_key}")
                return cached
        
        async def _get_branches():
            repo = self._github.get_repo(repo_full_name)
            github_branches = repo.get_branches()
            
            branches = [
                Branch(
                    name=branch.name,
                    commit=Commit(
                        sha=branch.commit.sha,
                        url=branch.commit.url
                    ),
                    protected=branch.protected,
                    protection_url=branch.protection_url if hasattr(branch, "protection_url") else None
                )
                for branch in github_branches
            ]
            
            return branches
        
        branches = await self._retry_with_backoff(_get_branches)
        
        # Cache results
        storage.cache_set(cache_key, branches, ttl_seconds=self.CACHE_TTL_BRANCHES)
        storage.save_branches(repo_full_name, branches)
        
        return branches
    
    async def create_branch(self, repo_full_name: str, branch_name: str, from_branch: str = "main") -> Branch:
        """
        Create a new branch.
        
        Args:
            repo_full_name: Repository full name (owner/repo)
            branch_name: Name for the new branch
            from_branch: Base branch to create from
        
        Returns:
            Created Branch model
        
        Raises:
            GitHubAPIError: If branch creation fails
        """
        async def _create():
            repo = self._github.get_repo(repo_full_name)
            
            # Get base branch
            base_branch = repo.get_branch(from_branch)
            base_sha = base_branch.commit.sha
            
            # Create new branch reference
            ref = repo.create_git_ref(
                ref=f"refs/heads/{branch_name}",
                sha=base_sha
            )
            
            # Get the created branch
            new_branch = repo.get_branch(branch_name)
            
            # Invalidate cache
            storage.cache_invalidate(f"branches:{repo_full_name}")
            
            return Branch(
                name=new_branch.name,
                commit=Commit(
                    sha=new_branch.commit.sha,
                    url=new_branch.commit.url
                ),
                protected=new_branch.protected,
                protection_url=new_branch.protection_url if hasattr(new_branch, "protection_url") else None
            )
        
        return await self._retry_with_backoff(_create)
    
    # ========================================================================
    # File Operations
    # ========================================================================
    
    async def read_file(self, repo_full_name: str, path: str, branch: str = "main", use_cache: bool = True) -> Tuple[str, str]:
        """
        Read file contents from repository.
        
        Args:
            repo_full_name: Repository full name (owner/repo)
            path: File path in repository
            branch: Branch name
            use_cache: Whether to use cached results
        
        Returns:
            Tuple of (content, sha) for optimistic locking
        
        Raises:
            GitHubAPIError: If file read fails
        """
        cache_key = f"file:{repo_full_name}:{branch}:{path}"
        
        # Check cache
        if use_cache:
            cached = storage.cache_get(cache_key)
            if cached:
                logger.debug(f"Cache hit for file: {cache_key}")
                return cached
        
        async def _read():
            repo = self._github.get_repo(repo_full_name)
            
            try:
                file_content = repo.get_contents(path, ref=branch)
                
                if isinstance(file_content, list):
                    raise GitHubAPIError(f"Path is a directory, not a file: {path}")
                
                content = file_content.decoded_content.decode('utf-8')
                sha = file_content.sha
                
                return content, sha
            
            except GithubException as e:
                if e.status == 404:
                    raise GitHubAPIError(f"File not found: {path}")
                raise
        
        result = await self._retry_with_backoff(_read)
        
        # Cache results
        storage.cache_set(cache_key, result, ttl_seconds=self.CACHE_TTL_FILES)
        
        return result
    
    async def write_file(
        self,
        repo_full_name: str,
        path: str,
        content: str,
        message: str,
        branch: str = "main",
        sha: Optional[str] = None
    ) -> str:
        """
        Write file contents to repository.
        
        Args:
            repo_full_name: Repository full name (owner/repo)
            path: File path in repository
            content: File content to write
            message: Commit message
            branch: Branch name
            sha: Existing file SHA for optimistic locking (None for new files)
        
        Returns:
            New file SHA
        
        Raises:
            GitHubAPIError: If file write fails or SHA mismatch
        """
        async def _write():
            repo = self._github.get_repo(repo_full_name)
            
            try:
                if sha:
                    # Update existing file
                    result = repo.update_file(
                        path=path,
                        message=message,
                        content=content,
                        sha=sha,
                        branch=branch
                    )
                else:
                    # Create new file
                    result = repo.create_file(
                        path=path,
                        message=message,
                        content=content,
                        branch=branch
                    )
                
                # Invalidate cache
                cache_key = f"file:{repo_full_name}:{branch}:{path}"
                storage.cache_invalidate(cache_key)
                
                return result["content"].sha
            
            except GithubException as e:
                if e.status == 409:
                    raise GitHubAPIError(f"File SHA mismatch (optimistic locking conflict): {path}")
                elif e.status == 422:
                    raise GitHubAPIError(f"Invalid file content or path: {path}")
                raise
        
        return await self._retry_with_backoff(_write)
    
    async def get_file_sha(self, repo_full_name: str, path: str, branch: str = "main") -> Optional[str]:
        """
        Get file SHA without reading full contents.
        
        Args:
            repo_full_name: Repository full name (owner/repo)
            path: File path in repository
            branch: Branch name
        
        Returns:
            File SHA or None if file doesn't exist
        """
        try:
            _, sha = await self.read_file(repo_full_name, path, branch, use_cache=False)
            return sha
        except GitHubAPIError:
            return None
    
    # ========================================================================
    # Rate Limit Information
    # ========================================================================
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """
        Get current rate limit status.
        
        Returns:
            Dict with rate limit information
        """
        rate_limit = self._github.get_rate_limit()
        
        return {
            "core": {
                "limit": rate_limit.core.limit,
                "remaining": rate_limit.core.remaining,
                "reset": rate_limit.core.reset,
                "used": rate_limit.core.used
            },
            "search": {
                "limit": rate_limit.search.limit,
                "remaining": rate_limit.search.remaining,
                "reset": rate_limit.search.reset,
                "used": rate_limit.search.used
            }
        }
