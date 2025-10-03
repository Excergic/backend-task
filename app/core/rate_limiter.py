from typing import Optional
from uuid import UUID
from fastapi import HTTPException, status
from app.core.redis_client import redis_client


class RateLimiter:
    """Token bucket rate limiter using Redis"""
    
    @staticmethod
    async def check_rate_limit(
        user_id: UUID,
        endpoint: str,
        limit: int,
        window: int = 60
    ) -> dict:
        """
        Check rate limit using token bucket algorithm
        
        Args:
            user_id: User UUID
            endpoint: Endpoint identifier (e.g., "stories", "reactions")
            limit: Max requests per window
            window: Time window in seconds (default: 60)
        
        Returns:
            dict with limit info
        
        Raises:
            HTTPException: 429 if rate limit exceeded
        """
        key = f"ratelimit:{endpoint}:{user_id}"
        
        # Get current count
        current = await redis_client.get(key)
        
        if current is None:
            # First request in window
            await redis_client.set(key, "1", ex=window)
            return {
                "allowed": True,
                "limit": limit,
                "remaining": limit - 1,
                "reset_in": window
            }
        
        current_count = int(current)
        
        if current_count >= limit:
            # Rate limit exceeded
            ttl = await redis_client.redis.ttl(key)
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {ttl} seconds.",
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(ttl),
                    "Retry-After": str(ttl)
                }
            )
        
        # Increment counter
        new_count = await redis_client.incr(key)
        ttl = await redis_client.redis.ttl(key)
        
        return {
            "allowed": True,
            "limit": limit,
            "remaining": limit - new_count,
            "reset_in": ttl
        }


rate_limiter = RateLimiter()
