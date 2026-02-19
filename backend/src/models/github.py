"""
GitHub repository models.

Models:
- Repository: GitHub repository information
- Branch: Repository branch information
- Feature: Feature branch with associated documents
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, HttpUrl
from enum import Enum


class RepositoryVisibility(str, Enum):
    """Repository visibility levels."""
    PUBLIC = "public"
    PRIVATE = "private"
    INTERNAL = "internal"


class Repository(BaseModel):
    """
    GitHub repository model.
    
    Represents a GitHub repository with metadata.
    """
    id: int = Field(..., description="GitHub repository ID")
    node_id: str = Field(..., description="GitHub GraphQL node ID")
    name: str = Field(..., description="Repository name")
    full_name: str = Field(..., description="Full repository name (owner/repo)")
    
    # Owner information
    owner: dict = Field(..., description="Repository owner (user or organization)")
    
    # Repository properties
    private: bool = Field(..., description="Whether repository is private")
    description: Optional[str] = Field(None, description="Repository description")
    fork: bool = Field(default=False, description="Whether repository is a fork")
    
    # URLs
    html_url: str = Field(..., description="Repository web URL")
    url: str = Field(..., description="Repository API URL")
    git_url: str = Field(..., description="Git clone URL")
    ssh_url: str = Field(..., description="SSH clone URL")
    clone_url: str = Field(..., description="HTTPS clone URL")
    
    # Default branch
    default_branch: str = Field(default="main", description="Default branch name")
    
    # Repository statistics
    size: Optional[int] = Field(None, description="Repository size in KB")
    stargazers_count: Optional[int] = Field(None, description="Number of stars")
    watchers_count: Optional[int] = Field(None, description="Number of watchers")
    forks_count: Optional[int] = Field(None, description="Number of forks")
    open_issues_count: Optional[int] = Field(None, description="Number of open issues")
    
    # Timestamps
    created_at: datetime = Field(..., description="Repository creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    pushed_at: Optional[datetime] = Field(None, description="Last push timestamp")
    
    # Permissions (if available)
    permissions: Optional[dict] = Field(None, description="User permissions on repository")
    
    # Repository features
    has_issues: bool = Field(default=True, description="Issues enabled")
    has_projects: bool = Field(default=True, description="Projects enabled")
    has_wiki: bool = Field(default=True, description="Wiki enabled")
    has_downloads: bool = Field(default=True, description="Downloads enabled")
    
    # Programming language
    language: Optional[str] = Field(None, description="Primary programming language")
    
    # Topics/tags
    topics: List[str] = Field(default_factory=list, description="Repository topics")
    
    # Archival status
    archived: bool = Field(default=False, description="Whether repository is archived")
    disabled: bool = Field(default=False, description="Whether repository is disabled")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 123456789,
                "node_id": "MDEwOlJlcG9zaXRvcnkxMjM0NTY3ODk=",
                "name": "copilotcli",
                "full_name": "octocat/copilotcli",
                "owner": {
                    "login": "octocat",
                    "id": 12345678,
                    "avatar_url": "https://avatars.githubusercontent.com/u/12345678"
                },
                "private": False,
                "description": "Copilot CLI with Modern Web UI",
                "html_url": "https://github.com/octocat/copilotcli",
                "default_branch": "main",
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-02-18T00:00:00Z"
            }
        }


class Commit(BaseModel):
    """Git commit reference."""
    sha: str = Field(..., description="Commit SHA hash", min_length=40, max_length=40)
    url: str = Field(..., description="Commit API URL")
    
    class Config:
        json_schema_extra = {
            "example": {
                "sha": "abc123def456789012345678901234567890abcd",
                "url": "https://api.github.com/repos/octocat/copilotcli/commits/abc123"
            }
        }


class Branch(BaseModel):
    """
    Git branch model.
    
    Represents a branch in a GitHub repository.
    """
    name: str = Field(..., description="Branch name")
    commit: Commit = Field(..., description="Latest commit on this branch")
    protected: bool = Field(default=False, description="Whether branch is protected")
    
    # Branch protection details (if available)
    protection_url: Optional[str] = Field(None, description="Branch protection API URL")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "feature/009-redesigned-workflow-ux",
                "commit": {
                    "sha": "abc123def456789012345678901234567890abcd",
                    "url": "https://api.github.com/repos/octocat/copilotcli/commits/abc123"
                },
                "protected": False
            }
        }


class FeatureStatus(str, Enum):
    """Feature development status."""
    INITIALIZING = "initializing"  # Feature being created
    ACTIVE = "active"  # Feature branch exists, documents ready
    IN_PROGRESS = "in_progress"  # Work in progress
    READY_FOR_REVIEW = "ready_for_review"  # Ready for PR
    COMPLETED = "completed"  # Merged to main
    ABANDONED = "abandoned"  # Feature abandoned


class Feature(BaseModel):
    """
    Feature branch with associated Copilot CLI documents.
    
    Represents a feature under development with spec/plan/task documents.
    """
    feature_id: str = Field(..., description="Unique feature identifier")
    
    # Repository and branch information
    repository_full_name: str = Field(..., description="Repository full name (owner/repo)")
    branch_name: str = Field(..., description="Feature branch name")
    base_branch: str = Field(default="main", description="Base branch (usually main)")
    
    # Feature metadata
    title: str = Field(..., description="Feature title/description")
    status: FeatureStatus = Field(default=FeatureStatus.ACTIVE, description="Feature status")
    
    # Document paths (relative to repository root)
    spec_path: Optional[str] = Field(None, description="Path to spec.md")
    plan_path: Optional[str] = Field(None, description="Path to plan.md")
    task_path: Optional[str] = Field(None, description="Path to tasks.md")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Feature creation time")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update time")
    
    # User information
    created_by_user_id: int = Field(..., description="GitHub user ID who created feature")
    
    # Feature progress
    completion_percentage: Optional[int] = Field(None, ge=0, le=100, description="Completion %")
    
    # Associated PR (if created)
    pull_request_number: Optional[int] = Field(None, description="PR number if created")
    pull_request_url: Optional[str] = Field(None, description="PR URL")
    
    class Config:
        json_schema_extra = {
            "example": {
                "feature_id": "feat_abc123xyz789",
                "repository_full_name": "octocat/copilotcli",
                "branch_name": "feature/009-redesigned-workflow-ux",
                "base_branch": "main",
                "title": "Redesigned Copilot CLI with Modern Web UI",
                "status": "active",
                "spec_path": "specs/009-redesigned-workflow-ux/spec.md",
                "plan_path": "specs/009-redesigned-workflow-ux/plan.md",
                "task_path": "specs/009-redesigned-workflow-ux/tasks.md",
                "created_at": "2026-02-18T09:00:00Z",
                "updated_at": "2026-02-18T10:00:00Z",
                "created_by_user_id": 12345678,
                "completion_percentage": 25
            }
        }


class CreateFeatureRequest(BaseModel):
    """Request model for creating a new feature."""
    repository_full_name: str = Field(..., description="Repository (owner/repo)")
    feature_title: str = Field(..., description="Feature title/description", min_length=5)
    base_branch: str = Field(default="main", description="Base branch to branch from")
    
    class Config:
        json_schema_extra = {
            "example": {
                "repository_full_name": "octocat/copilotcli",
                "feature_title": "Add user authentication",
                "base_branch": "main"
            }
        }


class CreateFeatureResponse(BaseModel):
    """Response model for feature creation."""
    feature: Feature = Field(..., description="Created feature information")
    branch_url: str = Field(..., description="GitHub branch URL")
    message: str = Field(default="Feature created successfully", description="Success message")


class ListRepositoriesRequest(BaseModel):
    """Request model for listing repositories."""
    page: int = Field(default=1, ge=1, description="Page number")
    per_page: int = Field(default=30, ge=1, le=100, description="Items per page")
    sort: str = Field(default="updated", description="Sort field (updated, created, pushed, full_name)")
    direction: str = Field(default="desc", description="Sort direction (asc, desc)")
    visibility: Optional[RepositoryVisibility] = Field(None, description="Filter by visibility")
    
    class Config:
        json_schema_extra = {
            "example": {
                "page": 1,
                "per_page": 30,
                "sort": "updated",
                "direction": "desc",
                "visibility": "private"
            }
        }


class ListRepositoriesResponse(BaseModel):
    """Response model for listing repositories."""
    repositories: List[Repository] = Field(..., description="List of repositories")
    total_count: int = Field(..., description="Total repository count")
    page: int = Field(..., description="Current page")
    per_page: int = Field(..., description="Items per page")
    has_next_page: bool = Field(..., description="Whether more pages exist")


class ListBranchesResponse(BaseModel):
    """Response model for listing branches."""
    branches: List[Branch] = Field(..., description="List of branches")
    default_branch: str = Field(..., description="Repository default branch")
    total_count: int = Field(..., description="Total branch count")
