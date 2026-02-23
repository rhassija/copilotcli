"""
In-memory storage layer for Phase 1 implementation.

Provides thread-safe in-memory storage for:
- Authentication sessions
- Features and repositories
- Documents
- WebSocket connections and operations

Features are persisted to disk in JSON format to survive backend restarts.
Sessions are kept in-memory only (expire on restart).

Note: This will be replaced with database storage (PostgreSQL + SQLAlchemy) in Phase 2.
"""

import threading
import json
import os
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict

from src.models.auth import AuthSession, User, Token
from src.models.github import Repository, Branch, Feature
from src.models.documents import Document, Spec, Plan, Task, AnalysisResult
from src.models.websocket import WebSocketSession, WebSocketMessage, Operation


class InMemoryStorage:
    """
    Thread-safe in-memory storage for all application data.
    
    Uses dictionaries with threading.Lock for concurrent access safety.
    
    Features are persisted to disk in JSON format for durability across restarts.
    Sessions are kept in-memory only (expire on restart).
    
    Storage paths:
    - Features: ./.data/features.json
    - Operations: ./.data/operations.json
    """
    
    # Data directory for persistence
    DATA_DIR = Path("./.data")
    FEATURES_FILE = DATA_DIR / "features.json"
    OPERATIONS_FILE = DATA_DIR / "operations.json"
    
    def __init__(self):
        """Initialize storage with empty collections and load persisted data."""
        # Locks for thread-safe operations
        self._lock = threading.RLock()
        
        # Ensure data directory exists
        self.DATA_DIR.mkdir(exist_ok=True)
        
        # Authentication storage (in-memory only, not persisted)
        self._sessions: Dict[str, AuthSession] = {}  # session_id -> AuthSession
        self._users: Dict[int, User] = {}  # user_id -> User
        self._tokens: Dict[str, Token] = {}  # token_id -> Token
        
        # GitHub data storage
        self._repositories: Dict[str, Repository] = {}  # full_name -> Repository
        self._branches: Dict[str, List[Branch]] = defaultdict(list)  # repo_full_name -> [Branch]
        self._features: Dict[str, Feature] = {}  # feature_id -> Feature
        
        # Document storage
        self._documents: Dict[str, Document] = {}  # document_id -> Document
        
        # Analysis results storage
        self._analysis_results: Dict[str, AnalysisResult] = {}  # analysis_id -> AnalysisResult
        
        # WebSocket storage
        self._ws_sessions: Dict[str, WebSocketSession] = {}  # connection_id -> WebSocketSession
        self._ws_messages: Dict[str, List[WebSocketMessage]] = defaultdict(list)  # operation_id -> [Message]
        self._operations: Dict[str, Operation] = {}  # operation_id -> Operation
        
        # Caches with TTL
        self._cache: Dict[str, Any] = {}  # cache_key -> cached_value
        self._cache_expiry: Dict[str, datetime] = {}  # cache_key -> expiry_time
        
        # Load persisted data from disk
        self._load_features_from_disk()
        self._load_operations_from_disk()
        
        # Discover features from local specs directory if storage is empty
        if not self._features:
            self._discover_features_from_local_specs()
    
    # ========================================================================
    # Authentication Operations
    # ========================================================================
    
    def save_session(self, session: AuthSession) -> None:
        """Save or update an authentication session."""
        with self._lock:
            self._sessions[session.session_id] = session
            self._users[session.user.id] = session.user
            self._tokens[session.token.token_id] = session.token
    
    def get_session(self, session_id: str) -> Optional[AuthSession]:
        """Get session by ID."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session and not session.is_expired and session.is_active:
                session.refresh_access()
                return session
            return None
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        with self._lock:
            if session_id in self._sessions:
                session = self._sessions.pop(session_id)
                # Don't delete user/token as they may be used by other sessions
                return True
            return False
    
    def get_user_sessions(self, user_id: int) -> List[AuthSession]:
        """Get all active sessions for a user."""
        with self._lock:
            return [
                session for session in self._sessions.values()
                if session.user.id == user_id and not session.is_expired and session.is_active
            ]
    
    def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions. Returns number of sessions cleaned."""
        with self._lock:
            expired_ids = [
                sid for sid, session in self._sessions.items()
                if session.is_expired or not session.is_active
            ]
            for sid in expired_ids:
                del self._sessions[sid]
            return len(expired_ids)
    
    # ========================================================================
    # Repository & Feature Operations
    # ========================================================================
    
    def save_repository(self, repository: Repository) -> None:
        """Save or update a repository."""
        with self._lock:
            self._repositories[repository.full_name] = repository
    
    def get_repository(self, full_name: str) -> Optional[Repository]:
        """Get repository by full name."""
        with self._lock:
            return self._repositories.get(full_name)
    
    def list_repositories(self, user_id: int) -> List[Repository]:
        """List all repositories (filtered by user if needed)."""
        with self._lock:
            # In Phase 1, return all repos (no user filtering)
            return list(self._repositories.values())
    
    def save_branches(self, repo_full_name: str, branches: List[Branch]) -> None:
        """Save branches for a repository."""
        with self._lock:
            self._branches[repo_full_name] = branches
    
    def get_branches(self, repo_full_name: str) -> List[Branch]:
        """Get branches for a repository."""
        with self._lock:
            return self._branches.get(repo_full_name, [])
    
    def save_feature(self, feature: Feature) -> None:
        """Save or update a feature."""
        with self._lock:
            self._features[feature.feature_id] = feature
            self._persist_features_to_disk()
    
    def get_feature(self, feature_id: str) -> Optional[Feature]:
        """Get feature by ID."""
        with self._lock:
            return self._features.get(feature_id)
    
    def list_features(self, repository_full_name: Optional[str] = None, user_id: Optional[int] = None) -> List[Feature]:
        """List features with optional filtering."""
        with self._lock:
            features = list(self._features.values())
            
            if repository_full_name:
                features = [f for f in features if f.repository_full_name == repository_full_name]
            
            if user_id:
                features = [f for f in features if f.created_by_user_id == user_id]
            
            return features
    
    def delete_feature(self, feature_id: str) -> bool:
        """Delete a feature."""
        with self._lock:
            if feature_id in self._features:
                del self._features[feature_id]
                self._persist_features_to_disk()
                return True
            return False
    
    # ========================================================================
    # Document Operations
    # ========================================================================
    
    def save_document(self, document: Document) -> None:
        """Save or update a document."""
        with self._lock:
            self._documents[document.document_id] = document
    
    def get_document(self, document_id: str) -> Optional[Document]:
        """Get document by ID."""
        with self._lock:
            return self._documents.get(document_id)
    
    def get_document_by_feature_and_type(self, feature_id: str, document_type: str) -> Optional[Document]:
        """Get document by feature ID and type."""
        with self._lock:
            for doc in self._documents.values():
                if doc.feature_id == feature_id and doc.document_type == document_type:
                    return doc
            return None
    
    def list_documents(self, feature_id: str) -> List[Document]:
        """List all documents for a feature."""
        with self._lock:
            return [doc for doc in self._documents.values() if doc.feature_id == feature_id]
    
    def delete_document(self, document_id: str) -> bool:
        """Delete a document."""
        with self._lock:
            if document_id in self._documents:
                del self._documents[document_id]
                return True
            return False
    
    def save_analysis_result(self, result: AnalysisResult) -> None:
        """Save analysis result."""
        with self._lock:
            self._analysis_results[result.analysis_id] = result
    
    def get_analysis_result(self, analysis_id: str) -> Optional[AnalysisResult]:
        """Get analysis result by ID."""
        with self._lock:
            return self._analysis_results.get(analysis_id)
    
    def list_analysis_results(self, feature_id: str) -> List[AnalysisResult]:
        """List all analysis results for a feature."""
        with self._lock:
            return [r for r in self._analysis_results.values() if r.feature_id == feature_id]
    
    # ========================================================================
    # WebSocket Operations
    # ========================================================================
    
    def save_ws_session(self, ws_session: WebSocketSession) -> None:
        """Save or update WebSocket session."""
        with self._lock:
            self._ws_sessions[ws_session.connection_id] = ws_session
    
    def get_ws_session(self, connection_id: str) -> Optional[WebSocketSession]:
        """Get WebSocket session by connection ID."""
        with self._lock:
            return self._ws_sessions.get(connection_id)
    
    def delete_ws_session(self, connection_id: str) -> bool:
        """Delete WebSocket session."""
        with self._lock:
            if connection_id in self._ws_sessions:
                del self._ws_sessions[connection_id]
                return True
            return False
    
    def list_ws_sessions(self, user_id: Optional[int] = None) -> List[WebSocketSession]:
        """List WebSocket sessions, optionally filtered by user."""
        with self._lock:
            sessions = list(self._ws_sessions.values())
            if user_id:
                sessions = [s for s in sessions if s.user_id == user_id]
            return sessions
    
    def add_ws_message(self, message: WebSocketMessage) -> None:
        """Add a WebSocket message to the history."""
        with self._lock:
            self._ws_messages[message.operation_id].append(message)
    
    def get_ws_messages(self, operation_id: str, from_sequence: Optional[int] = None) -> List[WebSocketMessage]:
        """Get WebSocket messages for an operation."""
        with self._lock:
            messages = self._ws_messages.get(operation_id, [])
            if from_sequence is not None:
                messages = [m for m in messages if m.sequence >= from_sequence]
            return sorted(messages, key=lambda m: m.sequence)
    
    def cleanup_old_ws_messages(self, retention_minutes: int = 10) -> int:
        """Remove WebSocket messages older than retention period. Returns count removed."""
        with self._lock:
            cutoff_time = datetime.utcnow() - timedelta(minutes=retention_minutes)
            removed_count = 0
            
            for operation_id in list(self._ws_messages.keys()):
                original_count = len(self._ws_messages[operation_id])
                self._ws_messages[operation_id] = [
                    m for m in self._ws_messages[operation_id]
                    if m.timestamp > cutoff_time
                ]
                removed_count += original_count - len(self._ws_messages[operation_id])
                
                # Remove empty operation message lists
                if not self._ws_messages[operation_id]:
                    del self._ws_messages[operation_id]
            
            return removed_count
    
    def save_operation(self, operation: Operation) -> None:
        """Save or update an operation."""
        with self._lock:
            self._operations[operation.operation_id] = operation
            self._persist_operations_to_disk()
    
    def get_operation(self, operation_id: str) -> Optional[Operation]:
        """Get operation by ID."""
        with self._lock:
            return self._operations.get(operation_id)
    
    def list_operations(self, feature_id: Optional[str] = None, connection_id: Optional[str] = None) -> List[Operation]:
        """List operations with optional filtering."""
        with self._lock:
            operations = list(self._operations.values())
            
            if feature_id:
                operations = [op for op in operations if op.feature_id == feature_id]
            
            if connection_id:
                operations = [op for op in operations if op.connection_id == connection_id]
            
            return operations
    
    # ========================================================================
    # Cache Operations
    # ========================================================================
    
    def cache_set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        """Set a cached value with TTL."""
        with self._lock:
            self._cache[key] = value
            self._cache_expiry[key] = datetime.utcnow() + timedelta(seconds=ttl_seconds)
    
    def cache_get(self, key: str) -> Optional[Any]:
        """Get a cached value if not expired."""
        with self._lock:
            if key in self._cache:
                if datetime.utcnow() < self._cache_expiry[key]:
                    return self._cache[key]
                else:
                    # Expired, remove
                    del self._cache[key]
                    del self._cache_expiry[key]
            return None
    
    def cache_invalidate(self, pattern: Optional[str] = None) -> int:
        """Invalidate cache entries matching pattern. Returns count invalidated."""
        with self._lock:
            if pattern is None:
                # Clear all
                count = len(self._cache)
                self._cache.clear()
                self._cache_expiry.clear()
                return count
            else:
                # Clear matching pattern
                keys_to_delete = [k for k in self._cache.keys() if pattern in k]
                for key in keys_to_delete:
                    del self._cache[key]
                    if key in self._cache_expiry:
                        del self._cache_expiry[key]
                return len(keys_to_delete)
    
    # ========================================================================
    # Persistence Operations (File-based for durability across restarts)
    # ========================================================================
    
    def _load_features_from_disk(self) -> None:
        """Load features from persistent JSON storage."""
        try:
            if self.FEATURES_FILE.exists():
                with open(self.FEATURES_FILE, 'r') as f:
                    data = json.load(f)
                    for feature_id, feature_dict in data.items():
                        try:
                            # Convert string datetime fields to datetime objects if needed
                            if 'created_at' in feature_dict and isinstance(feature_dict['created_at'], str):
                                feature_dict['created_at'] = feature_dict['created_at']
                            if 'updated_at' in feature_dict and isinstance(feature_dict['updated_at'], str):
                                feature_dict['updated_at'] = feature_dict['updated_at']
                            
                            feature = Feature(**feature_dict)
                            self._features[feature_id] = feature
                            print(f"[Storage] Loaded feature: {feature_id} | repo: {feature.repository_full_name} | branch: {feature.branch_name}")
                        except Exception as e:
                            print(f"[Storage ERROR] Failed to load feature {feature_id}: {e}")
                            import traceback
                            traceback.print_exc()
                    print(f"[Storage] Successfully loaded {len(self._features)} features from disk")
            else:
                print("[Storage] No features file found - starting with empty features")
        except Exception as e:
            print(f"[Storage ERROR] Error loading features from disk: {e}")
            import traceback
            traceback.print_exc()
    
    def _load_operations_from_disk(self) -> None:
        """Load operations from persistent JSON storage."""
        try:
            if self.OPERATIONS_FILE.exists():
                with open(self.OPERATIONS_FILE, 'r') as f:
                    data = json.load(f)
                    for operation_id, operation_dict in data.items():
                        try:
                            operation = Operation(**operation_dict)
                            self._operations[operation_id] = operation
                        except Exception as e:
                            print(f"Warning: Failed to load operation {operation_id}: {e}")
                    print(f"[Storage] Loaded {len(self._operations)} operations from disk")
            else:
                print("[Storage] No operations file found - starting with empty operations")
        except Exception as e:
            print(f"[Storage] Error loading operations from disk: {e}")
    
    def _discover_features_from_local_specs(self) -> None:
        """Discover features from local specs directory without requiring GitHub API."""
        try:
            # Check both Docker path and local path
            specs_paths = [Path("/app/specs"), Path("./specs")]
            specs_dir = None
            
            for path in specs_paths:
                if path.exists() and path.is_dir():
                    specs_dir = path
                    break
            
            if not specs_dir:
                print("[Storage] No specs directory found for local feature discovery")
                return
            
            print(f"[Storage] Discovering features from local specs directory: {specs_dir}")
            discovered_count = 0
            
            # Scan all subdirectories in specs/
            for spec_path in specs_dir.iterdir():
                if not spec_path.is_dir():
                    continue
                
                spec_file = spec_path / "spec.md"
                if not spec_file.exists():
                    continue
                
                try:
                    # Read spec.md to extract title and description
                    with open(spec_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        lines = content.split('\n')
                        title = spec_path.name
                        description = ""
                        
                        # Try to extract title from first header
                        for line in lines:
                            if line.startswith('# '):
                                title = line[2:].strip()
                                break
                        
                        # Try to extract description (first non-empty paragraph after title)
                        found_title = False
                        for line in lines:
                            if line.startswith('# '):
                                found_title = True
                                continue
                            if found_title and line.strip() and not line.startswith('#'):
                                description = line.strip()
                                break
                    
                    # Check for plan.md and tasks.md
                    plan_path = None
                    task_path = None
                    if (spec_path / "plan.md").exists():
                        plan_path = f"specs/{spec_path.name}/plan.md"
                    if (spec_path / "tasks.md").exists():
                        task_path = f"specs/{spec_path.name}/tasks.md"
                    
                    # Generate deterministic feature_id from spec path
                    feature_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"local-spec-{spec_path.name}"))
                    
                    # Create Feature object
                    feature = Feature(
                        feature_id=feature_id,
                        repository_full_name="local/specs",
                        branch_name="main",
                        spec_path=f"specs/{spec_path.name}/spec.md",
                        plan_path=plan_path,
                        task_path=task_path,
                        title=title,
                        status="active",
                        created_at=datetime.now(),
                        updated_at=datetime.now(),
                        created_by_user_id=0
                    )
                    
                    self._features[feature_id] = feature
                    discovered_count += 1
                    print(f"[Storage] Discovered feature: {title} ({spec_path.name})")
                    
                except Exception as e:
                    print(f"[Storage] Error discovering feature from {spec_path}: {e}")
            
            if discovered_count > 0:
                print(f"[Storage] Discovered {discovered_count} features from local specs")
                # Persist discovered features to disk
                self._persist_features_to_disk()
            else:
                print("[Storage] No features discovered from local specs")
        
        except Exception as e:
            print(f"[Storage] Error during local feature discovery: {e}")
            import traceback
            traceback.print_exc()
    
    def _persist_features_to_disk(self) -> None:
        """Persist all features to JSON file."""
        try:
            with open(self.FEATURES_FILE, 'w') as f:
                data = {
                    feature_id: feature.dict() 
                    for feature_id, feature in self._features.items()
                }
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"[Storage] Error persisting features to disk: {e}")
    
    def _persist_operations_to_disk(self) -> None:
        """Persist all operations to JSON file."""
        try:
            with open(self.OPERATIONS_FILE, 'w') as f:
                data = {
                    operation_id: operation.dict() 
                    for operation_id, operation in self._operations.items()
                }
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"[Storage] Error persisting operations to disk: {e}")
    
    # ========================================================================
    # Utility Operations
    # ========================================================================
    
    def clear(self) -> None:
        """Clear all storage (for testing)."""
        with self._lock:
            self._sessions.clear()
            self._users.clear()
            self._tokens.clear()
            self._repositories.clear()
            self._branches.clear()
            self._features.clear()
            self._documents.clear()
            self._analysis_results.clear()
            self._ws_sessions.clear()
            self._ws_messages.clear()
            self._operations.clear()
            self._cache.clear()
            self._cache_expiry.clear()
    
    def get_stats(self) -> Dict[str, int]:
        """Get storage statistics."""
        with self._lock:
            return {
                "sessions": len(self._sessions),
                "users": len(self._users),
                "repositories": len(self._repositories),
                "features": len(self._features),
                "documents": len(self._documents),
                "analysis_results": len(self._analysis_results),
                "ws_sessions": len(self._ws_sessions),
                "operations": len(self._operations),
                "cached_items": len(self._cache),
                "total_ws_messages": sum(len(msgs) for msgs in self._ws_messages.values())
            }


# Singleton instance
storage = InMemoryStorage()
