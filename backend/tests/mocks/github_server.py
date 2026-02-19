"""
Mock GitHub API server for testing.

Simulates GitHub API endpoints without hitting the real API:
- /user - User information
- /user/repos - Repository listing
- /repos/{owner}/{repo}/branches - Branch listing
- /repos/{owner}/{repo}/git/refs - Branch references
- /repos/{owner}/{repo}/contents/{path} - File contents

Usage in tests:
    @pytest.fixture
    def mock_github_server():
        server = MockGitHubServer()
        server.start()
        yield server
        server.stop()
"""

import json
import base64
from typing import Dict, List, Optional, Any
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from urllib.parse import urlparse, parse_qs


class MockGitHubAPIHandler(BaseHTTPRequestHandler):
    """HTTP request handler for mock GitHub API."""
    
    # Class-level storage for test data
    repositories: List[Dict[str, Any]] = []
    branches: Dict[str, List[Dict[str, Any]]] = {}
    files: Dict[str, Dict[str, Any]] = {}
    users: Dict[str, Dict[str, Any]] = {}
    tokens: Dict[str, str] = {}  # token -> username mapping
    
    def do_GET(self):
        """Handle GET requests."""
        # Parse authorization header
        auth_header = self.headers.get('Authorization', '')
        token = self._extract_token(auth_header)
        
        if not self._validate_token(token):
            self._send_error(401, "Bad credentials")
            return
        
        path = self.path
        parsed = urlparse(path)
        path_parts = parsed.path.split('/')
        
        # Route to appropriate handler
        if path == "/user":
            self._handle_get_user(token)
        elif path == "/user/repos":
            self._handle_get_repos(token, parse_qs(parsed.query))
        elif len(path_parts) >= 5 and path_parts[3] == "branches":
            owner, repo = path_parts[2].split('/')
            self._handle_get_branches(owner, repo)
        elif len(path_parts) >= 5 and path_parts[4] == "contents":
            owner, repo = path_parts[2].split('/')
            file_path = '/'.join(path_parts[5:])
            self._handle_get_file(owner, repo, file_path)
        else:
            self._send_error(404, "Not Found")
    
    def do_POST(self):
        """Handle POST requests."""
        auth_header = self.headers.get('Authorization', '')
        token = self._extract_token(auth_header)
        
        if not self._validate_token(token):
            self._send_error(401, "Bad credentials")
            return
        
        path = self.path
        path_parts = path.split('/')
        
        # Parse request body
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')
        data = json.loads(body) if body else {}
        
        # Route to appropriate handler
        if len(path_parts) >= 5 and path_parts[4] == "refs":
            owner, repo = path_parts[2].split('/')
            self._handle_create_branch(owner, repo, data)
        else:
            self._send_error(404, "Not Found")
    
    def do_PUT(self):
        """Handle PUT requests (file updates)."""
        auth_header = self.headers.get('Authorization', '')
        token = self._extract_token(auth_header)
        
        if not self._validate_token(token):
            self._send_error(401, "Bad credentials")
            return
        
        path = self.path
        path_parts = path.split('/')
        
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')
        data = json.loads(body) if body else {}
        
        # Handle file updates
        if len(path_parts) >= 5 and path_parts[4] == "contents":
            owner, repo = path_parts[2].split('/')
            file_path = '/'.join(path_parts[5:])
            self._handle_update_file(owner, repo, file_path, data)
        else:
            self._send_error(404, "Not Found")
    
    # ========================================================================
    # Handler Methods
    # ========================================================================
    
    def _handle_get_user(self, token: str):
        """Handle GET /user endpoint."""
        username = self.tokens.get(token, "testuser")
        user = self.users.get(username, self._default_user(username))
        self._send_json(200, user)
    
    def _handle_get_repos(self, token: str, query_params: Dict):
        """Handle GET /user/repos endpoint."""
        # Support pagination
        page = int(query_params.get('page', ['1'])[0])
        per_page = int(query_params.get('per_page', ['30'])[0])
        
        start = (page - 1) * per_page
        end = start + per_page
        
        repos = self.repositories[start:end] if self.repositories else [self._default_repo()]
        self._send_json(200, repos)
    
    def _handle_get_branches(self, owner: str, repo: str):
        """Handle GET /repos/{owner}/{repo}/branches endpoint."""
        repo_key = f"{owner}/{repo}"
        branches = self.branches.get(repo_key, [self._default_branch()])
        self._send_json(200, branches)
    
    def _handle_get_file(self, owner: str, repo: str, file_path: str):
        """Handle GET /repos/{owner}/{repo}/contents/{path} endpoint."""
        file_key = f"{owner}/{repo}/{file_path}"
        file_data = self.files.get(file_key, self._default_file(file_path))
        self._send_json(200, file_data)
    
    def _handle_create_branch(self, owner: str, repo: str, data: Dict):
        """Handle POST /repos/{owner}/{repo}/git/refs endpoint."""
        ref = data.get('ref', '')
        sha = data.get('sha', 'abc123def456')
        
        branch_name = ref.replace('refs/heads/', '')
        branch = {
            "ref": ref,
            "node_id": "MDM6UmVmMTIzNDU2Nzg5OnJlZnMvaGVhZHMvbWFpbg==",
            "url": f"https://api.github.com/repos/{owner}/{repo}/git/refs/heads/{branch_name}",
            "object": {
                "sha": sha,
                "type": "commit",
                "url": f"https://api.github.com/repos/{owner}/{repo}/git/commits/{sha}"
            }
        }
        
        # Store branch
        repo_key = f"{owner}/{repo}"
        if repo_key not in self.branches:
            self.branches[repo_key] = []
        self.branches[repo_key].append({
            "name": branch_name,
            "commit": {"sha": sha},
            "protected": False
        })
        
        self._send_json(201, branch)
    
    def _handle_update_file(self, owner: str, repo: str, file_path: str, data: Dict):
        """Handle PUT /repos/{owner}/{repo}/contents/{path} endpoint."""
        content = data.get('content', '')
        message = data.get('message', 'Update file')
        sha = data.get('sha', None)
        
        file_key = f"{owner}/{repo}/{file_path}"
        
        # Check if file exists and SHA matches (optimistic locking)
        if file_key in self.files and sha and self.files[file_key]['sha'] != sha:
            self._send_error(409, "Conflict: File has been modified")
            return
        
        # Update file
        new_sha = f"new_{datetime.utcnow().timestamp()}"
        self.files[file_key] = {
            "name": file_path.split('/')[-1],
            "path": file_path,
            "sha": new_sha,
            "content": content,
            "encoding": "base64"
        }
        
        response = {
            "content": self.files[file_key],
            "commit": {
                "sha": new_sha,
                "message": message,
                "author": {"name": "Test User", "email": "test@example.com"}
            }
        }
        
        self._send_json(200, response)
    
    # ========================================================================
    # Default Data Generators
    # ========================================================================
    
    def _default_user(self, username: str = "testuser") -> Dict:
        """Generate default user data."""
        return {
            "login": username,
            "id": 12345678,
            "node_id": "MDQ6VXNlcjEyMzQ1Njc4",
            "avatar_url": f"https://avatars.githubusercontent.com/u/12345678",
            "gravatar_id": "",
            "url": f"https://api.github.com/users/{username}",
            "html_url": f"https://github.com/{username}",
            "type": "User",
            "name": "Test User",
            "email": f"{username}@example.com",
            "public_repos": 10,
            "followers": 5,
            "following": 3
        }
    
    def _default_repo(self) -> Dict:
        """Generate default repository data."""
        return {
            "id": 123456789,
            "node_id": "MDEwOlJlcG9zaXRvcnkxMjM0NTY3ODk=",
            "name": "test-repo",
            "full_name": "testuser/test-repo",
            "owner": {"login": "testuser", "id": 12345678},
            "private": False,
            "html_url": "https://github.com/testuser/test-repo",
            "description": "Test repository",
            "fork": False,
            "url": "https://api.github.com/repos/testuser/test-repo",
            "default_branch": "main",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-02-18T00:00:00Z",
            "pushed_at": "2026-02-18T00:00:00Z"
        }
    
    def _default_branch(self, name: str = "main") -> Dict:
        """Generate default branch data."""
        return {
            "name": name,
            "commit": {
                "sha": "abc123def456",
                "url": "https://api.github.com/repos/testuser/test-repo/commits/abc123"
            },
            "protected": name == "main"
        }
    
    def _default_file(self, path: str) -> Dict:
        """Generate default file data."""
        content = base64.b64encode(b"# Test File\n\nThis is a test file.").decode('utf-8')
        return {
            "name": path.split('/')[-1],
            "path": path,
            "sha": "file_abc123",
            "size": 30,
            "url": f"https://api.github.com/repos/testuser/test-repo/contents/{path}",
            "html_url": f"https://github.com/testuser/test-repo/blob/main/{path}",
            "git_url": f"https://api.github.com/repos/testuser/test-repo/git/blobs/file_abc123",
            "type": "file",
            "content": content,
            "encoding": "base64"
        }
    
    # ========================================================================
    # Utility Methods
    # ========================================================================
    
    def _extract_token(self, auth_header: str) -> Optional[str]:
        """Extract token from Authorization header."""
        if auth_header.startswith('Bearer '):
            return auth_header[7:]
        elif auth_header.startswith('token '):
            return auth_header[6:]
        return None
    
    def _validate_token(self, token: Optional[str]) -> bool:
        """Validate GitHub token."""
        if not token:
            return False
        # Accept any test token or token in the tokens dict
        return token.startswith('ghp_test_') or token in self.tokens
    
    def _send_json(self, status_code: int, data: Any):
        """Send JSON response."""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
    def _send_error(self, status_code: int, message: str):
        """Send error response."""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        error = {"message": message, "documentation_url": "https://docs.github.com/rest"}
        self.wfile.write(json.dumps(error).encode('utf-8'))
    
    def log_message(self, format, *args):
        """Suppress default logging (comment out for debugging)."""
        pass


class MockGitHubServer:
    """Mock GitHub API server for testing."""
    
    def __init__(self, host: str = 'localhost', port: int = 8888):
        self.host = host
        self.port = port
        self.server: Optional[HTTPServer] = None
        self.thread: Optional[threading.Thread] = None
    
    def start(self):
        """Start the mock server in a background thread."""
        self.server = HTTPServer((self.host, self.port), MockGitHubAPIHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        print(f"Mock GitHub API server running on http://{self.host}:{self.port}")
    
    def stop(self):
        """Stop the mock server."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        if self.thread:
            self.thread.join(timeout=1)
        print("Mock GitHub API server stopped")
    
    @property
    def base_url(self) -> str:
        """Get base URL of the mock server."""
        return f"http://{self.host}:{self.port}"
    
    def add_repository(self, repo_data: Dict):
        """Add a repository to the mock server."""
        MockGitHubAPIHandler.repositories.append(repo_data)
    
    def add_branch(self, owner: str, repo: str, branch_data: Dict):
        """Add a branch to a repository."""
        repo_key = f"{owner}/{repo}"
        if repo_key not in MockGitHubAPIHandler.branches:
            MockGitHubAPIHandler.branches[repo_key] = []
        MockGitHubAPIHandler.branches[repo_key].append(branch_data)
    
    def add_file(self, owner: str, repo: str, file_path: str, file_data: Dict):
        """Add a file to a repository."""
        file_key = f"{owner}/{repo}/{file_path}"
        MockGitHubAPIHandler.files[file_key] = file_data
    
    def add_user(self, username: str, user_data: Dict):
        """Add a user to the mock server."""
        MockGitHubAPIHandler.users[username] = user_data
    
    def add_token(self, token: str, username: str):
        """Map a token to a username."""
        MockGitHubAPIHandler.tokens[token] = username
    
    def clear_data(self):
        """Clear all mock data."""
        MockGitHubAPIHandler.repositories.clear()
        MockGitHubAPIHandler.branches.clear()
        MockGitHubAPIHandler.files.clear()
        MockGitHubAPIHandler.users.clear()
        MockGitHubAPIHandler.tokens.clear()


# ============================================================================
# Pytest Fixture (add to conftest.py)
# ============================================================================

# @pytest.fixture(scope="session")
# def mock_github_server():
#     """Start mock GitHub API server for testing."""
#     server = MockGitHubServer()
#     server.start()
#     
#     # Add default test data
#     server.add_token("ghp_test_token_1234567890", "testuser")
#     
#     yield server
#     
#     server.stop()
