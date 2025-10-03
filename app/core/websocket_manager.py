from typing import Dict, Set
from uuid import UUID
from fastapi import WebSocket
import json
from datetime import datetime


class ConnectionManager:
    """Manage WebSocket connections for real-time events"""
    
    def __init__(self):
        # Store active connections: {user_id: Set[WebSocket]}
        self.active_connections: Dict[UUID, Set[WebSocket]] = {}
    
    async def connect(self, user_id: UUID, websocket: WebSocket):
        """Add a new WebSocket connection for a user"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        self.active_connections[user_id].add(websocket)
        
        print(f"WebSocket connected: user_id={user_id}, total_connections={len(self.active_connections[user_id])}")
    
    def disconnect(self, user_id: UUID, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            
            # Clean up empty sets
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        
        print(f"WebSocket disconnected: user_id={user_id}")
    
    async def send_to_user(self, user_id: UUID, message: dict):
        """
        Send message to all connections of a specific user
        
        Args:
            user_id: Target user UUID
            message: Dictionary to send as JSON
        """
        if user_id not in self.active_connections:
            # User not connected, skip
            return
        
        # Get all active connections for this user
        connections = self.active_connections[user_id].copy()
        
        # Send to all connections (user might have multiple tabs/devices)
        disconnected = set()
        
        for websocket in connections:
            try:
                await websocket.send_json(message)
            except Exception as e:
                print(f"Failed to send to websocket: {e}")
                disconnected.add(websocket)
        
        # Clean up failed connections
        for ws in disconnected:
            self.disconnect(user_id, ws)
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected users"""
        for user_id in list(self.active_connections.keys()):
            await self.send_to_user(user_id, message)
    
    def get_connected_users(self) -> list[UUID]:
        """Get list of currently connected user IDs"""
        return list(self.active_connections.keys())
    
    def get_connection_count(self, user_id: UUID) -> int:
        """Get number of active connections for a user"""
        if user_id in self.active_connections:
            return len(self.active_connections[user_id])
        return 0


# Global connection manager instance
manager = ConnectionManager()
