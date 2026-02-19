"""
Structured logging configuration for the application.

Provides:
- JSON-formatted structured logging
- Token masking for security
- Request/response logging
- Performance timing
"""

import logging
import re
import json
import time
from typing import Any, Dict, Optional
from datetime import datetime


# Token patterns to mask in logs
TOKEN_PATTERNS = [
    r"ghp_[a-zA-Z0-9]{36}",  # GitHub Personal Access Token
    r"gho_[a-zA-Z0-9]{36}",  # GitHub OAuth Token
    r"ghu_[a-zA-Z0-9]{36}",  # GitHub User-to-Server Token
    r"ghs_[a-zA-Z0-9]{36}",  # GitHub Server-to-Server Token
    r"ghr_[a-zA-Z0-9]{36}",  # GitHub Refresh Token
    r"Bearer [a-zA-Z0-9\-._~+/]+=*",  # Bearer tokens
    r'"token"\s*:\s*"[^"]*"',  # Token in JSON
    r'"authorization"\s*:\s*"[^"]*"',  # Authorization header
]


class TokenMaskingFormatter(logging.Formatter):
    """
    Logging formatter that masks sensitive token data.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Compile regex patterns
        self.token_regex = re.compile("|".join(TOKEN_PATTERNS), re.IGNORECASE)
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record and mask tokens."""
        # Format the record
        formatted = super().format(record)
        
        # Mask tokens
        masked = self._mask_tokens(formatted)
        
        return masked
    
    def _mask_tokens(self, text: str) -> str:
        """Replace tokens with masked versions."""
        def mask_match(match):
            """Mask matched token, showing only prefix."""
            token = match.group(0)
            
            # For Bearer tokens, keep "Bearer" prefix
            if token.startswith("Bearer "):
                return f"Bearer ***MASKED***"
            
            # For GitHub tokens, keep first 7 characters
            if "_" in token and len(token) > 10:
                prefix = token[:7]
                return f"{prefix}***MASKED***"
            
            # For JSON tokens, keep structure
            if '"token"' in token or '"authorization"' in token:
                key = token.split(":")[0]
                return f'{key}: "***MASKED***"'
            
            return "***MASKED_TOKEN***"
        
        return self.token_regex.sub(mask_match, text)


class StructuredLogger:
    """
    Structured logging with JSON output and metadata.
    """
    
    def __init__(self, name: str):
        """
        Initialize structured logger.
        
        Args:
            name: Logger name (typically __name__)
        """
        self.logger = logging.getLogger(name)
        self._setup_logger()
    
    def _setup_logger(self):
        """Configure logger with structured formatting."""
        # Skip if already configured
        if self.logger.handlers:
            return
        
        # Set level from environment or default to INFO
        import os
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        self.logger.setLevel(getattr(logging, log_level, logging.INFO))
        
        # Create console handler
        handler = logging.StreamHandler()
        
        # Use token-masking formatter
        formatter = TokenMaskingFormatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        self.logger.addHandler(handler)
    
    def log_structured(
        self,
        level: str,
        message: str,
        **kwargs: Any
    ):
        """
        Log structured message with metadata.
        
        Args:
            level: Log level (debug, info, warning, error, critical)
            message: Log message
            **kwargs: Additional structured data
        """
        # Build log entry
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level.upper(),
            "message": message,
            **kwargs
        }
        
        # Log as JSON
        log_method = getattr(self.logger, level.lower())
        log_method(json.dumps(log_data))
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self.log_structured("debug", message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self.log_structured("info", message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self.log_structured("warning", message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message."""
        self.log_structured("error", message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self.log_structured("critical", message, **kwargs)


class RequestLogger:
    """
    Logger for HTTP requests with timing and metadata.
    """
    
    def __init__(self, logger: StructuredLogger):
        """
        Initialize request logger.
        
        Args:
            logger: Structured logger instance
        """
        self.logger = logger
        self._request_start_times: Dict[str, float] = {}
    
    def log_request_start(
        self,
        request_id: str,
        method: str,
        path: str,
        client_ip: Optional[str] = None,
        user_id: Optional[int] = None
    ):
        """
        Log start of HTTP request.
        
        Args:
            request_id: Unique request ID
            method: HTTP method
            path: Request path
            client_ip: Client IP address
            user_id: Authenticated user ID
        """
        self._request_start_times[request_id] = time.time()
        
        self.logger.info(
            f"Request started: {method} {path}",
            request_id=request_id,
            method=method,
            path=path,
            client_ip=client_ip,
            user_id=user_id
        )
    
    def log_request_end(
        self,
        request_id: str,
        status_code: int,
        error: Optional[str] = None
    ):
        """
        Log end of HTTP request.
        
        Args:
            request_id: Unique request ID
            status_code: HTTP status code
            error: Error message if request failed
        """
        # Calculate duration
        start_time = self._request_start_times.pop(request_id, None)
        duration_ms = None
        if start_time:
            duration_ms = (time.time() - start_time) * 1000
        
        log_level = "info" if status_code < 400 else "error"
        
        self.logger.log_structured(
            log_level,
            f"Request completed: {status_code}",
            request_id=request_id,
            status_code=status_code,
            duration_ms=duration_ms,
            error=error
        )
    
    def log_slow_request(
        self,
        request_id: str,
        method: str,
        path: str,
        duration_ms: float,
        threshold_ms: float = 1000.0
    ):
        """
        Log slow request warning.
        
        Args:
            request_id: Request ID
            method: HTTP method
            path: Request path
            duration_ms: Request duration in milliseconds
            threshold_ms: Threshold for slow request warning
        """
        if duration_ms > threshold_ms:
            self.logger.warning(
                f"Slow request detected: {method} {path}",
                request_id=request_id,
                method=method,
                path=path,
                duration_ms=duration_ms,
                threshold_ms=threshold_ms
            )


def mask_sensitive_data(data: Any) -> Any:
    """
    Recursively mask sensitive data in dictionaries and strings.
    
    Args:
        data: Data to mask (dict, list, str, or other)
    
    Returns:
        Masked data with same structure
    """
    if isinstance(data, dict):
        return {
            key: mask_sensitive_data(value)
            for key, value in data.items()
        }
    
    elif isinstance(data, list):
        return [mask_sensitive_data(item) for item in data]
    
    elif isinstance(data, str):
        # Mask tokens in strings
        formatter = TokenMaskingFormatter()
        return formatter._mask_tokens(data)
    
    else:
        return data


def setup_logging(log_level: str = "INFO"):
    """
    Setup application-wide logging configuration.
    
    Args:
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Set root logger level
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Apply token masking formatter to all handlers
    root_logger = logging.getLogger()
    formatter = TokenMaskingFormatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    for handler in root_logger.handlers:
        handler.setFormatter(formatter)
    
    # Reduce noise from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("github").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    
    logging.info(f"Logging configured with level: {log_level}")


# Create default structured logger
default_logger = StructuredLogger(__name__)
