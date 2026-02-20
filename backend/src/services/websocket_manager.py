"""
WebSocket connection manager for real-time communication.

Handles:
- Connection lifecycle management
- Message queuing per operation
- Broadcasting to multiple clients
- Reconnection with message replay
- Message history retention
"""

import asyncio
import logging
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from collections import defaultdict

from fastapi import WebSocket, WebSocketDisconnect

from src.models.websocket import (
    WebSocketSession,
    WebSocketMessage,
    Operation,
    MessageType,
    MessagePriority
)
from src.services.storage import storage

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections and message delivery.
    
    Features:
    - Track active connections per user/session
    - Queue messages per operation
    - Broadcast to all clients subscribed to an operation
    - Support reconnection with message replay
    - Retain message history with TTL
    """
    
    # Message history retention (10 minutes)
    MESSAGE_RETENTION_MINUTES = 10
    
    def __init__(self):
        """Initialize connection manager."""
        # Active WebSocket connections: connection_id -> WebSocket
        self._connections: Dict[str, WebSocket] = {}
        
        # Operation subscriptions: operation_id -> Set[connection_id]
        self._operation_subscriptions: Dict[str, Set[str]] = defaultdict(set)
        
        # Connection to session mapping: connection_id -> session_id
        self._connection_sessions: Dict[str, str] = {}
        
        # Message queues per operation: operation_id -> List[WebSocketMessage]
        # (This is redundant with storage, but provides fast access)
        self._message_queues: Dict[str, List[WebSocketMessage]] = defaultdict(list)
        
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()
    
    # ========================================================================
    # Connection Management
    # ========================================================================
    
    async def connect(
        self,
        websocket: WebSocket,
        connection_id: str,
        session_id: str,
        user_id: int
    ) -> WebSocketSession:
        """
        Register a new WebSocket connection.
        
        Args:
            websocket: FastAPI WebSocket instance
            connection_id: Unique connection ID
            session_id: User session ID
            user_id: User ID
        
        Returns:
            Created WebSocketSession
        """
        await websocket.accept()
        
        async with self._lock:
            self._connections[connection_id] = websocket
            self._connection_sessions[connection_id] = session_id
        
        # Create WebSocket session
        ws_session = WebSocketSession(
            connection_id=connection_id,
            user_id=user_id,
            session_id=session_id,
            active_operations=[],
            last_message_sequence=0,
            acknowledged_sequence=0,
            is_connected=True,
            connected_at=datetime.utcnow()
        )
        
        storage.save_ws_session(ws_session)
        
        logger.info(f"WebSocket connected: {connection_id} (user: {user_id})")
        
        return ws_session
    
    async def disconnect(self, connection_id: str):
        """
        Disconnect and cleanup WebSocket connection.
        
        Args:
            connection_id: Connection ID to disconnect
        """
        async with self._lock:
            # Remove from connections
            websocket = self._connections.pop(connection_id, None)
            session_id = self._connection_sessions.pop(connection_id, None)
            
            # Remove from all operation subscriptions
            for operation_id in list(self._operation_subscriptions.keys()):
                self._operation_subscriptions[operation_id].discard(connection_id)
                
                # Clean up empty subscription sets
                if not self._operation_subscriptions[operation_id]:
                    del self._operation_subscriptions[operation_id]
        
        # Update session in storage
        ws_session = storage.get_ws_session(connection_id)
        if ws_session:
            ws_session.is_connected = False
            storage.save_ws_session(ws_session)
        
        logger.info(f"WebSocket disconnected: {connection_id}")
    
    async def subscribe_to_operation(self, connection_id: str, operation_id: str):
        """
        Subscribe connection to operation messages.
        
        Args:
            connection_id: Connection ID
            operation_id: Operation ID to subscribe to
        """
        async with self._lock:
            self._operation_subscriptions[operation_id].add(connection_id)
        
        # Update session
        ws_session = storage.get_ws_session(connection_id)
        if ws_session:
            if operation_id not in ws_session.active_operations:
                ws_session.active_operations.append(operation_id)
                storage.save_ws_session(ws_session)
        
        logger.debug(f"Connection {connection_id} subscribed to operation {operation_id}")
    
    async def unsubscribe_from_operation(self, connection_id: str, operation_id: str):
        """
        Unsubscribe connection from operation messages.
        
        Args:
            connection_id: Connection ID
            operation_id: Operation ID to unsubscribe from
        """
        async with self._lock:
            if operation_id in self._operation_subscriptions:
                self._operation_subscriptions[operation_id].discard(connection_id)
                
                if not self._operation_subscriptions[operation_id]:
                    del self._operation_subscriptions[operation_id]
        
        # Update session
        ws_session = storage.get_ws_session(connection_id)
        if ws_session:
            if operation_id in ws_session.active_operations:
                ws_session.active_operations.remove(operation_id)
                storage.save_ws_session(ws_session)
        
        logger.debug(f"Connection {connection_id} unsubscribed from operation {operation_id}")
    
    # ========================================================================
    # Message Delivery
    # ========================================================================
    
    async def send_message(self, connection_id: str, message: WebSocketMessage):
        """
        Send message to a specific connection.
        
        Args:
            connection_id: Target connection ID
            message: Message to send
        """
        async with self._lock:
            websocket = self._connections.get(connection_id)
        
        if websocket:
            try:
                await websocket.send_json(message.model_dump(mode="json"))
                logger.debug(f"Sent message {message.message_id} to {connection_id}")
            except Exception as e:
                logger.error(f"Failed to send message to {connection_id}: {e}")
                await self.disconnect(connection_id)
    
    async def broadcast_to_operation(self, operation_id: str, message: WebSocketMessage):
        """
        Broadcast message to all connections subscribed to operation.
        
        Args:
            operation_id: Operation ID
            message: Message to broadcast
        """
        # Add to message queue
        async with self._lock:
            self._message_queues[operation_id].append(message)
        
        # Store in persistent storage
        storage.add_ws_message(message)
        
        # Get subscribed connections
        async with self._lock:
            subscriber_ids = list(self._operation_subscriptions.get(operation_id, set()))
        
        # Send to all subscribers
        send_tasks = []
        for connection_id in subscriber_ids:
            send_tasks.append(self.send_message(connection_id, message))
        
        if send_tasks:
            await asyncio.gather(*send_tasks, return_exceptions=True)
        
        logger.debug(f"Broadcasted message {message.message_id} to {len(subscriber_ids)} connections")
    
    async def broadcast_to_user(self, user_id: int, message: WebSocketMessage):
        """
        Broadcast message to all connections for a user.
        
        Args:
            user_id: User ID
            message: Message to broadcast
        """
        # Get all user sessions
        sessions = storage.list_ws_sessions(user_id=user_id)
        
        # Send to all connected sessions
        send_tasks = []
        for ws_session in sessions:
            if ws_session.is_connected:
                send_tasks.append(self.send_message(ws_session.connection_id, message))
        
        if send_tasks:
            await asyncio.gather(*send_tasks, return_exceptions=True)
        
        logger.debug(f"Broadcasted message to {len(send_tasks)} connections for user {user_id}")
    
    # ========================================================================
    # Message Replay (for reconnection)
    # ========================================================================
    
    async def replay_messages(
        self,
        connection_id: str,
        operation_id: str,
        from_sequence: int
    ) -> int:
        """
        Replay messages from a specific sequence number.
        
        Args:
            connection_id: Connection ID to replay to
            operation_id: Operation ID
            from_sequence: Starting sequence number (exclusive)
        
        Returns:
            Number of messages replayed
        """
        # Get messages from storage
        messages = storage.get_ws_messages(operation_id, from_sequence=from_sequence + 1)
        
        # Send messages in sequence
        for message in messages:
            await self.send_message(connection_id, message)
        
        logger.info(f"Replayed {len(messages)} messages to {connection_id} for operation {operation_id}")
        
        return len(messages)
    
    # ========================================================================
    # Message History Cleanup
    # ========================================================================
    
    async def cleanup_old_messages(self) -> int:
        """
        Remove old messages from history.
        
        Returns:
            Number of messages removed
        """
        # Clean up from storage
        removed_count = storage.cleanup_old_ws_messages(
            retention_minutes=self.MESSAGE_RETENTION_MINUTES
        )
        
        # Clean up in-memory queues
        cutoff_time = datetime.utcnow() - timedelta(minutes=self.MESSAGE_RETENTION_MINUTES)
        
        async with self._lock:
            for operation_id in list(self._message_queues.keys()):
                original_count = len(self._message_queues[operation_id])
                self._message_queues[operation_id] = [
                    msg for msg in self._message_queues[operation_id]
                    if msg.timestamp > cutoff_time
                ]
                
                # Remove empty queues
                if not self._message_queues[operation_id]:
                    del self._message_queues[operation_id]
        
        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} old messages")
        
        return removed_count
    
    # ========================================================================
    # Stats & Monitoring
    # ========================================================================
    
    def get_connection_count(self) -> int:
        """Get number of active connections."""
        return len(self._connections)
    
    def get_operation_subscriber_count(self, operation_id: str) -> int:
        """Get number of subscribers for an operation."""
        return len(self._operation_subscriptions.get(operation_id, set()))
    
    def get_active_operations(self) -> List[str]:
        """Get list of operations with active subscribers."""
        return list(self._operation_subscriptions.keys())
    
    def is_connected(self, connection_id: str) -> bool:
        """Check if connection is active."""
        return connection_id in self._connections


# Global connection manager instance
connection_manager = ConnectionManager()
