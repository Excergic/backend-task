from typing import Annotated
from uuid import UUID
from fastapi import Depends
from app.api.deps import get_current_user_id
from app.core.rate_limiter import rate_limiter
from app.config import settings


async def rate_limit_stories(
    user_id: Annotated[UUID, Depends(get_current_user_id)]
):
    """Rate limit for POST /stories (20/min)"""
    await rate_limiter.check_rate_limit(
        user_id=user_id,
        endpoint="stories",
        limit=settings.RATE_LIMIT_STORIES,
        window=60
    )


async def rate_limit_reactions(
    user_id: Annotated[UUID, Depends(get_current_user_id)]
):
    """Rate limit for POST /reactions (60/min)"""
    await rate_limiter.check_rate_limit(
        user_id=user_id,
        endpoint="reactions",
        limit=settings.RATE_LIMIT_REACTIONS,
        window=60
    )


async def rate_limit_views(
    user_id: Annotated[UUID, Depends(get_current_user_id)]
):
    """Rate limit for POST /view (100/min)"""
    await rate_limiter.check_rate_limit(
        user_id=user_id,
        endpoint="views",
        limit=settings.RATE_LIMIT_VIEWS,
        window=60
    )


async def rate_limit_follow(
    user_id: Annotated[UUID, Depends(get_current_user_id)]
):
    """Rate limit for POST /follow (30/min)"""
    await rate_limiter.check_rate_limit(
        user_id=user_id,
        endpoint="follow",
        limit=settings.RATE_LIMIT_FOLLOW,
        window=60
    )
