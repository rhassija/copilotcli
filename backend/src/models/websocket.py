"""
WebSocket models for real-time communication.

Models:
- WebSocketSession: Active WebSocket connection
- WebSocketMessage: Message sent over WebSocket
- MessageType: Types of messages (thinking, execution, error, complete)
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum


class MessageType(str, Enum):
    """WebSocket message types."""
    THINKING = "thinking"  # AI thinking/planning messages
    EXECUTION = "execution"  # Task execution messages
    ERROR = "error"  # Error messages
    COMPLETE = "complete"  # Operation complete message
    PROGRESS = "progress"  # Progress update
    QUESTION = "question"  # Question from AI (for clarify operations)
    ANSWER = "answer"  # User answer to question
    CONNECTION = "connection"  # Connection status messages


class MessagePriority(str, Enum):
    """Message priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class WebSocketMessage(BaseModel):
    """
    WebSocket message model.
    
    Represents a single message sent over WebSocket connection.
    """
    message_id: str = Field(..., description="Unique message identifier")
    operation_id: str = Field(..., description="Operation this message belongs to")
    sequence: int = Field(..., description="Message sequence number (for ordering)")
    
    # Message content
    type: MessageType = Field(..., description="Message type")
    content: str = Field(..., description="Message text content")
    
    # Optional structured data
    data: Optional[Dict[str, Any]] = Field(None, description="Additional structured data")
    
    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message creation time")
    priority: MessagePriority = Field(default=MessagePriority.NORMAL, description="Message priority")
    
    # Message attributes
    is_final: bool = Field(default=False, description="Whether this is the final message")
    requires_acknowledgment: bool = Field(default=False, description="Whether message needs ACK")
    
    # UI hints
    collapsible: bool = Field(default=False, description="Whether message can be collapsed in UI")
    formatted: bool = Field(default=False, description="Whether content contains formatting")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message_id": "msg_abc123xyz789",
                "operation_id": "op_clarify_001",
                "sequence": 5,
                "type": "thinking",
                "content": "Analyzing the feature requirements to identify potential ambiguities...",
                "data": None,
                "timestamp": "2026-02-18T10:15:30Z",
                "priority": "normal",
                "is_final": False,
                "requires_acknowledgment": False,
                "collapsible": True,
                "formatted": False
            }
        }


class OperationStatus(str, Enum):
    """Operation execution status."""
    PENDING = "pending"  # Operation queued
    RUNNING = "running"  # Operation in progress
    PAUSED = "paused"  # Operation paused (waiting for user input)
    COMPLETED = "completed"  # Operation finished successfully
    FAILED = "failed"  # Operation failed with error
    CANCELLED = "cancelled"  # Operation cancelled by user


class WebSocketSession(BaseModel):
    """
    Active WebSocket connection session.
    
    Tracks an open WebSocket connection and its associated operations.
    """
    connection_id: str = Field(..., description="Unique connection identifier")
    user_id: int = Field(..., description="GitHub user ID")
    session_id: str = Field(..., description="Auth session ID")
    
    # Connection details
    connected_at: datetime = Field(default_factory=datetime.utcnow, description="Connection establishment time")
    last_ping_at: datetime = Field(default_factory=datetime.utcnow, description="Last ping timestamp")
    client_info: Optional[Dict[str, str]] = Field(None, description="Client metadata (user agent, etc.)")
    
    # Active operations
    active_operations: List[str] = Field(default_factory=list, description="List of active operation IDs")
    
    # Message tracking
    last_message_sequence: int = Field(default=0, description="Last sent message sequence number")
    acknowledged_sequence: int = Field(default=0, description="Last acknowledged sequence number")
    
    # Connection state
    is_connected: bool = Field(default=True, description="Whether connection is active")
    reconnect_attempts: int = Field(default=0, description="Number of reconnection attempts")
    
    class Config:
        json_schema_extra = {
            "example": {
                "connection_id": "conn_abc123xyz789",
                "user_id": 12345678,
                "session_id": "sess_xyz789abc123",
                "connected_at": "2026-02-18T10:00:00Z",
                "last_ping_at": "2026-02-18T10:15:00Z",
                "client_info": {
                    "user_agent": "Mozilla/5.0...",
                    "ip_address": "192.168.1.100"
                },
                "active_operations": ["op_clarify_001", "op_analyze_002"],
                "last_message_sequence": 42,
                "acknowledged_sequence": 40,
                "is_connected": True,
                "reconnect_attempts": 0
            }
        }


class Operation(BaseModel):
    """
    Long-running operation tracked via WebSocket.
    
    Represents a Copilot CLI operation (clarify, analyze, implement, etc.)
    that streams progress via WebSocket.
    """
    operation_id: str = Field(..., description="Unique operation identifier")
    operation_type: str = Field(..., description="Type of operation (clarify/analyze/implement)")
    
    # Associated entities
    feature_id: str = Field(..., description="Feature this operation is for")
    user_id: int = Field(..., description="User who initiated operation")
    connection_id: str = Field(..., description="WebSocket connection ID")
    
    # Operation state
    status: OperationStatus = Field(default=OperationStatus.PENDING, description="Current status")
    progress_percentage: int = Field(default=0, ge=0, le=100, description="Progress (0-100)")
    
    # Timestamps
    started_at: datetime = Field(default_factory=datetime.utcnow, description="Operation start time")
    completed_at: Optional[datetime] = Field(None, description="Operation completion time")
    
    # Messages
    message_count: int = Field(default=0, description="Number of messages sent")
    
    # Result
    result: Optional[Dict[str, Any]] = Field(None, description="Operation result data")
    error: Optional[str] = Field(None, description="Error message if failed")
    
    # Metadata
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional operation metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "operation_id": "op_clarify_001",
                "operation_type": "clarify",
                "feature_id": "feat_xyz789",
                "user_id": 12345678,
                "connection_id": "conn_abc123",
                "status": "running",
                "progress_percentage": 65,
                "started_at": "2026-02-18T10:00:00Z",
                "completed_at": None,
                "message_count": 25,
                "result": None,
                "error": None,
                "metadata": {
                    "spec_document_id": "doc_spec_abc123"
                }
            }
        }


# ============================================================================
# WebSocket Connection Management
# ============================================================================

class WebSocketConnectRequest(BaseModel):
    """Request model for establishing WebSocket connection."""
    session_id: str = Field(..., description="Auth session ID")
    client_info: Optional[Dict[str, str]] = Field(None, description="Client metadata")


class WebSocketConnectResponse(BaseModel):
    """Response model for WebSocket connection establishment."""
    connection_id: str = Field(..., description="Assigned connection ID")
    message: str = Field(default="WebSocket connection established", description="Status message")


class WebSocketDisconnectRequest(BaseModel):
    """Request model for closing WebSocket connection."""
    connection_id: str = Field(..., description="Connection ID to close")
    reason: Optional[str] = Field(None, description="Disconnect reason")


# ============================================================================
# Message Replay & Synchronization
# ============================================================================

class MessageReplayRequest(BaseModel):
    """Request model for replaying missed messages."""
    operation_id: str = Field(..., description="Operation ID")
    from_sequence: int = Field(..., description="Start replaying from this sequence number")
    to_sequence: Optional[int] = Field(None, description="End sequence (None = latest)")


class MessageReplayResponse(BaseModel):
    """Response model for message replay."""
    messages: List[WebSocketMessage] = Field(..., description="Replayed messages")
    latest_sequence: int = Field(..., description="Latest available sequence number")


class MessageAcknowledgment(BaseModel):
    """Message acknowledgment from client."""
    connection_id: str = Field(..., description="Connection ID")
    sequence: int = Field(..., description="Acknowledged sequence number")


# ============================================================================
# Operation Management
# ============================================================================

class StartOperationRequest(BaseModel):
    """Request model for starting a new operation."""
    operation_type: str = Field(..., description="Operation type (clarify/analyze/implement)")
    feature_id: str = Field(..., description="Feature ID")
    connection_id: str = Field(..., description="WebSocket connection ID")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Operation parameters")


class StartOperationResponse(BaseModel):
    """Response model for operation start."""
    operation_id: str = Field(..., description="Created operation ID")
    message: str = Field(default="Operation started successfully", description="Status message")


class CancelOperationRequest(BaseModel):
    """Request model for cancelling an operation."""
    operation_id: str = Field(..., description="Operation to cancel")


class CancelOperationResponse(BaseModel):
    """Response model for operation cancellation."""
    operation_id: str = Field(..., description="Cancelled operation ID")
    message: str = Field(default="Operation cancelled successfully", description="Status message")


class GetOperationStatusRequest(BaseModel):
    """Request model for checking operation status."""
    operation_id: str = Field(..., description="Operation ID")


class GetOperationStatusResponse(BaseModel):
    """Response model for operation status."""
    operation: Operation = Field(..., description="Operation details")
