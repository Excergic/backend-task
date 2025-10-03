from typing import Annotated
from fastapi import APIRouter, Depends, Query
from uuid import UUID
import asyncpg

from app.database import get_db
from app.api.deps import get_current_user_id
from app.models.schemas import UserStatsResponse
from app.services.story_service import StoryService


router = APIRouter(prefix="/me", tags=["User"])


@router.get("/stats", response_model=UserStatsResponse)
async def get_user_stats(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    pool: Annotated[asyncpg.Pool, Depends(get_db)],
    days: int = Query(7, ge=1, le=30, description="Number of days to look back")
):
    """
    Get user's story statistics
    
    Returns:
    - posted_count: Number of stories posted
    - total_views: Total view count across all stories
    - unique_viewers: Number of unique users who viewed
    - reactions: Breakdown by emoji type
    
    Default: Last 7 days
    """
    stats = await StoryService.get_user_stats(
        pool=pool,
        user_id=user_id,
        days=days
    )
    
    return UserStatsResponse(**stats)
