"""
Integration tests for authentication flow.

Tests the complete authentication workflow including:
- Token verification
- Session creation
- Session persistence
- Token refresh
- Logout
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
from src.main import app
from src.models.auth import User
from datetime import datetime, timedelta


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_github():
    """Mock GitHub API responses."""
    with patch('src.services.github_client.PyGithub') as mock:
        # Mock user data
        mock_user = Mock()
        mock_user.id = 12345
        mock_user.login = "testuser"
        mock_user.avatar_url = "https://github.com/avatar.png"
        mock_user.email = "test@example.com"
        
        # Mock GitHub client
        mock_github_instance = Mock()
        mock_github_instance.get_user.return_value = mock_user
        mock.return_value = mock_github_instance
        
        yield mock


class TestAuthenticationFlow:
    """Tests for complete authentication workflow."""

    def test_full_login_flow(self, client, mock_github):
        """Test complete login flow: verify → session → redirect."""
        # Step 1: Verify token
        response = client.post(
            "/api/v1/auth/verify",
            json={"token": "ghp_valid_token_123"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "session_id" in data
        assert "user" in data
        assert "token_prefix" in data
        assert data["user"]["login"] == "testuser"
        assert data["user"]["id"] == 12345
        
        session_id = data["session_id"]
        
        # Step 2: Verify session is valid
        response = client.get(
            "/api/v1/auth/verify",
            headers={"X-Session-ID": session_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["session_valid"] is True
        assert data["user"]["login"] == "testuser"
        
        # Step 3: Check service status
        response = client.get("/api/v1/auth/status")
        assert response.status_code == 200
        data = response.json()
        assert data["active_sessions"] >= 1
        
        return session_id

    def test_full_logout_flow(self, client, mock_github):
        """Test complete logout flow: login → logout → verify invalidation."""
        # Step 1: Login
        response = client.post(
            "/api/v1/auth/verify",
            json={"token": "ghp_valid_token_123"}
        )
        session_id = response.json()["session_id"]
        
        # Step 2: Verify session is active
        response = client.get(
            "/api/v1/auth/verify",
            headers={"X-Session-ID": session_id}
        )
        assert response.status_code == 200
        
        # Step 3: Logout
        response = client.post(
            "/api/v1/auth/logout",
            json={"session_id": session_id}
        )
        assert response.status_code == 200
        assert response.json()["success"] is True
        
        # Step 4: Verify session is now invalid
        response = client.get(
            "/api/v1/auth/verify",
            headers={"X-Session-ID": session_id}
        )
        assert response.status_code == 401

    def test_session_refresh_flow(self, client, mock_github):
        """Test session refresh flow."""
        # Step 1: Login
        response = client.post(
            "/api/v1/auth/verify",
            json={"token": "ghp_valid_token_123"}
        )
        old_session_id = response.json()["session_id"]
        
        # Step 2: Refresh session
        response = client.post(
            "/api/v1/auth/refresh",
            headers={"X-Session-ID": old_session_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        
        new_session_id = data["session_id"]
        assert new_session_id != old_session_id
        
        # Step 3: Verify old session is invalid
        response = client.get(
            "/api/v1/auth/verify",
            headers={"X-Session-ID": old_session_id}
        )
        assert response.status_code == 401
        
        # Step 4: Verify new session is valid
        response = client.get(
            "/api/v1/auth/verify",
            headers={"X-Session-ID": new_session_id}
        )
        assert response.status_code == 200

    def test_multiple_sessions(self, client, mock_github):
        """Test handling multiple concurrent sessions."""
        sessions = []
        
        # Create multiple sessions
        for i in range(3):
            response = client.post(
                "/api/v1/auth/verify",
                json={"token": f"ghp_valid_token_{i}"}
            )
            assert response.status_code == 200
            sessions.append(response.json()["session_id"])
        
        # Verify all sessions are valid
        for session_id in sessions:
            response = client.get(
                "/api/v1/auth/verify",
                headers={"X-Session-ID": session_id}
            )
            assert response.status_code == 200
        
        # Check status shows correct count
        response = client.get("/api/v1/auth/status")
        data = response.json()
        assert data["active_sessions"] >= 3


class TestAuthenticationErrors:
    """Tests for authentication error scenarios."""

    def test_invalid_token_flow(self, client):
        """Test authentication with invalid token."""
        with patch('src.services.github_client.PyGithub') as mock_github:
            from github import BadCredentialsException
            mock_github.return_value.get_user.side_effect = BadCredentialsException(
                401, "Bad credentials"
            )
            
            response = client.post(
                "/api/v1/auth/verify",
                json={"token": "ghp_invalid_token"}
            )
            
            assert response.status_code == 401
            assert "detail" in response.json()

    def test_missing_session_header(self, client):
        """Test accessing protected endpoint without session."""
        response = client.get("/api/v1/auth/verify")
        assert response.status_code == 401

    def test_invalid_session_id(self, client):
        """Test accessing with invalid session ID."""
        response = client.get(
            "/api/v1/auth/verify",
            headers={"X-Session-ID": "invalid_session"}
        )
        assert response.status_code == 401

    def test_refresh_expired_session(self, client, mock_github):
        """Test refreshing an expired session."""
        # Create session
        response = client.post(
            "/api/v1/auth/verify",
            json={"token": "ghp_valid_token_123"}
        )
        session_id = response.json()["session_id"]
        
        # Logout (invalidate session)
        client.post(
            "/api/v1/auth/logout",
            json={"session_id": session_id}
        )
        
        # Try to refresh expired session
        response = client.post(
            "/api/v1/auth/refresh",
            headers={"X-Session-ID": session_id}
        )
        assert response.status_code == 401


class TestSessionPersistence:
    """Tests for session persistence across requests."""

    def test_session_persists_across_requests(self, client, mock_github):
        """Test that session persists across multiple requests."""
        # Login
        response = client.post(
            "/api/v1/auth/verify",
            json={"token": "ghp_valid_token_123"}
        )
        session_id = response.json()["session_id"]
        
        # Make multiple requests with same session
        for _ in range(5):
            response = client.get(
                "/api/v1/auth/verify",
                headers={"X-Session-ID": session_id}
            )
            assert response.status_code == 200
            assert response.json()["session_valid"] is True

    def test_session_data_consistency(self, client, mock_github):
        """Test that session data remains consistent."""
        # Login
        response = client.post(
            "/api/v1/auth/verify",
            json={"token": "ghp_valid_token_123"}
        )
        original_data = response.json()
        session_id = original_data["session_id"]
        
        # Verify session data multiple times
        for _ in range(3):
            response = client.get(
                "/api/v1/auth/verify",
                headers={"X-Session-ID": session_id}
            )
            data = response.json()
            
            assert data["user"]["login"] == original_data["user"]["login"]
            assert data["user"]["id"] == original_data["user"]["id"]


class TestTokenValidation:
    """Tests for token validation logic."""

    def test_token_format_validation(self, client):
        """Test validation of token format."""
        invalid_tokens = [
            "",
            "invalid",
            "ghp_",
            "not_a_token",
        ]
        
        for token in invalid_tokens:
            response = client.post(
                "/api/v1/auth/verify",
                json={"token": token}
            )
            # Should return 401 or 422 for invalid format
            assert response.status_code in [401, 422]

    def test_valid_token_formats(self, client, mock_github):
        """Test acceptance of valid token formats."""
        valid_prefixes = ["ghp_", "github_pat_", "gho_"]
        
        for prefix in valid_prefixes:
            token = f"{prefix}valid_token_123"
            response = client.post(
                "/api/v1/auth/verify",
                json={"token": token}
            )
            assert response.status_code == 200


class TestServiceStatus:
    """Tests for service status endpoint."""

    def test_status_reflects_active_sessions(self, client, mock_github):
        """Test that status endpoint reflects active session count."""
        # Get initial status
        response = client.get("/api/v1/auth/status")
        initial_count = response.json()["active_sessions"]
        
        # Create session
        client.post(
            "/api/v1/auth/verify",
            json={"token": "ghp_valid_token_123"}
        )
        
        # Verify count increased
        response = client.get("/api/v1/auth/status")
        new_count = response.json()["active_sessions"]
        assert new_count > initial_count

    def test_status_shows_healthy(self, client):
        """Test that status endpoint shows service is healthy."""
        response = client.get("/api/v1/auth/status")
        assert response.status_code == 200
        data = response.json()
        assert data["service_status"] == "healthy"
