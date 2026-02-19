"""
Contract tests for authentication API endpoints.

Tests request/response schemas and API behavior for auth routes.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
from src.main import app
from src.models.auth import User, Token


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_auth_service():
    """Mock authentication service."""
    with patch('src.api.auth.auth_service') as mock:
        yield mock


class TestVerifyTokenEndpoint:
    """Tests for POST /api/v1/auth/verify."""

    def test_verify_token_success(self, client, mock_auth_service):
        """Test successful token verification."""
        # Mock session creation
        mock_session = Mock()
        mock_session.session_id = "test_session_123"
        mock_session.user = User(
            id=12345,
            login="testuser",
            avatar_url="https://github.com/avatar",
            email="test@example.com"
        )
        mock_session.token = Mock()
        mock_session.token.token_prefix = "ghp_test"
        
        mock_auth_service.create_session = AsyncMock(return_value=mock_session)

        # Make request
        response = client.post(
            "/api/v1/auth/verify",
            json={"token": "ghp_test1234567890"}
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "test_session_123"
        assert data["user"]["login"] == "testuser"
        assert data["user"]["id"] == 12345
        assert data["token_prefix"] == "ghp_test"
        assert data["message"] == "Authentication successful"

    def test_verify_token_invalid(self, client, mock_auth_service):
        """Test token verification with invalid token."""
        from src.utils.error_handlers import InvalidTokenError
        
        mock_auth_service.create_session = AsyncMock(
            side_effect=InvalidTokenError("Invalid token")
        )

        response = client.post(
            "/api/v1/auth/verify",
            json={"token": "invalid_token"}
        )

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid token" in data["detail"]

    def test_verify_token_missing_token(self, client):
        """Test token verification without token in body."""
        response = client.post(
            "/api/v1/auth/verify",
            json={}
        )

        assert response.status_code == 422  # Validation error

    def test_verify_token_request_schema(self, client, mock_auth_service):
        """Test request schema validation."""
        # Valid schema
        mock_auth_service.create_session = AsyncMock(
            return_value=Mock(
                session_id="test",
                user=User(id=1, login="test", avatar_url="", email=""),
                token=Mock(token_prefix="ghp")
            )
        )
        
        response = client.post(
            "/api/v1/auth/verify",
            json={"token": "ghp_valid"}
        )
        assert response.status_code == 200

        # Invalid schema - wrong type
        response = client.post(
            "/api/v1/auth/verify",
            json={"token": 12345}  # Should be string
        )
        assert response.status_code == 422


class TestLogoutEndpoint:
    """Tests for POST /api/v1/auth/logout."""

    def test_logout_success(self, client, mock_auth_service):
        """Test successful logout."""
        mock_auth_service.logout.return_value = True

        response = client.post(
            "/api/v1/auth/logout",
            json={"session_id": "test_session_123"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Logout successful"

    def test_logout_session_not_found(self, client, mock_auth_service):
        """Test logout with non-existent session."""
        mock_auth_service.logout.return_value = False

        response = client.post(
            "/api/v1/auth/logout",
            json={"session_id": "nonexistent_session"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["message"] == "Session not found"

    def test_logout_missing_session_id(self, client):
        """Test logout without session_id in body."""
        response = client.post(
            "/api/v1/auth/logout",
            json={}
        )

        assert response.status_code == 422  # Validation error


class TestVerifySessionEndpoint:
    """Tests for GET /api/v1/auth/verify."""

    def test_verify_session_valid(self, client, mock_auth_service):
        """Test session verification with valid session."""
        mock_user = User(
            id=12345,
            login="testuser",
            avatar_url="https://github.com/avatar",
            email="test@example.com"
        )
        mock_auth_service.get_session.return_value = Mock(user=mock_user)

        response = client.get(
            "/api/v1/auth/verify",
            headers={"X-Session-ID": "test_session_123"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["session_valid"] is True
        assert data["user"]["login"] == "testuser"
        assert data["message"] == "Session valid"

    def test_verify_session_invalid(self, client, mock_auth_service):
        """Test session verification with invalid session."""
        mock_auth_service.get_session.return_value = None

        response = client.get(
            "/api/v1/auth/verify",
            headers={"X-Session-ID": "invalid_session"}
        )

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid or expired session" in data["detail"]

    def test_verify_session_missing_header(self, client):
        """Test session verification without X-Session-ID header."""
        response = client.get("/api/v1/auth/verify")

        assert response.status_code == 401


class TestRefreshSessionEndpoint:
    """Tests for POST /api/v1/auth/refresh."""

    def test_refresh_session_success(self, client, mock_auth_service):
        """Test successful session refresh."""
        mock_session = Mock()
        mock_session.session_id = "new_session_456"
        mock_session.user = User(
            id=12345,
            login="testuser",
            avatar_url="https://github.com/avatar",
            email="test@example.com"
        )
        mock_session.token = Mock(token_prefix="ghp_test")

        mock_auth_service.refresh_session = AsyncMock(return_value=mock_session)

        response = client.post(
            "/api/v1/auth/refresh",
            headers={"X-Session-ID": "old_session_123"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "new_session_456"
        assert data["user"]["login"] == "testuser"
        assert data["message"] == "Session refreshed"

    def test_refresh_session_invalid(self, client, mock_auth_service):
        """Test session refresh with invalid session."""
        from src.utils.error_handlers import InvalidTokenError
        
        mock_auth_service.refresh_session = AsyncMock(
            side_effect=InvalidTokenError("Session expired")
        )

        response = client.post(
            "/api/v1/auth/refresh",
            headers={"X-Session-ID": "expired_session"}
        )

        assert response.status_code == 401

    def test_refresh_session_missing_header(self, client):
        """Test session refresh without X-Session-ID header."""
        response = client.post("/api/v1/auth/refresh")

        assert response.status_code == 401


class TestStatusEndpoint:
    """Tests for GET /api/v1/auth/status."""

    def test_status_success(self, client, mock_auth_service):
        """Test service status endpoint."""
        mock_auth_service.get_active_sessions.return_value = 5

        response = client.get("/api/v1/auth/status")

        assert response.status_code == 200
        data = response.json()
        assert data["active_sessions"] == 5
        assert data["service_status"] == "healthy"


class TestResponseSchemas:
    """Tests for response schema validation."""

    def test_verify_response_schema(self, client, mock_auth_service):
        """Test verify endpoint response schema."""
        mock_session = Mock()
        mock_session.session_id = "test_session"
        mock_session.user = User(
            id=1,
            login="test",
            avatar_url="https://test.com",
            email="test@test.com"
        )
        mock_session.token = Mock(token_prefix="ghp")

        mock_auth_service.create_session = AsyncMock(return_value=mock_session)

        response = client.post(
            "/api/v1/auth/verify",
            json={"token": "ghp_test"}
        )

        data = response.json()
        # Check all required fields exist
        assert "session_id" in data
        assert "user" in data
        assert "token_prefix" in data
        assert "message" in data
        
        # Check user schema
        user = data["user"]
        assert "id" in user
        assert "login" in user
        assert "avatar_url" in user
        assert "email" in user
