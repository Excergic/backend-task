from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from uuid import UUID
import asyncio
from datetime import datetime

from app.core.security import decode_token
from app.core.websocket_manager import manager


router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token")
):
    """
    WebSocket endpoint for real-time events
    
    **Authentication:**
    - Pass JWT token as query parameter: /ws?token=YOUR_JWT_TOKEN
    
    **Events received:**
    - story.viewed: When someone views your story
    - story.reacted: When someone reacts to your story
    
    **Message format:**
    ```
    {
        "event": "story.viewed",
        "data": {
            "story_id": "uuid",
            "viewer_id": "uuid",
            "viewed_at": "2025-10-03T10:00:00Z"
        },
        "timestamp": "2025-10-03T10:00:00Z"
    }
    ```
    """
    user_id = None
    
    try:
        # Authenticate with JWT token
        user_id_str = decode_token(token)
        user_id = UUID(user_id_str)
    except Exception as e:
        # Authentication failed
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
        return
    
    # Accept connection
    await manager.connect(user_id, websocket)
    
    try:
        # Send welcome message
        await websocket.send_json({
            "event": "connection.established",
            "data": {
                "user_id": str(user_id),
                "message": "WebSocket connection established"
            },
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            # Receive messages from client (heartbeat/ping)
            data = await websocket.receive_text()
            
            # Echo back (optional - for heartbeat)
            if data == "ping":
                await websocket.send_json({
                    "event": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                })
    
    except WebSocketDisconnect:
        # Client disconnected normally
        manager.disconnect(user_id, websocket)
    
    except Exception as e:
        # Error occurred
        print(f"WebSocket error for user {user_id}: {e}")
        manager.disconnect(user_id, websocket)


@router.get("/ws/status")
async def websocket_status():
    """
    Get WebSocket server status
    
    Returns connected users count
    """
    connected_users = manager.get_connected_users()
    
    return {
        "status": "operational",
        "connected_users": len(connected_users),
        "total_connections": sum(
            manager.get_connection_count(user_id) 
            for user_id in connected_users
        )
    }
