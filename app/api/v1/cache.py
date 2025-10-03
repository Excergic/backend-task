from typing import Annotated
from fastapi import APIRouter, Depends
from uuid import UUID

from app.api.deps import get_current_user_id
from app.services.cache_service import cache_service
from app.core.redis_client import redis_client


router = APIRouter(prefix="/cache", tags=["Cache Management"])


@router.get("/stats")
async def get_cache_stats(
    user_id: Annotated[UUID, Depends(get_current_user_id)]
):
    """
    Get cache statistics
    
    Shows cache status for current user
    """
    # Check if user's data is cached
    followees_cached = await cache_service.get_user_followees(user_id) is not None
    feed_cached = await cache_service.get_user_feed(user_id, 20, 0) is not None
    
    # Get Redis info
    info = await redis_client.redis.info("stats")
    
    return {
        "user_cache": {
            "user_id": str(user_id),
            "followees_cached": followees_cached,
            "feed_cached": feed_cached
        },
        "redis_stats": {
            "total_connections": info.get("total_connections_received", 0),
            "total_commands": info.get("total_commands_processed", 0),
            "keyspace_hits": info.get("keyspace_hits", 0),
            "keyspace_misses": info.get("keyspace_misses", 0),
            "hit_rate": round(
                info.get("keyspace_hits", 0) / 
                max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1) * 100, 
                2
            )
        },
        "cache_ttls": {
            "followees": f"{cache_service.FOLLOWEES_TTL}s",
            "feed": f"{cache_service.FEED_TTL}s"
        }
    }


@router.delete("/clear")
async def clear_user_cache(
    user_id: Annotated[UUID, Depends(get_current_user_id)]
):
    """
    Clear all cache for current user
    
    Useful for testing or troubleshooting
    """
    await cache_service.invalidate_user_followees(user_id)
    await cache_service.invalidate_user_feed(user_id)
    
    return {
        "message": "Cache cleared successfully",
        "user_id": str(user_id)
    }
