import redis.asyncio as redis
import json
from typing import Any, Optional
import os
from dotenv import load_dotenv

load_dotenv()

class RedisClient:
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.client: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.PubSub] = None
    
    async def connect(self):
        """Connect to Redis"""
        self.client = redis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        self.pubsub = self.client.pubsub()
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.pubsub:
            await self.pubsub.close()
        if self.client:
            await self.client.close()
    
    async def publish(self, channel: str, message: dict):
        """Publish message to channel"""
        if self.client:
            await self.client.publish(channel, json.dumps(message))
    
    async def subscribe(self, channel: str):
        """Subscribe to channel"""
        if self.pubsub:
            await self.pubsub.subscribe(channel)
    
    async def unsubscribe(self, channel: str):
        """Unsubscribe from channel"""
        if self.pubsub:
            await self.pubsub.unsubscribe(channel)
    
    async def get_message(self):
        """Get message from subscribed channels"""
        if self.pubsub:
            message = await self.pubsub.get_message(ignore_subscribe_messages=True)
            if message and message["data"]:
                return json.loads(message["data"])
        return None
    
    async def set_user_online(self, user_id: str):
        """Set user online status"""
        if self.client:
            await self.client.setex(f"user_online:{user_id}", 300, "true")  # 5 min expiry
    
    async def set_user_offline(self, user_id: str):
        """Set user offline"""
        if self.client:
            await self.client.delete(f"user_online:{user_id}")
    
    async def is_user_online(self, user_id: str) -> bool:
        """Check if user is online"""
        if self.client:
            result = await self.client.get(f"user_online:{user_id}")
            return result is not None
        return False

# Global Redis client instance
redis_client = RedisClient()
