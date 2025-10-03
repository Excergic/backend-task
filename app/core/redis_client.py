import redis.asyncio as redis
from app.config import settings


class RedisClient:
    """Redis client for caching and rate limiting"""
    
    def __init__(self):
        self.redis: redis.Redis = None
    
    async def connect(self):
        """Initialize Redis connection"""
        self.redis = await redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        # Test connection
        await self.redis.ping()
        print("Redis connected")
    
    async def disconnect(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
            print("Redis disconnected")
    
    async def get(self, key: str) -> str:
        """Get value by key"""
        return await self.redis.get(key)
    
    async def set(self, key: str, value: str, ex: int = None):
        """Set key-value with optional expiration (seconds)"""
        await self.redis.set(key, value, ex=ex)
    
    async def delete(self, key: str):
        """Delete key"""
        await self.redis.delete(key)
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        return await self.redis.exists(key) > 0
    
    async def incr(self, key: str) -> int:
        """Increment counter"""
        return await self.redis.incr(key)
    
    async def expire(self, key: str, seconds: int):
        """Set expiration on key"""
        await self.redis.expire(key, seconds)


# Global Redis client instance
redis_client = RedisClient()
