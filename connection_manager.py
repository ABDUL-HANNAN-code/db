from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Set
import json
import asyncio
from app.utils.redis_client import redis_client
from app.database import get_database
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # Store active connections: {user_id: {websocket_objects}}
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Store user channels for Redis pub/sub
        self.user_channels: Dict[str, str] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept WebSocket connection and add to active connections"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        self.active_connections[user_id].add(websocket)
        
        # Set user online in Redis
        await redis_client.set_user_online(user_id)
        
        # Subscribe to user's personal channel
        user_channel = f"user_channel:{user_id}"
        self.user_channels[user_id] = user_channel
        await redis_client.subscribe(user_channel)
        
        # Notify friends that user is online
        await self._notify_friends_status(user_id, True)
        
        logger.info(f"User {user_id} connected via WebSocket")
    
    async def disconnect(self, websocket: WebSocket, user_id: str):
        """Remove WebSocket connection"""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            
            # If no more connections for this user
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                
                # Set user offline
                await redis_client.set_user_offline(user_id)
                
                # Unsubscribe from user channel
                if user_id in self.user_channels:
                    await redis_client.unsubscribe(self.user_channels[user_id])
                    del self.user_channels[user_id]
                
                # Notify friends that user is offline
                await self._notify_friends_status(user_id, False)
        
        logger.info(f"User {user_id} disconnected from WebSocket")
    
    async def send_personal_message(self, user_id: str, message: dict):
        """Send message to specific user via Redis pub/sub"""
        user_channel = f"user_channel:{user_id}"
        await redis_client.publish(user_channel, message)
    
    async def send_to_conversation(self, conversation_id: str, message: dict, exclude_user: str = None):
        """Send message to all participants in a conversation"""
        db = await get_database()
        
        # Get conversation participants
        conversation = await db.conversations.find_one({"_id": ObjectId(conversation_id)})
        if not conversation:
            return
        
        # Send to all participants except the sender
        for participant_id in conversation["participants"]:
            if participant_id != exclude_user:
                await self.send_personal_message(participant_id, message)
    
    async def broadcast_to_friends(self, user_id: str, message: dict):
        """Broadcast message to all user's friends"""
        db = await get_database()
        
        # Get user's friends
        friends_cursor = db.friendships.find({
            "$or": [
                {"requester_id": user_id, "status": "accepted"},
                {"addressee_id": user_id, "status": "accepted"}
            ]
        })
        
        async for friendship in friends_cursor:
            friend_id = (friendship["addressee_id"] 
                        if friendship["requester_id"] == user_id 
                        else friendship["requester_id"])
            await self.send_personal_message(friend_id, message)
    
    async def _notify_friends_status(self, user_id: str, is_online: bool):
        """Notify friends about user's online status"""
        status_message = {
            "type": "user_status",
            "user_id": user_id,
            "is_online": is_online,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast_to_friends(user_id, status_message)
    
    async def get_online_users(self) -> List[str]:
        """Get list of currently online users"""
        return list(self.active_connections.keys())
    
    async def is_user_online(self, user_id: str) -> bool:
        """Check if specific user is online"""
        return user_id in self.active_connections

# Global connection manager instance
connection_manager = ConnectionManager()
