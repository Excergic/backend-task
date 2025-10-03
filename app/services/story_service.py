# app/services/story_service.py
from typing import Optional, List
from uuid import UUID
from datetime import datetime
import asyncpg
from fastapi import HTTPException, status

from app.repositories.story_repo import StoryRepository
from app.repositories.follow_repo import FollowRepository
from app.core.websocket_manager import manager
from app.services.cache_service import cache_service


class StoryService:
    """Stories business logic"""
    
    @staticmethod
    async def create_story(
        pool: asyncpg.Pool,
        author_id: UUID,
        text: Optional[str],
        media_key: Optional[str],
        visibility: str,
        audience_user_ids: Optional[List[UUID]] = None
    ) -> dict:
        """Create new story and invalidate relevant caches"""
        # Validate: must have text or media
        if not text and not media_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Story must have text or media"
            )
        
        # Create story
        story = await StoryRepository.create_story(
            pool=pool,
            author_id=author_id,
            text=text,
            media_key=media_key,
            visibility=visibility
        )
        
        # If custom audience specified for friends-only story
        if visibility == "friends" and audience_user_ids:
            await StoryRepository.add_story_audience(
                pool=pool,
                story_id=story["id"],
                user_ids=audience_user_ids
            )
        
        # Invalidate author's feed cache
        await cache_service.invalidate_user_feed(author_id)
        
        return story
    
    @staticmethod
    async def get_story(
        pool: asyncpg.Pool,
        story_id: UUID,
        viewer_id: UUID
    ) -> Optional[dict]:
        """
        Get story with permission checks
        
        Rules:
        - Public: Anyone can view
        - Friends: Only followers can view (or author)
        - Private: Only author can view
        """
        # Get story
        story = await StoryRepository.get_story_by_id(pool, story_id)
        
        if not story:
            return None
        
        # Check permissions
        author_id = story["author_id"]
        visibility = story["visibility"]
        
        # Author can always view their own story
        if viewer_id == author_id:
            return story
        
        # Public stories: anyone can view
        if visibility == "public":
            return story
        
        # Private stories: only author
        if visibility == "private":
            return None
        
        # Friends stories: check if viewer follows author
        if visibility == "friends":
            is_following = await FollowRepository.is_following(
                pool=pool,
                follower_id=viewer_id,
                followee_id=author_id
            )
            
            if is_following:
                return story
            else:
                return None
        
        return None
    
    @staticmethod
    async def get_feed(
        pool: asyncpg.Pool,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0
    ) -> List[dict]:
        """
        Get feed with caching optimization
        
        Cache layers:
        1. Cache user's followee IDs (5 min)
        2. Cache feed results (60 sec)
        3. Use optimized query to prevent N+1
        """
    # Try to get cached feed first
        cached_feed = await cache_service.get_user_feed(user_id, limit, offset)
        if cached_feed:
            print(f"Cache hit: Feed for user {user_id}")
            return cached_feed
        
        print(f"Cache miss: Feed for user {user_id}")
        
        # Try to get cached followee IDs
        followee_ids_str = await cache_service.get_user_followees(user_id)
        
        if followee_ids_str:
            print(f"Cache hit: Followees for user {user_id}")
            followee_ids = [UUID(fid) for fid in followee_ids_str]
        else:
            print(f"Cache miss: Followees for user {user_id}")
            # Get followee IDs from database
            followee_ids = await FollowRepository.get_followee_ids(pool, user_id)
            
            # Cache followee IDs
            await cache_service.set_user_followees(user_id, followee_ids)
        
        # Get feed using optimized query with preloaded followee IDs
        stories = await StoryRepository.get_feed_optimized(
            pool=pool,
            user_id=user_id,
            followee_ids=followee_ids,
            limit=limit,
            offset=offset
        )
    
        # Cache the feed
        await cache_service.set_user_feed(user_id, limit, offset, stories)
    
        return stories
    
    @staticmethod
    async def record_view(
        pool: asyncpg.Pool,
        story_id: UUID,
        viewer_id: UUID
    ) -> dict:
        """
        Record story view (idempotent)
        
        Returns is_new_view: true/false
        Emits real-time event to story author
        """
        # Check if story exists
        story = await StoryRepository.get_story_by_id(pool, story_id)
        
        if not story:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Story not found"
            )
        
        # Record view
        view = await StoryRepository.add_view(
            pool=pool,
            story_id=story_id,
            viewer_id=viewer_id
        )
        
        # Emit real-time event to story author (if new view)
        if view["is_new_view"]:
            author_id = story["author_id"]
            
            # Don't notify if viewing own story
            if author_id != viewer_id:
                await manager.send_to_user(
                    user_id=author_id,
                    message={
                        "event": "story.viewed",
                        "data": {
                            "story_id": str(story_id),
                            "viewer_id": str(viewer_id),
                            "viewed_at": view["viewed_at"].isoformat()
                        },
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
        
        return view
    
    @staticmethod
    async def add_reaction(
        pool: asyncpg.Pool,
        story_id: UUID,
        user_id: UUID,
        emoji: str
    ) -> dict:
        """
        Add reaction to story
        
        Emits real-time event to story author
        """
        # Check if story exists
        story = await StoryRepository.get_story_by_id(pool, story_id)
        
        if not story:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Story not found"
            )
        
        # Add reaction
        reaction = await StoryRepository.add_reaction(
            pool=pool,
            story_id=story_id,
            user_id=user_id,
            emoji=emoji
        )
        
        # Emit real-time event to story author
        author_id = story["author_id"]
        
        # Don't notify if reacting to own story
        if author_id != user_id:
            await manager.send_to_user(
                user_id=author_id,
                message={
                    "event": "story.reacted",
                    "data": {
                        "story_id": str(story_id),
                        "user_id": str(user_id),
                        "emoji": emoji,
                        "reaction_id": str(reaction["id"]),
                        "created_at": reaction["created_at"].isoformat()
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        return reaction
    
    @staticmethod
    async def delete_story(
        pool: asyncpg.Pool,
        story_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Delete story (soft delete)
        
        Only author can delete their own story
        """
        # Get story
        story = await StoryRepository.get_story_by_id(pool, story_id)
        
        if not story:
            return False
        
        # Check ownership
        if story["author_id"] != user_id:
            return False
        
        # Soft delete
        query = """
            UPDATE stories
            SET deleted_at = NOW()
            WHERE id = $1 AND deleted_at IS NULL
        """
        
        async with pool.acquire() as conn:
            result = await conn.execute(query, story_id)
            return result.split()[-1] != "0"
    
    @staticmethod
    async def get_user_stats(
        pool: asyncpg.Pool,
        user_id: UUID,
        days: int = 7
    ) -> dict:
        """Get user's story statistics"""
        stats = await StoryRepository.get_user_stats(
            pool=pool,
            user_id=user_id,
            days=days
        )
        
        return stats
