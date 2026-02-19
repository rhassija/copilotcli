"""
Authentication service for GitHub token validation and session management.

Provides:
- Token verification via GitHub API
- Session creation and persistence
- Token expiration detection
- Logout and session cleanup
"""

import logging
import secrets
import hashlib
from typing import Optional, Tuple
from datetime import datetime, timedelta

from cryptography.fernet import Fernet

from src.models.auth import User, Token, AuthSession, TokenScope, AuthRequest, AuthResponse
from src.services.github_client import GitHubClient, GitHubAuthenticationError, GitHubAPIError
from src.services.storage import storage

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Base exception for authentication errors."""
    pass


class InvalidTokenError(AuthenticationError):
    """Raised when token is invalid."""
    pass


class SessionExpiredError(AuthenticationError):
    """Raised when session has expired."""
    pass


class AuthService:
    """
    Service for authentication and session management.
    
    Handles:
    - GitHub PAT validation
    - Session creation with encrypted token storage
    - Session lifecycle management
    - Token expiration detection
    """
    
    # Session configuration
    SESSION_DURATION_HOURS = 24  # Default session duration
    TOKEN_VALIDATION_CACHE_SECONDS = 300  # Cache token validation for 5 minutes
    
    def __init__(self, encryption_key: Optional[bytes] = None):
        """
        Initialize auth service.
        
        Args:
            encryption_key: Fernet encryption key for token storage.
                          If None, generates a new key (for testing/development).
        """
        # In production, this should be loaded from environment variable
        if encryption_key is None:
            encryption_key = Fernet.generate_key()
            logger.warning("Using generated encryption key - tokens will not persist across restarts!")
        
        self._cipher = Fernet(encryption_key)
    
    def _encrypt_token(self, token: str) -> str:
        """Encrypt GitHub token for storage."""
        return self._cipher.encrypt(token.encode()).decode()
    
    def _decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt stored GitHub token."""
        return self._cipher.decrypt(encrypted_token.encode()).decode()
    
    def _generate_session_id(self) -> str:
        """Generate secure session ID."""
        return secrets.token_urlsafe(32)
    
    def _generate_token_id(self, token: str) -> str:
        """Generate deterministic token ID from token value."""
        return hashlib.sha256(token.encode()).hexdigest()[:16]
    
    def _get_token_prefix(self, token: str) -> str:
        """Get first 7 characters of token for identification."""
        return token[:7] if len(token) >= 7 else token
    
    # ========================================================================
    # Token Verification
    # ========================================================================
    
    async def verify_token(self, token: str, force_validation: bool = False) -> Tuple[bool, Optional[User]]:
        """
        Verify GitHub token and get user information.
        
        Args:
            token: GitHub personal access token
            force_validation: Skip cache and force GitHub API validation
        
        Returns:
            Tuple of (is_valid, user_data)
        
        Raises:
            InvalidTokenError: If token is invalid
            GitHubAPIError: If GitHub API call fails
        """
        # Check cache unless force validation
        if not force_validation:
            cache_key = f"token_validation:{self._get_token_prefix(token)}"
            cached = storage.cache_get(cache_key)
            if cached:
                logger.debug(f"Token validation cache hit")
                return cached
        
        try:
            # Use GitHub client to validate
            client = GitHubClient(token)
            is_valid, user = await client.validate_token()
            await client.close()
            
            # Cache validation result
            cache_key = f"token_validation:{self._get_token_prefix(token)}"
            storage.cache_set(cache_key, (is_valid, user), ttl_seconds=self.TOKEN_VALIDATION_CACHE_SECONDS)
            
            logger.info(f"Token validated successfully for user: {user.login}")
            return is_valid, user
        
        except GitHubAuthenticationError as e:
            logger.warning(f"Token validation failed: {e}")
            raise InvalidTokenError(str(e))
        
        except GitHubAPIError as e:
            logger.error(f"GitHub API error during token validation: {e}")
            raise
    
    # ========================================================================
    # Session Management
    # ========================================================================
    
    async def create_session(
        self,
        token: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuthSession:
        """
        Create authenticated session.
        
        Args:
            token: GitHub personal access token
            ip_address: Client IP address
            user_agent: Client user agent
        
        Returns:
            Created AuthSession
        
        Raises:
            InvalidTokenError: If token is invalid
        """
        # Validate token and get user
        is_valid, user = await self.verify_token(token)
        
        if not is_valid or not user:
            raise InvalidTokenError("Invalid GitHub token")
        
        # Get token scopes (basic check)
        client = GitHubClient(token)
        scopes = client.get_token_scopes()
        await client.close()
        
        # Create token model
        token_id = self._generate_token_id(token)
        token_model = Token(
            token_id=token_id,
            user_id=user.id,
            scopes=scopes,
            is_valid=True,
            last_validated_at=datetime.utcnow(),
            token_prefix=self._get_token_prefix(token),
            created_at=datetime.utcnow(),
            expires_at=None  # GitHub PATs don't have expiry by default
        )
        
        # Create session
        session_id = self._generate_session_id()
        encrypted_token = self._encrypt_token(token)
        expires_at = datetime.utcnow() + timedelta(hours=self.SESSION_DURATION_HOURS)
        
        session = AuthSession(
            session_id=session_id,
            user=user,
            token=token_model,
            encrypted_token=encrypted_token,
            created_at=datetime.utcnow(),
            last_accessed_at=datetime.utcnow(),
            expires_at=expires_at,
            is_active=True,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Store session
        storage.save_session(session)
        
        logger.info(f"Created session {session_id} for user {user.login}")
        return session
    
    def get_session(self, session_id: str) -> Optional[AuthSession]:
        """
        Get active session by ID.
        
        Args:
            session_id: Session ID
        
        Returns:
            AuthSession if valid and active, None otherwise
        """
        session = storage.get_session(session_id)
        
        if not session:
            logger.debug(f"Session not found: {session_id}")
            return None
        
        if session.is_expired:
            logger.info(f"Session expired: {session_id}")
            self.logout(session_id)
            return None
        
        if not session.is_active:
            logger.debug(f"Session inactive: {session_id}")
            return None
        
        # Refresh access time
        session.refresh_access()
        storage.save_session(session)
        
        return session
    
    def get_session_token(self, session_id: str) -> Optional[str]:
        """
        Get decrypted GitHub token for a session.
        
        Args:
            session_id: Session ID
        
        Returns:
            Decrypted GitHub token if session is valid, None otherwise
        """
        session = self.get_session(session_id)
        
        if not session:
            return None
        
        try:
            return self._decrypt_token(session.encrypted_token)
        except Exception as e:
            logger.error(f"Failed to decrypt token for session {session_id}: {e}")
            return None
    
    async def refresh_session(self, session_id: str) -> Optional[AuthSession]:
        """
        Refresh session by revalidating token.
        
        Args:
            session_id: Session ID
        
        Returns:
            Refreshed AuthSession if valid, None otherwise
        """
        session = storage.get_session(session_id)
        
        if not session:
            return None
        
        # Get token
        token = self._decrypt_token(session.encrypted_token)
        
        try:
            # Revalidate token
            is_valid, user = await self.verify_token(token, force_validation=True)
            
            if not is_valid:
                logger.warning(f"Token no longer valid for session {session_id}")
                self.logout(session_id)
                return None
            
            # Update session
            session.user = user
            session.token.is_valid = True
            session.token.last_validated_at = datetime.utcnow()
            session.refresh_access()
            
            storage.save_session(session)
            
            logger.info(f"Refreshed session {session_id}")
            return session
        
        except (InvalidTokenError, GitHubAPIError) as e:
            logger.error(f"Failed to refresh session {session_id}: {e}")
            self.logout(session_id)
            return None
    
    def logout(self, session_id: str) -> bool:
        """
        Logout and cleanup session.
        
        Args:
            session_id: Session ID to logout
        
        Returns:
            True if session was deleted, False if not found
        """
        session = storage.get_session(session_id)
        
        if session:
            # Mark as inactive before deletion
            session.invalidate()
            storage.save_session(session)
        
        # Delete session
        deleted = storage.delete_session(session_id)
        
        if deleted:
            logger.info(f"Logged out session {session_id}")
        
        return deleted
    
    def logout_user(self, user_id: int) -> int:
        """
        Logout all sessions for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            Number of sessions logged out
        """
        sessions = storage.get_user_sessions(user_id)
        count = 0
        
        for session in sessions:
            if self.logout(session.session_id):
                count += 1
        
        logger.info(f"Logged out {count} sessions for user {user_id}")
        return count
    
    # ========================================================================
    # Token Expiration Detection
    # ========================================================================
    
    async def detect_token_expiration(self, session_id: str) -> bool:
        """
        Detect if token has expired by attempting validation.
        
        This is called when API returns 401 error.
        
        Args:
            session_id: Session ID
        
        Returns:
            True if token expired, False if still valid
        """
        session = storage.get_session(session_id)
        
        if not session:
            return True
        
        # Get token
        token = self._decrypt_token(session.encrypted_token)
        
        try:
            # Force validation
            is_valid, _ = await self.verify_token(token, force_validation=True)
            
            if not is_valid:
                logger.warning(f"Token expired for session {session_id}")
                session.token.is_valid = False
                storage.save_session(session)
                return True
            
            return False
        
        except InvalidTokenError:
            logger.warning(f"Token expired/revoked for session {session_id}")
            session.token.is_valid = False
            storage.save_session(session)
            return True
        
        except GitHubAPIError as e:
            logger.error(f"Error detecting token expiration: {e}")
            # Assume expired on error
            return True
    
    # ========================================================================
    # Session Cleanup
    # ========================================================================
    
    def cleanup_expired_sessions(self) -> int:
        """
        Remove expired sessions from storage.
        
        Returns:
            Number of sessions cleaned up
        """
        count = storage.cleanup_expired_sessions()
        
        if count > 0:
            logger.info(f"Cleaned up {count} expired sessions")
        
        return count
    
    def get_active_sessions_count(self, user_id: Optional[int] = None) -> int:
        """
        Get count of active sessions.
        
        Args:
            user_id: Optional user ID to filter by
        
        Returns:
            Count of active sessions
        """
        if user_id:
            return len(storage.get_user_sessions(user_id))
        else:
            stats = storage.get_stats()
            return stats.get("sessions", 0)


# Global auth service instance
auth_service = AuthService()
