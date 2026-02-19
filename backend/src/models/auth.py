"""
Authentication models for user sessions and tokens.

Models:
- User: GitHub user information
- AuthSession: Active user sessions with token storage
- Token: GitHub personal access token metadata
"""

from datetime import datetime, timedelta
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class TokenScope(str, Enum):
    """GitHub token scopes."""
    REPO = "repo"
    USER = "user"
    WORKFLOW = "workflow"
    READ_ORG = "read:org"
    WRITE_ORG = "write:org"
    ADMIN_REPO_HOOK = "admin:repo_hook"


class User(BaseModel):
    """
    GitHub user model.
    
    Represents authenticated user information from GitHub API.
    """
    id: int = Field(..., description="GitHub user ID")
    login: str = Field(..., description="GitHub username")
    name: Optional[str] = Field(None, description="User's full name")
    email: Optional[str] = Field(None, description="User's email address")
    avatar_url: str = Field(..., description="URL to user's avatar image")
    html_url: str = Field(..., description="URL to user's GitHub profile")
    type: str = Field(default="User", description="Account type (User/Organization)")
    site_admin: bool = Field(default=False, description="Whether user is a GitHub site admin")
    
    # Additional metadata
    public_repos: Optional[int] = Field(None, description="Number of public repositories")
    followers: Optional[int] = Field(None, description="Number of followers")
    following: Optional[int] = Field(None, description="Number of following")
    created_at: Optional[datetime] = Field(None, description="Account creation timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 12345678,
                "login": "octocat",
                "name": "The Octocat",
                "email": "octocat@github.com",
                "avatar_url": "https://avatars.githubusercontent.com/u/12345678",
                "html_url": "https://github.com/octocat",
                "type": "User",
                "site_admin": False,
                "public_repos": 10,
                "followers": 100,
                "following": 50
            }
        }


class Token(BaseModel):
    """
    GitHub personal access token metadata.
    
    Stores token information without exposing the actual token value.
    The actual token is stored securely in AuthSession.
    """
    token_id: str = Field(..., description="Unique identifier for this token")
    user_id: int = Field(..., description="GitHub user ID this token belongs to")
    scopes: List[TokenScope] = Field(default_factory=list, description="Token permissions/scopes")
    
    # Token validation
    is_valid: bool = Field(default=True, description="Whether token is currently valid")
    last_validated_at: Optional[datetime] = Field(None, description="Last validation timestamp")
    
    # Token metadata (not sensitive)
    token_prefix: str = Field(..., description="First 7 chars of token (for identification)")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Token creation time")
    expires_at: Optional[datetime] = Field(None, description="Token expiration time (if set)")
    
    @field_validator('token_prefix')
    @classmethod
    def validate_token_prefix(cls, v: str) -> str:
        """Ensure token prefix is exactly 7 characters."""
        if len(v) != 7:
            raise ValueError("Token prefix must be exactly 7 characters")
        return v
    
    @property
    def is_expired(self) -> bool:
        """Check if token has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    class Config:
        json_schema_extra = {
            "example": {
                "token_id": "tok_abc123def456",
                "user_id": 12345678,
                "scopes": ["repo", "user", "workflow"],
                "is_valid": True,
                "last_validated_at": "2026-02-18T10:00:00Z",
                "token_prefix": "ghp_abc",
                "created_at": "2026-02-18T09:00:00Z",
                "expires_at": None
            }
        }


class AuthSession(BaseModel):
    """
    Active authentication session.
    
    Represents a user's active session with stored authentication token.
    Sessions are stored in-memory (Phase 1) or database (Phase 2+).
    """
    session_id: str = Field(..., description="Unique session identifier")
    user: User = Field(..., description="Authenticated user information")
    token: Token = Field(..., description="Token metadata")
    
    # Secure token storage (encrypted in production)
    encrypted_token: str = Field(..., description="Encrypted GitHub PAT")
    
    # Session metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Session creation time")
    last_accessed_at: datetime = Field(default_factory=datetime.utcnow, description="Last access time")
    expires_at: datetime = Field(..., description="Session expiration time")
    
    # Session state
    is_active: bool = Field(default=True, description="Whether session is active")
    ip_address: Optional[str] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="Client user agent")
    
    @property
    def is_expired(self) -> bool:
        """Check if session has expired."""
        return datetime.utcnow() > self.expires_at
    
    @property
    def time_until_expiry(self) -> timedelta:
        """Get time remaining until session expires."""
        return self.expires_at - datetime.utcnow()
    
    def refresh_access(self) -> None:
        """Update last accessed timestamp."""
        self.last_accessed_at = datetime.utcnow()
    
    def invalidate(self) -> None:
        """Invalidate this session."""
        self.is_active = False
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "sess_xyz789abc123",
                "user": {
                    "id": 12345678,
                    "login": "octocat",
                    "name": "The Octocat",
                    "email": "octocat@github.com",
                    "avatar_url": "https://avatars.githubusercontent.com/u/12345678",
                    "html_url": "https://github.com/octocat"
                },
                "token": {
                    "token_id": "tok_abc123def456",
                    "user_id": 12345678,
                    "scopes": ["repo", "user"],
                    "token_prefix": "ghp_abc"
                },
                "encrypted_token": "encrypted_value_here",
                "created_at": "2026-02-18T09:00:00Z",
                "last_accessed_at": "2026-02-18T10:00:00Z",
                "expires_at": "2026-02-19T09:00:00Z",
                "is_active": True
            }
        }


class AuthRequest(BaseModel):
    """Request model for authentication."""
    token: str = Field(..., description="GitHub personal access token", min_length=40)
    
    @field_validator('token')
    @classmethod
    def validate_token_format(cls, v: str) -> str:
        """Validate GitHub token format."""
        if not (v.startswith('ghp_') or v.startswith('github_pat_')):
            raise ValueError("Invalid GitHub token format. Must start with 'ghp_' or 'github_pat_'")
        return v


class AuthResponse(BaseModel):
    """Response model for successful authentication."""
    session_id: str = Field(..., description="Session identifier")
    user: User = Field(..., description="Authenticated user info")
    expires_at: datetime = Field(..., description="Session expiration time")
    message: str = Field(default="Authentication successful", description="Success message")


class LogoutRequest(BaseModel):
    """Request model for logout."""
    session_id: str = Field(..., description="Session to terminate")


class LogoutResponse(BaseModel):
    """Response model for logout."""
    success: bool = Field(..., description="Whether logout was successful")
    message: str = Field(default="Logged out successfully", description="Status message")
