# app/api/v1/stories.py
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from uuid import UUID
import asyncpg

from app.database import get_db
from app.api.deps import get_current_user_id
from app.api.rate_limit_deps import rate_limit_stories, rate_limit_reactions, rate_limit_views
from app.models.schemas import (
    CreateStoryRequest,
    StoryResponse,
    ViewStoryResponse,
    ReactionRequest,
    ReactionResponse,
    UserStatsResponse
)
from app.services.story_service import StoryService
from app.core.idempotency import idempotency_handler


router = APIRouter(prefix="/stories", tags=["Stories"])


@router.post(
    "",
    response_model=StoryResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit_stories)]  # Add rate limiting
)
async def create_story(
    data: CreateStoryRequest,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    pool: Annotated[asyncpg.Pool, Depends(get_db)],
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
):
    """
    Create new story
    
    **Rate Limit:** 20 requests per minute per user
    
    **Idempotency:**
    - Provide `Idempotency-Key` header to prevent duplicate stories
    - Same key within 24h returns cached response
    
    **Body:**
    - **text**: Optional story text (max 500 chars)
    - **media_key**: Optional media from upload endpoint
    - **visibility**: public, friends, or private
    - **audience_user_ids**: Optional custom audience
    
    Story expires after 24 hours automatically
    """
    # Check idempotency
    if idempotency_key:
        cached = await idempotency_handler.get_cached_response(idempotency_key, user_id)
        if cached:
            return StoryResponse(**cached)
    
    # Create story
    story = await StoryService.create_story(
        pool=pool,
        author_id=user_id,
        text=data.text,
        media_key=data.media_key,
        visibility=data.visibility,
        audience_user_ids=data.audience_user_ids
    )
    
    # Cache response for idempotency
    if idempotency_key:
        await idempotency_handler.cache_response(
            idempotency_key=idempotency_key,
            user_id=user_id,
            response=story
        )
    
    return StoryResponse(**story)


@router.get("/{story_id}", response_model=StoryResponse)
async def get_story(
    story_id: UUID,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    pool: Annotated[asyncpg.Pool, Depends(get_db)]
):
    """
    Get story by ID
    
    Permission rules:
    - Public: Anyone can view
    - Friends: Only followers can view
    - Private: Only author can view
    """
    story = await StoryService.get_story(
        pool=pool,
        story_id=story_id,
        viewer_id=user_id
    )
    
    if not story:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Story not found or you don't have permission to view it"
        )
    
    return StoryResponse(**story)


@router.get("", response_model=list[StoryResponse])
async def get_feed(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    pool: Annotated[asyncpg.Pool, Depends(get_db)],
    limit: int = Query(20, ge=1, le=100, description="Number of stories to return"),
    offset: int = Query(0, ge=0, description="Number of stories to skip")
):
    """
    Get feed of active stories
    
    Returns:
    - Public stories from all users
    - Friends-only stories from users you follow
    - Your own stories (all visibilities)
    
    Ordered by newest first, only active (not expired, not deleted)
    """
    stories = await StoryService.get_feed(
        pool=pool,
        user_id=user_id,
        limit=limit,
        offset=offset
    )
    
    return [StoryResponse(**story) for story in stories]


@router.post(
    "/{story_id}/view",
    response_model=ViewStoryResponse,
    dependencies=[Depends(rate_limit_views)]  # Add rate limiting
)
async def view_story(
    story_id: UUID,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    pool: Annotated[asyncpg.Pool, Depends(get_db)]
):
    """
    Record story view (idempotent)
    
    **Rate Limit:** 100 requests per minute per user
    
    - First view: Creates new view record
    - Subsequent views: Returns existing view record
    - is_new_view: true if first time, false if already viewed
    """
    view = await StoryService.record_view(
        pool=pool,
        story_id=story_id,
        viewer_id=user_id
    )
    
    return ViewStoryResponse(**view)


@router.post(
    "/{story_id}/reactions",
    response_model=ReactionResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit_reactions)]  # Add rate limiting
)
async def add_reaction(
    story_id: UUID,
    data: ReactionRequest,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    pool: Annotated[asyncpg.Pool, Depends(get_db)]
):
    """
    Add reaction to story
    
    **Rate Limit:** 60 requests per minute per user
    
    Supported emojis: 👍 ❤️ 😂 😮 😢 🔥
    
    Idempotent: Same user + same emoji = returns existing reaction
    """
    reaction = await StoryService.add_reaction(
        pool=pool,
        story_id=story_id,
        user_id=user_id,
        emoji=data.emoji
    )
    
    return ReactionResponse(**reaction)


@router.delete("/{story_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_story(
    story_id: UUID,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    pool: Annotated[asyncpg.Pool, Depends(get_db)]
):
    """
    Delete story (soft delete)
    
    Only the author can delete their own story
    """
    deleted = await StoryService.delete_story(
        pool=pool,
        story_id=story_id,
        user_id=user_id
    )
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Story not found or you don't have permission to delete it"
        )
    
    return None
