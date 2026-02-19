"""
WebSocket API routes for real-time communication.

Provides:
- WebSocket connection endpoint
- Message streaming
- Operation subscriptions
- Reconnection with message replay
"""

import asyncio
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends, status
from fastapi.responses import JSONResponse

from src.models.websocket import (
    WebSocketMessage,
    WebSocketSession,
    MessageType,
    MessagePriority,
    WebSocketConnectRequest,
    WebSocketConnectResponse,
    MessageReplayRequest,
    MessageAcknowledgment
)
from src.services.websocket_manager import connection_manager
from src.services.auth_service import auth_service
from src.services.storage import storage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/connect")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str = Query(..., description="User session ID")
):
    """
    WebSocket connection endpoint.
    
    Establishes persistent connection for real-time message delivery.
    Supports operation subscriptions and message replay on reconnection.
    
    Query Parameters:
    - session_id: User session ID for authentication
    
    Message Flow:
    1. Client connects with session_id
    2. Server validates session and accepts connection
    3. Client sends subscription requests for operations
    4. Server streams messages for subscribed operations
    5. Client can request message replay for missed messages
    6. Client sends acknowledgments to track delivery
    """
    connection_id = str(uuid.uuid4())
    
    # Validate session
    session = auth_service.get_session(session_id)
    if not session:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid session")
        logger.warning(f"WebSocket connection rejected: invalid session {session_id}")
        return
    
    user_id = session.user.id
    
    try:
        # Connect and register
        ws_session = await connection_manager.connect(
            websocket=websocket,
            connection_id=connection_id,
            session_id=session_id,
            user_id=user_id
        )
        
        # Send connection confirmation
        connection_message = WebSocketMessage(
            message_id=str(uuid.uuid4()),
            operation_id="system",
            sequence=0,
            type=MessageType.CONNECTION,
            content="Connected successfully",
            data={
                "connection_id": connection_id,
                "user_id": user_id
            },
            timestamp=ws_session.connected_at,
            priority=MessagePriority.HIGH,
            is_final=False,
            collapsible=False
        )
        
        await websocket.send_json(connection_message.model_dump())
        
        # Message handling loop
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_json()
                
                # Parse message type
                message_type = data.get("type")
                
                if message_type == "subscribe":
                    # Subscribe to operation
                    operation_id = data.get("operation_id")
                    if operation_id:
                        await connection_manager.subscribe_to_operation(connection_id, operation_id)
                        
                        # Send confirmation
                        confirm_msg = WebSocketMessage(
                            message_id=str(uuid.uuid4()),
                            operation_id=operation_id,
                            sequence=0,
                            type=MessageType.CONNECTION,
                            content=f"Subscribed to operation {operation_id}",
                            timestamp=datetime.utcnow(),
                            priority=MessagePriority.NORMAL,
                            is_final=False,
                            collapsible=False
                        )
                        await websocket.send_json(confirm_msg.model_dump())
                
                elif message_type == "unsubscribe":
                    # Unsubscribe from operation
                    operation_id = data.get("operation_id")
                    if operation_id:
                        await connection_manager.unsubscribe_from_operation(connection_id, operation_id)
                
                elif message_type == "replay":
                    # Replay messages from sequence
                    operation_id = data.get("operation_id")
                    from_sequence = data.get("from_sequence", 0)
                    
                    if operation_id:
                        count = await connection_manager.replay_messages(
                            connection_id,
                            operation_id,
                            from_sequence
                        )
                        
                        # Send replay complete message
                        replay_msg = WebSocketMessage(
                            message_id=str(uuid.uuid4()),
                            operation_id=operation_id,
                            sequence=0,
                            type=MessageType.CONNECTION,
                            content=f"Replayed {count} messages",
                            data={"replayed_count": count},
                            timestamp=datetime.utcnow(),
                            priority=MessagePriority.NORMAL,
                            is_final=False,
                            collapsible=False
                        )
                        await websocket.send_json(replay_msg.model_dump())
                
                elif message_type == "acknowledge":
                    # Update acknowledged sequence
                    operation_id = data.get("operation_id")
                    sequence = data.get("sequence")
                    
                    if operation_id and sequence is not None:
                        ws_session = storage.get_ws_session(connection_id)
                        if ws_session:
                            ws_session.acknowledged_sequence = max(
                                ws_session.acknowledged_sequence,
                                sequence
                            )
                            storage.save_ws_session(ws_session)
                
                elif message_type == "ping":
                    # Respond to ping
                    pong_msg = WebSocketMessage(
                        message_id=str(uuid.uuid4()),
                        operation_id="system",
                        sequence=0,
                        type=MessageType.CONNECTION,
                        content="pong",
                        timestamp=datetime.utcnow(),
                        priority=MessagePriority.NORMAL,
                        is_final=False,
                        collapsible=False
                    )
                    await websocket.send_json(pong_msg.model_dump())
            
            except WebSocketDisconnect:
                break
            
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                # Send error message
                error_msg = WebSocketMessage(
                    message_id=str(uuid.uuid4()),
                    operation_id="system",
                    sequence=0,
                    type=MessageType.ERROR,
                    content=f"Error: {str(e)}",
                    timestamp=datetime.utcnow(),
                    priority=MessagePriority.HIGH,
                    is_final=False,
                    collapsible=False
                )
                try:
                    await websocket.send_json(error_msg.model_dump())
                except:
                    break
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {connection_id}")
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    
    finally:
        # Cleanup
        await connection_manager.disconnect(connection_id)


@router.get("/stats")
async def get_websocket_stats():
    """
    Get WebSocket connection statistics.
    
    Returns:
    - active_connections: Number of active WebSocket connections
    - active_operations: List of operations with subscribers
    - storage_stats: Message storage statistics
    """
    return {
        "active_connections": connection_manager.get_connection_count(),
        "active_operations": connection_manager.get_active_operations(),
        "storage_stats": storage.get_stats()
    }


@router.post("/cleanup")
async def cleanup_old_messages():
    """
    Manually trigger cleanup of old messages.
    
    Removes messages older than retention period.
    """
    removed_count = await connection_manager.cleanup_old_messages()
    
    return {
        "status": "success",
        "removed_messages": removed_count
    }


# Import datetime for message timestamps
from datetime import datetime
