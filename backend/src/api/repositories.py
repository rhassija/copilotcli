"""
Repository API endpoints.

Provides:
- Repository listing with search/filter
- Branch listing and creation
- Feature/branch management
- Feature persistence and tracking
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query, Header
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import logging
import uuid
import os
import subprocess
import json
import shutil
import tempfile
from pathlib import Path

from src.models.github import Repository, Branch, Feature, FeatureStatus, Commit
from src.models.auth import User
from src.services.github_client import GitHubClient, GitHubAPIError, GitHubAuthenticationError
from src.services.auth_service import auth_service
from src.services.storage import storage
from src.services.copilot_runner import CopilotRunner, SubprocessError
from src.services.document_generator import DocumentGenerator
from src.utils.error_handlers import create_error_response

router = APIRouter(prefix="/api/v1/repos", tags=["repositories"])
logger = logging.getLogger(__name__)


# ========================================================================
# Dependency: Get GitHub Client from Session
# ========================================================================

async def get_github_client(
    x_session_id: str = Header(..., description="Session ID")
) -> GitHubClient:
    """
    Get authenticated GitHub client from session.
    
    Args:
        x_session_id: Session ID from X-Session-ID header
    
    Returns:
        GitHubClient instance with user's token
    
    Raises:
        HTTPException: If session invalid or token missing
    """
    token = auth_service.get_session_token(x_session_id)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session"
        )
    
    return GitHubClient(token)


# ========================================================================
# Request/Response Models
# ========================================================================

class RepositoryListResponse(BaseModel):
    """Response for repository listing."""
    repositories: List[Repository]
    total_count: int
    page: int
    per_page: int
    has_next: bool


class BranchListResponse(BaseModel):
    """Response for branch listing."""
    branches: List[Branch]
    repository: str
    total_count: int


class CreateBranchRequest(BaseModel):
    """Request to create a new branch."""
    branch_name: Optional[str] = Field(None, description="Name for the new branch (auto-generated if not provided)", min_length=1, max_length=255)
    from_branch: str = Field(default="main", description="Base branch to create from")
    feature_title: str = Field(..., description="Feature title/description", min_length=1)


class CreateBranchResponse(BaseModel):
    """Response from branch creation."""
    branch: Branch
    feature_id: str
    message: str = "Branch created successfully"
    documents_initialized: bool = False
    spec_path: Optional[str] = None
    plan_path: Optional[str] = None
    task_path: Optional[str] = None


class FeatureListResponse(BaseModel):
    """Response for feature listing."""
    features: List[Feature]
    repository: Optional[str] = None
    total_count: int


# ========================================================================
# T087-T088: Repository Listing Endpoint
# ========================================================================

@router.get("", response_model=RepositoryListResponse, status_code=status.HTTP_200_OK)
async def list_repositories(
    visibility: Optional[str] = Query(None, description="Filter by visibility: public, private, or all"),
    sort: str = Query("updated", description="Sort by: created, updated, pushed, full_name"),
    search: Optional[str] = Query(None, description="Search by repository name (case-insensitive)"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    per_page: int = Query(30, ge=1, le=100, description="Results per page (max 100)"),
    use_cache: bool = Query(True, description="Use cached results (5 min TTL)"),
    github_client: GitHubClient = Depends(get_github_client)
):
    """
    List user's repositories with search, filter, and pagination.
    
    Implements T087-T088:
    - Fetches repositories from GitHub API
    - Supports search by name
    - Supports filter by visibility
    - Supports sorting
    - Returns paginated results
    - Uses 5-minute cache (T089)
    
    Args:
        visibility: Filter by "public", "private", or None for all
        sort: Sort by "created", "updated", "pushed", "full_name"
        search: Search term for repository name
        page: Page number
        per_page: Results per page
        use_cache: Whether to use cached results
        github_client: Authenticated GitHub client (from dependency)
    
    Returns:
        RepositoryListResponse with repositories and pagination info
    """
    try:
        # Get repositories from GitHub (with cache)
        repos = await github_client.get_repositories(
            visibility=visibility,
            sort=sort,
            page=page,
            per_page=per_page,
            use_cache=use_cache
        )
        
        # Apply search filter if provided
        if search:
            search_lower = search.lower()
            repos = [
                repo for repo in repos
                if search_lower in repo.name.lower() or 
                   (repo.description and search_lower in repo.description.lower())
            ]
        
        total_count = len(repos)
        has_next = len(repos) == per_page  # Simple heuristic
        
        logger.info(f"Listed {total_count} repositories (page {page}, search='{search}')")
        
        return RepositoryListResponse(
            repositories=repos,
            total_count=total_count,
            page=page,
            per_page=per_page,
            has_next=has_next
        )
        
    except GitHubAuthenticationError as e:
        logger.error(f"GitHub authentication failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"GitHub authentication failed: {str(e)}"
        )
    except GitHubAPIError as e:
        logger.error(f"GitHub API error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"GitHub API error: {str(e)}"
        )
    except Exception as e:
        logger.exception(f"Unexpected error listing repositories: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list repositories: {str(e)}"
        )


# ========================================================================
# T090: Branch Listing Endpoint
# ========================================================================

@router.get("/{owner}/{repo}/branches", response_model=BranchListResponse, status_code=status.HTTP_200_OK)
async def list_branches(
    owner: str,
    repo: str,
    use_cache: bool = Query(True, description="Use cached results (1 min TTL)"),
    github_client: GitHubClient = Depends(get_github_client)
):
    """
    List branches for a repository.
    
    Implements T090:
    - Fetches branches from GitHub API
    - Returns branch list with commit SHAs
    - Uses 1-minute cache
    
    Args:
        owner: Repository owner
        repo: Repository name
        use_cache: Whether to use cached results
        github_client: Authenticated GitHub client
    
    Returns:
        BranchListResponse with branches
    """
    try:
        repo_full_name = f"{owner}/{repo}"
        branches = await github_client.get_branches(repo_full_name, use_cache=use_cache)
        
        logger.info(f"Listed {len(branches)} branches for {repo_full_name}")
        
        return BranchListResponse(
            branches=branches,
            repository=repo_full_name,
            total_count=len(branches)
        )
        
    except GitHubAuthenticationError as e:
        logger.error(f"GitHub authentication failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"GitHub authentication failed: {str(e)}"
        )
    except GitHubAPIError as e:
        logger.error(f"GitHub API error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository not found or inaccessible: {str(e)}"
        )
    except Exception as e:
        logger.exception(f"Unexpected error listing branches: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list branches: {str(e)}"
        )


# ========================================================================
# T091-T092: Branch/Feature Creation Endpoint
# ========================================================================

@router.post("/{owner}/{repo}/branches", response_model=CreateBranchResponse, status_code=status.HTTP_201_CREATED)
async def create_branch(
    owner: str,
    repo: str,
    request: CreateBranchRequest,
    x_session_id: str = Header(..., description="Session ID"),
    github_client: GitHubClient = Depends(get_github_client)
):
    """
    Create a new feature branch with Speckit.
    
    Workflow (simplified):
    1. Call Speckit create-new-feature.sh script to create branch
    2. Initialize directory structure (documents created via Generate buttons in UI)
    3. Track feature in storage
    
    Note: Spec/plan/task generation moved to document endpoints (Generate buttons)
    to avoid frontend timeout during branch creation.
    
    Args:
        owner: Repository owner
        repo: Repository name
        request: Branch creation request with feature title
        x_session_id: Session ID for user context
        github_client: Authenticated GitHub client
    
    Returns:
        CreateBranchResponse with branch and feature details
    """
    try:
        repo_full_name = f"{owner}/{repo}"
        session = auth_service.get_session(x_session_id) if x_session_id else None
        feature_id = f"feat_{uuid.uuid4().hex[:16]}"
        
        # Get user from session
        session = auth_service.get_session(x_session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session"
            )
        
        # Get token for GitHub operations
        token = auth_service.get_session_token(x_session_id)
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to retrieve authentication token"
            )
        
        # Step 1: Use Speckit script to create branch structure
        branch_name = request.branch_name
        if not branch_name:
            # If branch_name not provided, generate from feature title
            logger.info(f"Auto-generating branch name from feature title")
            import re
            branch_name = "feature/" + re.sub(r'[^a-z0-9]+', '-', request.feature_title.lower())[:50]
        
        logger.info(f"Creating feature branch via Speckit: {branch_name}")
        
        # Path to Speckit script (from app repo)
        app_repo_root = Path(__file__).parent.parent.parent.parent
        speckit_script = app_repo_root / ".specify/scripts/bash/create-new-feature.sh"
        speckit_dir = app_repo_root / ".specify"
        
        if not speckit_script.exists():
            logger.warning(f"Speckit script not found at {speckit_script}, using direct GitHub API")
            # Fallback: create branch directly
            branch = await github_client.create_branch(
                repo_full_name=repo_full_name,
                branch_name=branch_name,
                from_branch=request.from_branch
            )
            spec_file_path = f"specs/{branch_name}/spec.md"
            plan_file_path = f"specs/{branch_name}/plan.md"
            task_file_path = f"specs/{branch_name}/tasks.md"
        else:
            # Use Speckit script (preferred) in the selected repo
            cmd = ["bash", str(speckit_script), "--json"]
            if branch_name:
                cmd.extend(["--short-name", branch_name.replace("feature/", "")])
            cmd.append(request.feature_title)  # Use feature title as argument
            
            # Prepare environment for git operations
            env = os.environ.copy()
            env["GH_TOKEN"] = token
            env["GITHUB_TOKEN"] = token
            env["GIT_TERMINAL_PROMPT"] = "0"
            env["GIT_ASKPASS"] = "echo"
            
            # Clone the selected repo to a temporary workspace
            with tempfile.TemporaryDirectory(prefix="speckit-") as temp_dir:
                temp_repo_root = Path(temp_dir) / "repo"
                clone_url = f"https://x-access-token:{token}@github.com/{repo_full_name}.git"
                clone_cmd = [
                    "git",
                    "clone",
                    "--depth",
                    "1",
                    "--branch",
                    request.from_branch,
                    clone_url,
                    str(temp_repo_root)
                ]
                
                clone_result = subprocess.run(
                    clone_cmd,
                    capture_output=True,
                    text=True,
                    env=env
                )
                if clone_result.returncode != 0:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Failed to clone target repository: {clone_result.stderr}"
                    )
                
                # Ensure .specify exists in the target repo for templates/scripts
                if not (temp_repo_root / ".specify").exists():
                    shutil.copytree(speckit_dir, temp_repo_root / ".specify", dirs_exist_ok=True)
                
                # Configure git identity for commit
                git_user_name = session.user.name or session.user.login
                git_user_email = session.user.email or f"{session.user.login}@users.noreply.github.com"
                subprocess.run(
                    ["git", "-C", str(temp_repo_root), "config", "user.name", git_user_name],
                    capture_output=True,
                    text=True
                )
                subprocess.run(
                    ["git", "-C", str(temp_repo_root), "config", "user.email", git_user_email],
                    capture_output=True,
                    text=True
                )
                
                logger.info("Running Speckit in selected repo...")
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=str(temp_repo_root),
                    env=env
                )
                
                stdout, stderr = process.communicate()
                
                logger.info(f"Speckit stdout: {stdout[:200]}")
                if stderr:
                    logger.warning(f"Speckit stderr: {stderr[:200]}")
                
                # Parse JSON output from Speckit
                branch_created = False
                spec_file_path = None
                for line in stdout.split("\n"):
                    if line.strip().startswith("{"):
                        try:
                            data = json.loads(line)
                            if "BRANCH_NAME" in data:
                                branch_name = data["BRANCH_NAME"]
                                branch_created = True
                                logger.info(f"Speckit created branch: {branch_name}")
                            if "SPEC_FILE" in data:
                                spec_file_path = data["SPEC_FILE"]
                        except json.JSONDecodeError:
                            pass
                
                if not branch_created or not spec_file_path:
                    logger.error(f"Speckit failed - stdout: {stdout[:500]}, stderr: {stderr[:500]}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Speckit script failed: {stderr or 'Unknown error'}"
                    )
                
                # Normalize paths to repo-relative (handle /private prefix on macOS)
                spec_path_obj = Path(spec_file_path)
                if spec_path_obj.is_absolute():
                    spec_path_obj_resolved = spec_path_obj.resolve()
                    temp_repo_resolved = temp_repo_root.resolve()
                    try:
                        spec_path_obj = spec_path_obj_resolved.relative_to(temp_repo_resolved)
                    except ValueError:
                        # Fallback: strip /private prefix if present
                        spec_str = str(spec_path_obj_resolved)
                        temp_str = str(temp_repo_resolved)
                        if spec_str.startswith("/private") and not temp_str.startswith("/private"):
                            spec_str = spec_str[len("/private"):]
                        if temp_str.startswith("/private") and not spec_str.startswith("/private"):
                            temp_str = temp_str[len("/private"):]
                        spec_path_obj = Path(spec_str).relative_to(Path(temp_str))
                spec_file_path = spec_path_obj.as_posix()
                spec_dir = spec_path_obj.parent
                plan_file_path = str(spec_dir / "plan.md")
                task_file_path = str(spec_dir / "tasks.md")
                
                # Skip enrichment during branch creation - moved to Generate button in UI
                # This avoids timeout issues by keeping branch creation fast
                logger.info("Branch created - spec generation will be handled via UI Generate button")
                
                # Commit the empty directory structure from Speckit
                commit_message = f"Initialize feature: {request.feature_title}"
                subprocess.run(
                    ["git", "-C", str(temp_repo_root), "add", str(spec_dir)],
                    capture_output=True,
                    text=True
                )
                commit_result = subprocess.run(
                    ["git", "-C", str(temp_repo_root), "commit", "-m", commit_message],
                    capture_output=True,
                    text=True
                )
                if commit_result.returncode != 0 and "nothing to commit" not in (commit_result.stderr or "").lower():
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Failed to commit feature structure: {commit_result.stderr}"
                    )
                
                # Push the branch to GitHub
                push_cmd = ["git", "-C", str(temp_repo_root), "push", "-u", "origin", branch_name]
                push_result = subprocess.run(
                    push_cmd,
                    capture_output=True,
                    text=True,
                    env=env
                )
                if push_result.returncode != 0:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Failed to push branch to GitHub: {push_result.stderr}"
                    )
                logger.info(f"Branch {branch_name} pushed to GitHub successfully")
            
            # Speckit already created the branch and pushed to GitHub
            # Just construct a Branch object with the branch name
            branch = Branch(
                name=branch_name,
                commit=Commit(
                    sha="0000000000000000000000000000000000000000",  # Placeholder SHA (40 chars required)
                    url=f"https://api.github.com/repos/{repo_full_name}/commits/0000000000000000000000000000000000000000"
                ),
                protected=False,
                protection_url=None
            )
            logger.info(f"Branch created by Speckit: {branch_name}")
        
        # Step 2: Directory structure created by Speckit
        # Document generation moved to UI Generate buttons (no timeout)
        documents_initialized = False
        spec_file_path = f"specs/{branch_name}/spec.md"
        plan_file_path = None  # Not generated during branch creation
        task_file_path = None  # Not generated during branch creation
        
        logger.info("Feature branch created - documents can be generated via UI Generate buttons")
        
        # Step 3: Create Feature model and persist
        feature = Feature(
            feature_id=feature_id,
            repository_full_name=repo_full_name,
            branch_name=branch_name,
            base_branch=request.from_branch,
            title=request.feature_title,
            status=FeatureStatus.ACTIVE,
            created_by_user_id=session.user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            spec_path=spec_file_path,
            plan_path=plan_file_path if documents_initialized else None,
            task_path=task_file_path if documents_initialized else None
        )
        
        storage.save_feature(feature)
        logger.info(f"Feature {feature_id} saved to storage")
        
        return CreateBranchResponse(
            branch=branch,
            feature_id=feature_id,
            message=f"Branch '{branch_name}' created successfully. Use Generate buttons to create documents.",
            documents_initialized=documents_initialized,
            spec_path=spec_file_path,
            plan_path=plan_file_path,
            task_path=task_file_path
        )
        
    except subprocess.TimeoutExpired:
        logger.error("Speckit script timeout")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Feature creation timed out"
        )
    except GitHubAPIError as e:
        logger.error(f"GitHub API error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create branch: {str(e)}"
        )
    except Exception as e:
        logger.exception(f"Unexpected error creating branch: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create branch: {str(e)}"
        )


# ========================================================================
# T094: Feature Listing Endpoint
# ========================================================================

@router.get("/{owner}/{repo}/features", response_model=FeatureListResponse, status_code=status.HTTP_200_OK)
async def list_features(
    owner: str,
    repo: str,
    status_filter: Optional[str] = Query(None, description="Filter by feature status"),
    x_session_id: Optional[str] = Header(None, description="Session ID")
):
    """
    List features for a repository.
    
    Implements T094:
    - Returns features filtered by repository
    - Optionally filters by status
    - Returns feature metadata
    - NOTE: Session ID is optional for MVP simplicity
    
    Args:
        owner: Repository owner
        repo: Repository name
        status_filter: Optional status filter (active, in_progress, etc.)
        x_session_id: Optional session ID (for auth validation in future)
    
    Returns:
        FeatureListResponse with features
    """
    try:
        repo_full_name = f"{owner}/{repo}"
        
        # Log the request for debugging
        session_info = f"Session: {x_session_id[:16]}..." if x_session_id else "No session"
        logger.info(f"LIST_FEATURES: {repo_full_name} | {session_info}")
        
        # Get ALL features to debug
        all_features = storage.list_features()
        logger.info(f"DEBUG: Total features in storage: {len(all_features)}")
        for f in all_features:
            logger.info(f"  - Feature: {f.feature_id} | Repo: {f.repository_full_name} | Branch: {f.branch_name} | Title: {f.title}")
        
        # Get features from storage (filtered by repository)
        features = storage.list_features(repository_full_name=repo_full_name)
        logger.info(f"DEBUG: Found {len(features)} features for {repo_full_name}")

        # Sync stored features with live GitHub branches when session is available.
        # This prevents deleted branches from lingering in the UX.
        if x_session_id:
            try:
                token = auth_service.get_session_token(x_session_id)
                if token:
                    github_client = GitHubClient(token)
                    live_branches = await github_client.get_branches(repo_full_name, use_cache=False)
                    live_branch_names = {branch.name for branch in live_branches}

                    stale_features = [f for f in features if f.branch_name not in live_branch_names]
                    if stale_features:
                        for stale_feature in stale_features:
                            storage.delete_feature(stale_feature.feature_id)
                        features = [f for f in features if f.branch_name in live_branch_names]
                        logger.info(
                            f"Pruned {len(stale_features)} stale features for {repo_full_name} "
                            f"(deleted branches no longer in GitHub)"
                        )
            except Exception as sync_error:
                # Do not fail feature listing if GitHub sync check fails.
                logger.warning(f"Feature sync with GitHub branches skipped: {str(sync_error)}")
        
        # If no tracked features are found in storage, bootstrap from repo specs directory.
        # This makes fresh environments (like Docker) show existing specs/docs from GitHub.
        if not features and x_session_id:
            logger.info(f"Bootstrap triggered for {repo_full_name} - attempting GitHub discovery")
            try:
                session = storage.get_session(x_session_id)
                token = auth_service.get_session_token(x_session_id)
                if token:
                    github_client = GitHubClient(token)
                    discovered_features = await github_client.discover_features_from_specs(
                        repo_full_name=repo_full_name,
                        created_by_user_id=session.user.id if session else 0,
                    )

                    if discovered_features:
                        for discovered in discovered_features:
                            storage.save_feature(discovered)
                        features = storage.list_features(repository_full_name=repo_full_name)
                        logger.info(
                            f"Bootstrapped {len(discovered_features)} features from specs directory for {repo_full_name}"
                        )
                    else:
                        logger.info(f"No specs found in {repo_full_name} - repository may not have specs/ directory")
            except Exception as bootstrap_error:
                logger.warning(f"Feature bootstrap from specs skipped: {str(bootstrap_error)}")

        # Apply status filter if provided
        if status_filter:
            features = [
                f for f in features
                if f.status.value == status_filter
            ]
        
        logger.info(f"Listed {len(features)} features for {repo_full_name} (status={status_filter})")
        
        return FeatureListResponse(
            features=features,
            repository=repo_full_name,
            total_count=len(features)
        )
        
    except Exception as e:
        logger.exception(f"Unexpected error listing features: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list features: {str(e)}"
        )


# ========================================================================
# Additional Helper Endpoint: Get All Features (for dashboard)
# ========================================================================

@router.get("/features", response_model=FeatureListResponse, status_code=status.HTTP_200_OK)
async def list_all_features(
    repository: Optional[str] = Query(None, description="Filter by repository (owner/repo)"),
    status_filter: Optional[str] = Query(None, description="Filter by feature status"),
    x_session_id: str = Header(..., description="Session ID")
):
    """
    List all features across repositories for authenticated user.
    
    Args:
        repository: Optional repository filter (owner/repo)
        status_filter: Optional status filter
        github_client: Authenticated GitHub client
    
    Returns:
        FeatureListResponse with features
    """
    try:
        # Get features from storage
        features = storage.list_features(repository_full_name=repository)
        
        # If storage is empty or has only local/specs features, discover from GitHub
        github_features = [f for f in features if not f.repository_full_name.startswith("local/")]
        
        if not github_features:
            # Get GitHub client from session
            try:
                token = auth_service.get_session_token(x_session_id)
                session = storage.get_session(x_session_id)
                
                if token:
                    github_client = GitHubClient(token)
                    repos = await github_client.get_repositories(use_cache=True)
                    
                    # Discover features from each repo
                    for repo in repos:
                        discovered = await github_client.discover_features_from_specs(
                            repo_full_name=repo.full_name,
                            created_by_user_id=session.user.id if session else 0
                        )
                        
                        if discovered:
                            for feature in discovered:
                                storage.save_feature(feature)
                            logger.info(f"Discovered {len(discovered)} features from {repo.full_name}")
                    
                    # Reload features from storage after discovery
                    features = storage.list_features(repository_full_name=repository)
                    logger.info(f"GitHub feature discovery completed, total features: {len(features)}")
                    
            except Exception as discovery_error:
                logger.warning(f"GitHub feature discovery failed: {str(discovery_error)}")
        
        # Apply repository filter if provided
        if repository:
            features = [
                f for f in features
                if f.repository_full_name == repository
            ]
        
        # Apply status filter if provided
        if status_filter:
            features = [
                f for f in features
                if f.status.value == status_filter
            ]
        
        logger.info(f"Listed {len(features)} features (repo={repository}, status={status_filter})")
        
        return FeatureListResponse(
            features=features,
            repository=repository,
            total_count=len(features)
        )
        
    except Exception as e:
        logger.exception(f"Unexpected error listing all features: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list features: {str(e)}"
        )


# ========================================================================
# Diagnostic Endpoint (for debugging)
# ========================================================================

class StorageStatusResponse(BaseModel):
    """Response for storage status check."""
    total_features: int
    total_sessions: int
    features_by_repo: dict
    persistence_enabled: bool
    message: str


@router.get("/health/storage", response_model=StorageStatusResponse, status_code=status.HTTP_200_OK)
async def get_storage_status():
    """
    Get diagnostic information about backend storage.
    
    Returns:
        StorageStatusResponse with storage state information
    """
    try:
        all_features = storage.list_features()
        
        # Group features by repository
        features_by_repo = {}
        for feature in all_features:
            repo = feature.repository_full_name
            if repo not in features_by_repo:
                features_by_repo[repo] = []
            features_by_repo[repo].append({
                "feature_id": feature.feature_id,
                "branch_name": feature.branch_name,
                "title": feature.title,
                "status": feature.status
            })
        
        return StorageStatusResponse(
            total_features=len(all_features),
            total_sessions=len(storage._sessions),
            features_by_repo=features_by_repo,
            persistence_enabled=True,
            message=f"Backend is running. {len(all_features)} features in storage."
        )
        
    except Exception as e:
        logger.error(f"Error getting storage status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting storage status: {str(e)}"
        )


# ========================================================================
# Debug Endpoint: Check features without auth (for troubleshooting)
# ========================================================================

@router.get("/debug/features-no-auth", response_model=FeatureListResponse, status_code=status.HTTP_200_OK)
async def debug_list_features_no_auth(
    owner: str = Query(..., description="Repository owner"),
    repo: str = Query(..., description="Repository name")
):
    """
    DEBUG ENDPOINT: List features WITHOUT requiring authentication.
    
    This is only for troubleshooting and should be removed in production.
    
    Returns:
        FeatureListResponse with features
    """
    try:
        repo_full_name = f"{owner}/{repo}"
        
        # Get features directly from storage
        features = storage.list_features(repository_full_name=repo_full_name)
        logger.info(f"DEBUG (NO-AUTH): Found {len(features)} features for {repo_full_name}")
        
        return FeatureListResponse(
            features=features,
            repository=repo_full_name,
            total_count=len(features)
        )
        
    except Exception as e:
        logger.exception(f"Unexpected error in debug features endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list features: {str(e)}"
        )


