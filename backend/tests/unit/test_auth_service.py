"""
Unit tests for authentication service.

Tests token validation, session management, and encryption.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from src.services.auth_service import AuthService
from src.models.auth import User, Token, AuthSession, TokenScope
from src.utils.error_handlers import InvalidTokenError


@pytest.fixture
def mock_storage():
    """Mock storage service."""
    mock = Mock()
    mock.create_session = AsyncMock()
    mock.get_session = Mock()
    mock.delete_session = Mock()
    mock.list_sessions = Mock()
    return mock


@pytest.fixture
def mock_github_client():
    """Mock GitHub client."""
    mock = Mock()
    mock.get_authenticated_user = AsyncMock()
    mock.verify_token = AsyncMock()
    return mock


@pytest.fixture
def auth_service(mock_storage, mock_github_client):
    """Create AuthService with mocked dependencies."""
    with patch('src.services.auth_service.storage', mock_storage), \
         patch('src.services.auth_service.GitHubClient') as mock_client_class:
        
        mock_client_class.return_value = mock_github_client
        service = AuthService()
        return service


class TestTokenVerification:
    """Tests for token verification."""

    @pytest.mark.asyncio
    async def test_verify_token_success(self, auth_service, mock_github_client):
        """Test successful token verification."""
        # Mock GitHub user response
        mock_user = User(
            id=12345,
            login="testuser",
            avatar_url="https://github.com/avatar",
            email="test@example.com"
        )
        mock_github_client.get_authenticated_user.return_value = mock_user
        mock_github_client.verify_token.return_value = {
            "scopes": ["repo", "user"],
            "valid": True
        }

        # Verify token
        token = "ghp_test1234567890"
        session = await auth_service.create_session(token)

        # Verify session created
        assert session is not None
        assert session.user.login == "testuser"
        assert session.user.id == 12345
        assert session.token.token_prefix == "ghp_test"
        assert TokenScope.REPO in session.token.scopes
        assert TokenScope.USER in session.token.scopes

    @pytest.mark.asyncio
    async def test_verify_token_invalid_format(self, auth_service):
        """Test token verification with invalid format."""
        with pytest.raises(InvalidTokenError, match="Invalid token format"):
            await auth_service.create_session("invalid_token")

    @pytest.mark.asyncio
    async def test_verify_token_github_error(self, auth_service, mock_github_client):
        """Test token verification when GitHub API fails."""
        from github import BadCredentialsException
        
        mock_github_client.get_authenticated_user.side_effect = BadCredentialsException(
            401, "Bad credentials"
        )

        with pytest.raises(InvalidTokenError, match="Invalid GitHub token"):
            await auth_service.create_session("ghp_valid1234567890")

    @pytest.mark.asyncio
    async def test_verify_token_network_error(self, auth_service, mock_github_client):
        """Test token verification with network error."""
        mock_github_client.get_authenticated_user.side_effect = Exception("Network error")

        with pytest.raises(Exception, match="Network error"):
            await auth_service.create_session("ghp_valid1234567890")


class TestSessionManagement:
    """Tests for session management."""

    @pytest.mark.asyncio
    async def test_create_session(self, auth_service, mock_storage, mock_github_client):
        """Test session creation."""
        mock_user = User(
            id=12345,
            login="testuser",
            avatar_url="https://github.com/avatar",
            email="test@example.com"
        )
        mock_github_client.get_authenticated_user.return_value = mock_user
        mock_github_client.verify_token.return_value = {
            "scopes": ["repo"],
            "valid": True
        }

        session = await auth_service.create_session("ghp_test1234567890")

        # Verify session properties
        assert session.session_id is not None
        assert len(session.session_id) > 20  # Should be UUID-like
        assert session.user.id == 12345
        assert session.created_at is not None
        assert session.expires_at > datetime.utcnow()

        # Verify storage was called
        mock_storage.create_session.assert_called_once()

    def test_get_session_valid(self, auth_service, mock_storage):
        """Test retrieving valid session."""
        mock_session = AuthSession(
            session_id="test_session_123",
            user=User(id=1, login="test", avatar_url="", email=""),
            token=Token(
                token_prefix="ghp",
                encrypted_token="encrypted",
                scopes=[TokenScope.REPO]
            ),
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        mock_storage.get_session.return_value = mock_session

        session = auth_service.get_session("test_session_123")

        assert session is not None
        assert session.session_id == "test_session_123"
        mock_storage.get_session.assert_called_once_with(
            "sessions", "test_session_123"
        )

    def test_get_session_expired(self, auth_service, mock_storage):
        """Test retrieving expired session."""
        mock_session = AuthSession(
            session_id="test_session_123",
            user=User(id=1, login="test", avatar_url="", email=""),
            token=Token(
                token_prefix="ghp",
                encrypted_token="encrypted",
                scopes=[TokenScope.REPO]
            ),
            created_at=datetime.utcnow() - timedelta(hours=2),
            expires_at=datetime.utcnow() - timedelta(hours=1)  # Expired
        )
        mock_storage.get_session.return_value = mock_session

        session = auth_service.get_session("test_session_123")

        # Should return None for expired session
        assert session is None
        
        # Should have cleaned up expired session
        mock_storage.delete_session.assert_called_once_with(
            "sessions", "test_session_123"
        )

    def test_get_session_not_found(self, auth_service, mock_storage):
        """Test retrieving non-existent session."""
        mock_storage.get_session.return_value = None

        session = auth_service.get_session("nonexistent_session")

        assert session is None

    def test_logout(self, auth_service, mock_storage):
        """Test session logout."""
        mock_storage.delete_session.return_value = True

        success = auth_service.logout("test_session_123")

        assert success is True
        mock_storage.delete_session.assert_called_once_with(
            "sessions", "test_session_123"
        )

    def test_logout_session_not_found(self, auth_service, mock_storage):
        """Test logout with non-existent session."""
        mock_storage.delete_session.return_value = False

        success = auth_service.logout("nonexistent_session")

        assert success is False


class TestSessionRefresh:
    """Tests for session refresh."""

    @pytest.mark.asyncio
    async def test_refresh_session_success(
        self, 
        auth_service, 
        mock_storage, 
        mock_github_client
    ):
        """Test successful session refresh."""
        # Mock existing session
        old_session = AuthSession(
            session_id="old_session_123",
            user=User(id=12345, login="testuser", avatar_url="", email="test@test.com"),
            token=Token(
                token_prefix="ghp",
                encrypted_token="encrypted_token",
                scopes=[TokenScope.REPO]
            ),
            created_at=datetime.utcnow() - timedelta(hours=1),
            expires_at=datetime.utcnow() + timedelta(hours=23)
        )
        mock_storage.get_session.return_value = old_session

        # Mock GitHub verification
        mock_user = User(
            id=12345,
            login="testuser",
            avatar_url="https://github.com/avatar",
            email="test@example.com"
        )
        mock_github_client.get_authenticated_user.return_value = mock_user
        mock_github_client.verify_token.return_value = {
            "scopes": ["repo"],
            "valid": True
        }

        # Refresh session
        new_session = await auth_service.refresh_session("old_session_123")

        # Verify new session created
        assert new_session is not None
        assert new_session.session_id != "old_session_123"
        assert new_session.user.id == 12345

        # Verify old session deleted
        mock_storage.delete_session.assert_called_once_with(
            "sessions", "old_session_123"
        )

    @pytest.mark.asyncio
    async def test_refresh_session_not_found(self, auth_service, mock_storage):
        """Test refresh with non-existent session."""
        mock_storage.get_session.return_value = None

        with pytest.raises(InvalidTokenError, match="Session not found"):
            await auth_service.refresh_session("nonexistent_session")

    @pytest.mark.asyncio
    async def test_refresh_session_token_revoked(
        self, 
        auth_service, 
        mock_storage, 
        mock_github_client
    ):
        """Test refresh when token has been revoked."""
        from github import BadCredentialsException
        
        # Mock existing session
        old_session = AuthSession(
            session_id="old_session_123",
            user=User(id=12345, login="testuser", avatar_url="", email=""),
            token=Token(
                token_prefix="ghp",
                encrypted_token="encrypted_token",
                scopes=[TokenScope.REPO]
            ),
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        mock_storage.get_session.return_value = old_session

        # Mock GitHub error (token revoked)
        mock_github_client.get_authenticated_user.side_effect = BadCredentialsException(
            401, "Bad credentials"
        )

        with pytest.raises(InvalidTokenError, match="Token has been revoked"):
            await auth_service.refresh_session("old_session_123")


class TestTokenEncryption:
    """Tests for token encryption/decryption."""

    def test_encrypt_token(self, auth_service):
        """Test token encryption."""
        token = "ghp_test1234567890"
        encrypted = auth_service._encrypt_token(token)

        # Verify encrypted
        assert encrypted != token
        assert len(encrypted) > len(token)

    def test_decrypt_token(self, auth_service):
        """Test token decryption."""
        token = "ghp_test1234567890"
        encrypted = auth_service._encrypt_token(token)
        decrypted = auth_service._decrypt_token(encrypted)

        # Verify decrypted matches original
        assert decrypted == token

    def test_encrypt_decrypt_roundtrip(self, auth_service):
        """Test encryption/decryption roundtrip."""
        original_tokens = [
            "ghp_test1234567890",
            "github_pat_11ABCDEFG",
            "gho_specialchars!@#$%",
        ]

        for token in original_tokens:
            encrypted = auth_service._encrypt_token(token)
            decrypted = auth_service._decrypt_token(encrypted)
            assert decrypted == token


class TestUtilityMethods:
    """Tests for utility methods."""

    def test_get_active_sessions(self, auth_service, mock_storage):
        """Test getting active session count."""
        mock_storage.list_sessions.return_value = [
            Mock(expires_at=datetime.utcnow() + timedelta(hours=1)),
            Mock(expires_at=datetime.utcnow() + timedelta(hours=2)),
            Mock(expires_at=datetime.utcnow() - timedelta(hours=1)),  # Expired
        ]

        count = auth_service.get_active_sessions()

        assert count == 2  # Only non-expired sessions

    def test_validate_token_format_valid(self, auth_service):
        """Test token format validation with valid tokens."""
        valid_tokens = [
            "ghp_test1234567890",
            "github_pat_11ABCDEFGHIJKLMNOPQRSTUVWXYZ",
            "gho_test1234567890",
        ]

        for token in valid_tokens:
            # Should not raise
            auth_service._validate_token_format(token)

    def test_validate_token_format_invalid(self, auth_service):
        """Test token format validation with invalid tokens."""
        invalid_tokens = [
            "invalid",
            "ghp_",
            "",
            "   ",
            "not_a_github_token",
        ]

        for token in invalid_tokens:
            with pytest.raises(InvalidTokenError):
                auth_service._validate_token_format(token)
