from typing import Optional
from uuid import UUID
from datetime import datetime
import json
from fastapi import HTTPException, status
from app.core.redis_client import redis_client

class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for UUID and datetime objects"""
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class IdempotencyHandler:
    """Handle idempotent requests using Redis"""
    
    @staticmethod
    async def get_cached_response(
        idempotency_key: str,
        user_id: UUID
    ) -> Optional[dict]:
        """
        Get cached response for idempotency key
        
        Returns:
            Cached response dict or None
        """
        key = f"idempotency:{user_id}:{idempotency_key}"
        
        cached = await redis_client.get(key)
        if cached:
            return json.loads(cached)
        
        return None
    
    @staticmethod
    async def cache_response(
        idempotency_key: str,
        user_id: UUID,
        response: dict,
        ttl: int = 86400  # 24 hours
    ):
        """
        Cache response for idempotency key
        
        Args:
            idempotency_key: Client-provided unique key
            user_id: User UUID
            response: Response data to cache
            ttl: Time to live in seconds (default: 24h)
        """
        key = f"idempotency:{user_id}:{idempotency_key}"
        
        await redis_client.set(
            key,
            json.dumps(response, cls=CustomJSONEncoder),
            ex=ttl
        )


idempotency_handler = IdempotencyHandler()
