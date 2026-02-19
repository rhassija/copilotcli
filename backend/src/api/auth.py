"""
Authentication API endpoints.

Provides:
- Token verification
- Session management
- Logout functionality
"""

from fastapi import APIRouter, HTTPException, status, Depends, Header
from pydantic import BaseModel, Field
from typing import Optional

from src.models.auth import User, AuthRequest, AuthResponse, LogoutRequest, LogoutResponse
from src.services.auth_service import auth_service, InvalidTokenError, AuthenticationError
from src.utils.error_handlers import create_error_response

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


# ========================================================================
# Request/Response Models
# ========================================================================

class VerifyTokenRequest(BaseModel):
    """Request to verify GitHub token."""
    token: str = Field(..., description="GitHub personal access token", min_length=1)


class VerifyTokenResponse(BaseModel):
    """Response from token verification."""
    session_id: str
    user: User
    token_prefix: str
    message: str = "Authentication successful"


class LogoutRequestBody(BaseModel):
    """Request to logout."""
    session_id: str = Field(..., description="Session ID to logout")


class LogoutResponseBody(BaseModel):
    """Response from logout."""
    success: bool
    message: str


class SessionVerifyResponse(BaseModel):
    """Response from session verification."""
    user: User
    session_valid: bool
    message: str


# ========================================================================
# Authentication Endpoints
# ========================================================================

@router.post("/verify", response_model=VerifyTokenResponse, status_code=status.HTTP_200_OK)
async def verify_token(request: VerifyTokenRequest):
    """
    Verify GitHub personal access token and create session.
    
    This endpoint:
    1. Validates the token with GitHub API
    2. Fetches user information
    3. Creates an authenticated session
    4. Returns session ID and user details
    
    Args:
        request: Token verification request
    
    Returns:
        VerifyTokenResponse with session ID and user info
    
    Raises:
        401: Invalid or expired token
        502: GitHub API error
    """
    try:
        # Create session with token
        session = await auth_service.create_session(token=request.token)
        
        return VerifyTokenResponse(
            session_id=session.session_id,
            user=session.user,
            token_prefix=session.token.token_prefix,
            message="Authentication successful"
        )
    
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}"
        )


@router.post("/logout", response_model=LogoutResponseBody, status_code=status.HTTP_200_OK)
async def logout(request: LogoutRequestBody):
    """
    Logout and cleanup session.
    
    This endpoint:
    1. Invalidates the session
    2. Removes session from storage
    3. Clears any cached data
    
    Args:
        request: Logout request with session ID
    
    Returns:
        LogoutResponseBody with success status
    """
    try:
        # Logout session
        success = auth_service.logout(request.session_id)
        
        if success:
            return LogoutResponseBody(
                success=True,
                message="Logout successful"
            )
        else:
            return LogoutResponseBody(
                success=False,
                message="Session not found or already logged out"
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout failed: {str(e)}"
        )


@router.get("/verify", response_model=SessionVerifyResponse, status_code=status.HTTP_200_OK)
async def verify_session(x_session_id: Optional[str] = Header(None, alias="X-Session-ID")):
    """
    Verify existing session is still valid.
    
    Used by frontend to check if user is still authenticated.
    
    Args:
        x_session_id: Session ID from request header
    
    Returns:
        SessionVerifyResponse with user info and validity
    
    Raises:
        401: Session invalid or expired
    """
    if not x_session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No session ID provided"
        )
    
    try:
        # Get session
        session = auth_service.get_session(x_session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired or invalid"
            )
        
        return SessionVerifyResponse(
            user=session.user,
            session_valid=True,
            message="Session is valid"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/refresh", response_model=VerifyTokenResponse, status_code=status.HTTP_200_OK)
async def refresh_session(x_session_id: Optional[str] = Header(None, alias="X-Session-ID")):
    """
    Refresh session by revalidating token.
    
    Args:
        x_session_id: Session ID from request header
    
    Returns:
        VerifyTokenResponse with updated session info
    
    Raises:
        401: Session invalid or token expired
    """
    if not x_session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No session ID provided"
        )
    
    try:
        # Refresh session
        session = await auth_service.refresh_session(x_session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session could not be refreshed"
            )
        
        return VerifyTokenResponse(
            session_id=session.session_id,
            user=session.user,
            token_prefix=session.token.token_prefix,
            message="Session refreshed successfully"
        )
    
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Session refresh failed: {str(e)}"
        )


@router.get("/status")
async def get_auth_status():
    """
    Get authentication service status.
    
    Returns statistics about active sessions.
    """
    stats = {
        "active_sessions": auth_service.get_active_sessions_count(),
        "service_status": "healthy"
    }
    
    return stats
