"""
Centralized error handling for the application.

Provides:
- Standard error response formatting
- HTTP exception handlers
- WebSocket error handlers
- Error logging with context
"""

import logging
import traceback
from typing import Optional, Any, Dict
from datetime import datetime

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.services.github_client import GitHubAPIError, GitHubAuthenticationError, GitHubRateLimitError
from src.services.auth_service import AuthenticationError, InvalidTokenError, SessionExpiredError
from src.services.copilot_runner import SubprocessError, SubprocessTimeoutError, SubprocessExecutionError

logger = logging.getLogger(__name__)


class ErrorResponse:
    """
    Standard error response format.
    
    Ensures consistent error messages across all API endpoints.
    """
    
    @staticmethod
    def format(
        error_code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500
    ) -> Dict[str, Any]:
        """
        Format error response.
        
        Args:
            error_code: Machine-readable error code
            message: Human-readable error message
            details: Additional error details
            status_code: HTTP status code
        
        Returns:
            Formatted error response dict
        """
        response = {
            "error": {
                "code": error_code,
                "message": message,
                "timestamp": datetime.utcnow().isoformat(),
                "status": status_code
            }
        }
        
        if details:
            response["error"]["details"] = details
        
        return response


# ========================================================================
# Exception Handlers
# ========================================================================

async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Handle HTTP exceptions.
    
    Args:
        request: FastAPI request
        exc: HTTP exception
    
    Returns:
        JSON error response
    """
    logger.warning(
        f"HTTP {exc.status_code}: {exc.detail}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "status_code": exc.status_code
        }
    )
    
    error_response = ErrorResponse.format(
        error_code=f"HTTP_{exc.status_code}",
        message=exc.detail,
        status_code=exc.status_code
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle request validation errors.
    
    Args:
        request: FastAPI request
        exc: Validation error
    
    Returns:
        JSON error response with validation details
    """
    logger.warning(
        f"Validation error: {exc.errors()}",
        extra={
            "path": request.url.path,
            "method": request.method
        }
    )
    
    error_response = ErrorResponse.format(
        error_code="VALIDATION_ERROR",
        message="Request validation failed",
        details={"errors": exc.errors()},
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response
    )


async def authentication_exception_handler(request: Request, exc: AuthenticationError) -> JSONResponse:
    """
    Handle authentication errors.
    
    Args:
        request: FastAPI request
        exc: Authentication error
    
    Returns:
        JSON error response
    """
    logger.warning(
        f"Authentication error: {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method
        }
    )
    
    # Determine specific error code
    if isinstance(exc, InvalidTokenError):
        error_code = "INVALID_TOKEN"
        message = "GitHub token is invalid or revoked"
    elif isinstance(exc, SessionExpiredError):
        error_code = "SESSION_EXPIRED"
        message = "Session has expired"
    else:
        error_code = "AUTHENTICATION_FAILED"
        message = str(exc)
    
    error_response = ErrorResponse.format(
        error_code=error_code,
        message=message,
        status_code=status.HTTP_401_UNAUTHORIZED
    )
    
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=error_response
    )


async def github_api_exception_handler(request: Request, exc: GitHubAPIError) -> JSONResponse:
    """
    Handle GitHub API errors.
    
    Args:
        request: FastAPI request
        exc: GitHub API error
    
    Returns:
        JSON error response
    """
    logger.error(
        f"GitHub API error: {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method
        }
    )
    
    # Determine specific error code and status
    if isinstance(exc, GitHubAuthenticationError):
        error_code = "GITHUB_AUTH_ERROR"
        status_code = status.HTTP_401_UNAUTHORIZED
    elif isinstance(exc, GitHubRateLimitError):
        error_code = "GITHUB_RATE_LIMIT"
        status_code = status.HTTP_429_TOO_MANY_REQUESTS
    else:
        error_code = "GITHUB_API_ERROR"
        status_code = status.HTTP_502_BAD_GATEWAY
    
    error_response = ErrorResponse.format(
        error_code=error_code,
        message=str(exc),
        status_code=status_code
    )
    
    return JSONResponse(
        status_code=status_code,
        content=error_response
    )


async def subprocess_exception_handler(request: Request, exc: SubprocessError) -> JSONResponse:
    """
    Handle subprocess errors.
    
    Args:
        request: FastAPI request
        exc: Subprocess error
    
    Returns:
        JSON error response
    """
    logger.error(
        f"Subprocess error: {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method
        }
    )
    
    # Determine specific error code
    if isinstance(exc, SubprocessTimeoutError):
        error_code = "SUBPROCESS_TIMEOUT"
        message = "Operation timed out"
    elif isinstance(exc, SubprocessExecutionError):
        error_code = "SUBPROCESS_EXECUTION_ERROR"
        message = str(exc)
    else:
        error_code = "SUBPROCESS_ERROR"
        message = str(exc)
    
    error_response = ErrorResponse.format(
        error_code=error_code,
        message=message,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle unexpected errors.
    
    Args:
        request: FastAPI request
        exc: Exception
    
    Returns:
        JSON error response
    """
    # Log full traceback for debugging
    logger.error(
        f"Unexpected error: {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "traceback": traceback.format_exc()
        }
    )
    
    error_response = ErrorResponse.format(
        error_code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred",
        details={"error_type": type(exc).__name__} if logger.level <= logging.DEBUG else None,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response
    )


# ========================================================================
# Error Handler Registration
# ========================================================================

def register_exception_handlers(app):
    """
    Register all exception handlers with FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    # HTTP exceptions
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    
    # Validation errors
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    
    # Authentication errors
    app.add_exception_handler(AuthenticationError, authentication_exception_handler)
    app.add_exception_handler(InvalidTokenError, authentication_exception_handler)
    app.add_exception_handler(SessionExpiredError, authentication_exception_handler)
    
    # GitHub API errors
    app.add_exception_handler(GitHubAPIError, github_api_exception_handler)
    app.add_exception_handler(GitHubAuthenticationError, github_api_exception_handler)
    app.add_exception_handler(GitHubRateLimitError, github_api_exception_handler)
    
    # Subprocess errors
    app.add_exception_handler(SubprocessError, subprocess_exception_handler)
    app.add_exception_handler(SubprocessTimeoutError, subprocess_exception_handler)
    app.add_exception_handler(SubprocessExecutionError, subprocess_exception_handler)
    
    # Generic errors (catch-all)
    app.add_exception_handler(Exception, generic_exception_handler)
    
    logger.info("Exception handlers registered")


# ========================================================================
# Error Utilities
# ========================================================================

def create_error_response(
    error_code: str,
    message: str,
    status_code: int,
    details: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """
    Create error JSON response.
    
    Args:
        error_code: Error code
        message: Error message
        status_code: HTTP status code
        details: Additional details
    
    Returns:
        JSON response
    """
    error_response = ErrorResponse.format(
        error_code=error_code,
        message=message,
        details=details,
        status_code=status_code
    )
    
    return JSONResponse(
        status_code=status_code,
        content=error_response
    )


def log_error_with_context(
    error: Exception,
    context: Dict[str, Any],
    level: str = "error"
):
    """
    Log error with additional context.
    
    Args:
        error: Exception to log
        context: Additional context information
        level: Log level (error, warning, critical)
    """
    log_method = getattr(logger, level)
    
    log_method(
        f"{type(error).__name__}: {str(error)}",
        extra={
            **context,
            "error_type": type(error).__name__,
            "traceback": traceback.format_exc()
        }
    )
