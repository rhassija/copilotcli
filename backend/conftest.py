"""
Pytest configuration and fixtures for backend tests.

Provides shared fixtures for:
- Test client
- Mock GitHub API
- Authentication tokens
- Database/storage setup
- WebSocket connections
"""

import asyncio
from typing import Generator, AsyncGenerator
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from src.main import app


# ============================================================================
# Pytest Configuration
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# FastAPI Test Client Fixtures
# ============================================================================

@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """
    Synchronous test client for FastAPI application.
    
    Usage:
        def test_health_check(client):
            response = client.get("/health")
            assert response.status_code == 200
    """
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Asynchronous test client for FastAPI application.
    
    Usage:
        @pytest.mark.asyncio
        async def test_auth_endpoint(async_client):
            response = await async_client.post("/api/v1/auth/verify", json={...})
            assert response.status_code == 200
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


# ============================================================================
# Authentication Fixtures
# ============================================================================

@pytest.fixture
def mock_github_token() -> str:
    """Mock GitHub personal access token for testing."""
    return "ghp_test_token_1234567890abcdefghijklmnopqrstuv"


@pytest.fixture
def mock_user_data() -> dict:
    """Mock GitHub user data returned from /user endpoint."""
    return {
        "login": "testuser",
        "id": 12345678,
        "avatar_url": "https://avatars.githubusercontent.com/u/12345678",
        "email": "testuser@example.com",
        "name": "Test User",
        "scopes": ["repo", "user", "workflow"]
    }


@pytest.fixture
def auth_headers(mock_github_token: str) -> dict:
    """
    Headers with authentication token for API requests.
    
    Usage:
        def test_protected_endpoint(client, auth_headers):
            response = client.get("/api/v1/repos", headers=auth_headers)
            assert response.status_code == 200
    """
    return {"Authorization": f"Bearer {mock_github_token}"}


# ============================================================================
# GitHub API Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_repository_data() -> dict:
    """Mock GitHub repository data."""
    return {
        "id": 123456789,
        "name": "test-repo",
        "full_name": "testuser/test-repo",
        "owner": {"login": "testuser", "id": 12345678},
        "private": False,
        "description": "Test repository for testing",
        "default_branch": "main",
        "html_url": "https://github.com/testuser/test-repo"
    }


@pytest.fixture
def mock_branch_data() -> dict:
    """Mock GitHub branch data."""
    return {
        "name": "feature/test-branch",
        "commit": {
            "sha": "abc123def456",
            "url": "https://api.github.com/repos/testuser/test-repo/commits/abc123"
        },
        "protected": False
    }


@pytest.fixture
def mock_file_content() -> dict:
    """Mock GitHub file content response."""
    return {
        "name": "spec.md",
        "path": "specs/001-test-feature/spec.md",
        "sha": "abc123def456",
        "content": "IyBGZWF0dXJlIFNwZWNpZmljYXRpb24KClRoaXMgaXMgYSB0ZXN0IHNwZWMu",  # base64 encoded
        "encoding": "base64"
    }


# ============================================================================
# Storage/Database Fixtures
# ============================================================================

@pytest.fixture
def clean_storage():
    """
    Clean in-memory storage before/after tests.
    
    Usage:
        def test_feature_creation(client, clean_storage):
            # Storage is clean at start and will be cleaned after
            response = client.post("/api/v1/features", json={...})
    """
    from src.services.storage import storage
    
    # Clear storage before test
    storage.clear()
    
    yield storage
    
    # Clear storage after test
    storage.clear()


# ============================================================================
# WebSocket Fixtures
# ============================================================================

@pytest.fixture
def mock_websocket_url() -> str:
    """WebSocket URL for testing."""
    return "ws://test/ws"


@pytest.fixture
def mock_operation_id() -> str:
    """Mock operation ID for tracking WebSocket messages."""
    return "op_test_12345"


# ============================================================================
# Copilot CLI Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_copilot_output() -> list[dict]:
    """
    Mock Copilot CLI output messages.
    
    Returns list of message dictionaries with:
    - type: "thinking" | "execution" | "error" | "complete"
    - content: Message text
    - timestamp: ISO format timestamp
    """
    return [
        {"type": "thinking", "content": "Analyzing requirements...", "timestamp": "2026-02-18T10:00:00Z"},
        {"type": "execution", "content": "Creating feature branch...", "timestamp": "2026-02-18T10:00:01Z"},
        {"type": "execution", "content": "Generating spec.md...", "timestamp": "2026-02-18T10:00:02Z"},
        {"type": "complete", "content": "Feature initialized successfully", "timestamp": "2026-02-18T10:00:03Z"}
    ]


# ============================================================================
# Test Data Factories (Optional - for more complex test data)
# ============================================================================

class TestDataFactory:
    """Factory for generating test data with variations."""
    
    @staticmethod
    def create_repository(name: str = "test-repo", owner: str = "testuser", **kwargs) -> dict:
        """Create a test repository object with customizable fields."""
        defaults = {
            "id": 123456789,
            "name": name,
            "full_name": f"{owner}/{name}",
            "owner": {"login": owner, "id": 12345678},
            "private": False,
            "default_branch": "main"
        }
        defaults.update(kwargs)
        return defaults
    
    @staticmethod
    def create_branch(name: str = "main", sha: str = "abc123", **kwargs) -> dict:
        """Create a test branch object."""
        defaults = {
            "name": name,
            "commit": {"sha": sha, "url": f"https://api.github.com/repos/test/test/commits/{sha}"},
            "protected": False
        }
        defaults.update(kwargs)
        return defaults


@pytest.fixture
def test_data_factory() -> TestDataFactory:
    """Provide test data factory for generating varied test data."""
    return TestDataFactory()


# ============================================================================
# Markers for Test Organization
# ============================================================================

# Usage in tests:
# @pytest.mark.unit - Unit tests (no external dependencies)
# @pytest.mark.integration - Integration tests (with mocked external services)
# @pytest.mark.contract - Contract tests (API endpoint validation)
# @pytest.mark.e2e - End-to-end tests (full workflow)
# @pytest.mark.slow - Tests that take >1 second
# @pytest.mark.asyncio - Async tests (requires pytest-asyncio)

pytest.register_assert_rewrite("tests")
