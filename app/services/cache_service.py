from typing import Optional, List
from uuid import UUID
import json
from app.core.redis_client import redis_client
from datetime import datetime


class CacheService:
    """Redis caching for performance optimization"""
    
    # Cache TTLs (Time To Live)
    FOLLOWEES_TTL = 300  # 5 minutes
    FEED_TTL = 60  # 60 seconds for hot feed
    USER_TTL = 300  # 5 minutes
    
    @staticmethod
    async def get_user_followees(user_id: UUID) -> Optional[List[str]]:
        """
        Get cached list of users that user_id follows
        
        Returns:
            List of followee UUID strings or None if not cached
        """
        key = f"followees:{user_id}"
        cached = await redis_client.get(key)
        
        if cached:
            return json.loads(cached)
        
        return None
    
    @staticmethod
    async def set_user_followees(user_id: UUID, followee_ids: List[UUID]):
        """
        Cache list of users that user_id follows
        
        Args:
            user_id: User UUID
            followee_ids: List of followee UUIDs
        """
        key = f"followees:{user_id}"
        
        # Convert UUIDs to strings for JSON
        followee_strings = [str(fid) for fid in followee_ids]
        
        await redis_client.set(
            key,
            json.dumps(followee_strings),
            ex=CacheService.FOLLOWEES_TTL
        )
    
    @staticmethod
    async def invalidate_user_followees(user_id: UUID):
        """Invalidate followees cache when user follows/unfollows"""
        key = f"followees:{user_id}"
        await redis_client.delete(key)
    
    @staticmethod
    async def get_user_feed(user_id: UUID, limit: int, offset: int) -> Optional[List[dict]]:
        """
        Get cached feed for user
        
        Returns:
            List of story dicts or None if not cached
        """
        key = f"feed:{user_id}:{limit}:{offset}"
        cached = await redis_client.get(key)
        
        if cached:
            return json.loads(cached)
        
        return None
    
    @staticmethod
    async def set_user_feed(user_id: UUID, limit: int, offset: int, stories: List[dict]):
        """
        Cache user's feed
        
        Args:
            user_id: User UUID
            limit: Page size
            offset: Page offset
            stories: List of story dictionaries
        """
        key = f"feed:{user_id}:{limit}:{offset}"
        
        # Serialize with custom handling for UUID and datetime
        def serialize_value(obj):
            if isinstance(obj, UUID):
                return str(obj)
            if isinstance(obj, datetime):
                return obj.isoformat()
            return obj
        
        serialized_stories = []
        for story in stories:
            serialized_story = {
                key: serialize_value(value) 
                for key, value in story.items()
            }
            serialized_stories.append(serialized_story)
        
        await redis_client.set(
            key,
            json.dumps(serialized_stories),
            ex=CacheService.FEED_TTL
        )
    
    @staticmethod
    async def invalidate_user_feed(user_id: UUID):
        """
        Invalidate all feed cache entries for a user
        
        Called when user creates/deletes a story
        """
        # Delete all feed pages for this user
        pattern = f"feed:{user_id}:*"
        
        # Note: This is a simple implementation
        # In production, use Redis SCAN for large datasets
        keys = []
        cursor = 0
        
        # Scan for matching keys
        while True:
            cursor, partial_keys = await redis_client.redis.scan(
                cursor=cursor,
                match=pattern,
                count=100
            )
            keys.extend(partial_keys)
            
            if cursor == 0:
                break
        
        # Delete all matching keys
        if keys:
            await redis_client.redis.delete(*keys)
    
    @staticmethod
    async def invalidate_feeds_for_followees(author_id: UUID):
        """
        Invalidate feed cache for all users who follow the author
        
        Called when author creates a new story
        This ensures followers see the new story
        """
        # Get all users who follow this author
        # Note: This requires a query, but it's worth it for cache invalidation
        # In production, you might maintain a reverse index in Redis
        
        # For now, we'll use a simple pattern match
        # You could optimize this by maintaining follower lists in Redis
        pattern = f"feed:*"
        
        # In production, consider:
        # 1. Publishing to Redis pub/sub channel
        # 2. Background task to invalidate caches
        # 3. TTL-based expiration (which we already have)
        
        # For this implementation, we'll rely on TTL expiration
        # Feeds will naturally refresh within 60 seconds
        pass


cache_service = CacheService()
