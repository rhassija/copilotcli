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

from src.models.github import Repository, Branch, Feature, FeatureStatus
from src.models.auth import User
from src.services.github_client import GitHubClient, GitHubAPIError, GitHubAuthenticationError
from src.services.auth_service import auth_service
from src.services.storage import storage
from src.services.copilot_runner import CopilotRunner, SubprocessError
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
    session = auth_service.get_session(x_session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session"
        )
    
    token = auth_service.decrypt_token(session.encrypted_token)
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
    branch_name: str = Field(..., description="Name for the new branch", min_length=1, max_length=255)
    from_branch: str = Field(default="main", description="Base branch to create from")
    feature_title: str = Field(..., description="Feature title/description", min_length=1)
    initialize_documents: bool = Field(default=True, description="Initialize spec/plan/task documents via Copilot CLI")


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
    Create a new feature branch with optional document initialization.
    
    Implements T091-T092:
    - Creates branch via GitHub API
    - Optionally invokes Copilot CLI to initialize spec/plan/task documents
    - Uses copilot_runner service from Phase 2
    - Tracks feature in storage (T093)
    
    Args:
        owner: Repository owner
        repo: Repository name
        request: Branch creation request
        x_session_id: Session ID for user context
        github_client: Authenticated GitHub client
    
    Returns:
        CreateBranchResponse with branch and feature details
    """
    try:
        repo_full_name = f"{owner}/{repo}"
        feature_id = f"feat_{uuid.uuid4().hex[:16]}"
        
        # T091: Create branch via GitHub API
        logger.info(f"Creating branch '{request.branch_name}' in {repo_full_name} from '{request.from_branch}'")
        branch = await github_client.create_branch(
            repo_full_name=repo_full_name,
            branch_name=request.branch_name,
            from_branch=request.from_branch
        )
        
        # Get user from session
        session = auth_service.get_session(x_session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session"
            )
        
        # T093: Create Feature model
        feature = Feature(
            feature_id=feature_id,
            repository_full_name=repo_full_name,
            branch_name=request.branch_name,
            base_branch=request.from_branch,
            title=request.feature_title,
            status=FeatureStatus.INITIALIZING if request.initialize_documents else FeatureStatus.ACTIVE,
            created_by_user_id=session.user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        documents_initialized = False
        spec_path = None
        plan_path = None
        task_path = None
        
        # T092: Initialize documents via Copilot CLI (if requested)
        if request.initialize_documents:
            try:
                logger.info(f"Initializing documents for feature {feature_id} via Copilot CLI")
                
                # Get token for subprocess
                token = auth_service.decrypt_token(session.encrypted_token)
                
                # Create copilot runner
                runner = CopilotRunner(timeout_seconds=120)
                
                # Run Copilot CLI to initialize documents
                # Note: This is a placeholder - actual command depends on Copilot CLI implementation
                # Example: gh copilot init --repo owner/repo --branch branch_name --title "Feature Title"
                result = await runner.run_command(
                    args=[
                        "copilot", "init",
                        "--repo", repo_full_name,
                        "--branch", request.branch_name,
                        "--title", request.feature_title
                    ],
                    github_token=token,
                    working_dir=None
                )
                
                if result.return_code == 0:
                    documents_initialized = True
                    # Update feature with document paths (conventional paths)
                    spec_path = f"specs/{request.branch_name}/spec.md"
                    plan_path = f"specs/{request.branch_name}/plan.md"
                    task_path = f"specs/{request.branch_name}/tasks.md"
                    
                    feature.spec_path = spec_path
                    feature.plan_path = plan_path
                    feature.task_path = task_path
                    feature.status = FeatureStatus.ACTIVE
                    
                    logger.info(f"Documents initialized successfully for feature {feature_id}")
                else:
                    logger.warning(f"Copilot CLI returned non-zero: {result.return_code}")
                    logger.warning(f"Stderr: {result.stderr}")
                    feature.status = FeatureStatus.ACTIVE  # Continue anyway
                    
            except SubprocessError as e:
                logger.error(f"Copilot CLI subprocess error: {str(e)}")
                # Don't fail the entire request - branch was created
                feature.status = FeatureStatus.ACTIVE
            except Exception as e:
                logger.exception(f"Unexpected error during document initialization: {str(e)}")
                feature.status = FeatureStatus.ACTIVE
        
        # T093: Persist feature to storage
        storage.save_feature(feature)
        logger.info(f"Feature {feature_id} saved to storage")
        
        return CreateBranchResponse(
            branch=branch,
            feature_id=feature_id,
            message=f"Branch '{request.branch_name}' created successfully",
            documents_initialized=documents_initialized,
            spec_path=spec_path,
            plan_path=plan_path,
            task_path=task_path
        )
        
    except GitHubAPIError as e:
        logger.error(f"GitHub API error creating branch: {str(e)}")
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
    github_client: GitHubClient = Depends(get_github_client)
):
    """
    List features for a repository.
    
    Implements T094:
    - Returns features filtered by repository
    - Optionally filters by status
    - Returns feature metadata
    
    Args:
        owner: Repository owner
        repo: Repository name
        status_filter: Optional status filter (active, in_progress, etc.)
        github_client: Authenticated GitHub client (for auth validation)
    
    Returns:
        FeatureListResponse with features
    """
    try:
        repo_full_name = f"{owner}/{repo}"
        
        # Get features from storage (filtered by repository)
        features = storage.list_features(repository_full_name=repo_full_name)
        
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
    github_client: GitHubClient = Depends(get_github_client)
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
