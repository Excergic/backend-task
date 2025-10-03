from typing import Optional, List
from uuid import UUID
from datetime import datetime, timedelta
import asyncpg

from app.config import settings


class StoryRepository:
    """Database operations for stories"""
    
    @staticmethod
    async def create_story(
        pool: asyncpg.Pool,
        author_id: UUID,
        text: Optional[str],
        media_key: Optional[str],
        visibility: str
    ) -> dict:
        """Create new story with auto-expiration"""
        expires_at = datetime.utcnow() + timedelta(hours=settings.STORY_EXPIRATION_HOURS)
        
        query = """
            INSERT INTO stories (author_id, text, media_key, visibility, expires_at)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, author_id, text, media_key, visibility, created_at, expires_at
        """
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(query, author_id, text, media_key, visibility, expires_at)
            return dict(row)
    
    @staticmethod
    async def get_story_by_id(
        pool: asyncpg.Pool,
        story_id: UUID
    ) -> Optional[dict]:
        """Get story by ID with author info and counts"""
        query = """
            SELECT 
                s.id, s.author_id, s.text, s.media_key, s.visibility, 
                s.created_at, s.expires_at, s.deleted_at,
                u.email as author_email,
                COUNT(DISTINCT sv.viewer_id) as view_count,
                COUNT(DISTINCT r.id) as reaction_count
            FROM stories s
            JOIN users u ON s.author_id = u.id
            LEFT JOIN story_views sv ON s.id = sv.story_id
            LEFT JOIN reactions r ON s.id = r.story_id
            WHERE s.id = $1 AND s.deleted_at IS NULL AND s.expires_at > NOW()
            GROUP BY s.id, u.email
        """
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(query, story_id)
            return dict(row) if row else None
    
    @staticmethod
    async def get_feed(
        pool: asyncpg.Pool,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0
    ) -> List[dict]:
        """Get feed: public stories + stories from users I follow + my own stories"""
        query = """
            SELECT DISTINCT
                s.id, s.author_id, s.text, s.media_key, s.visibility,
                s.created_at, s.expires_at,
                u.email as author_email,
                COUNT(DISTINCT sv.viewer_id) as view_count,
                COUNT(DISTINCT r.id) as reaction_count
            FROM stories s
            JOIN users u ON s.author_id = u.id
            LEFT JOIN story_views sv ON s.id = sv.story_id
            LEFT JOIN reactions r ON s.id = r.story_id
            WHERE s.deleted_at IS NULL 
              AND s.expires_at > NOW()
              AND (
                s.visibility = 'public'
                OR (s.visibility = 'friends' AND s.author_id IN (
                    SELECT followee_id FROM follows WHERE follower_id = $1
                ))
                OR s.author_id = $1
              )
            GROUP BY s.id, u.email
            ORDER BY s.created_at DESC
            LIMIT $2 OFFSET $3
        """
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, user_id, limit, offset)
            return [dict(row) for row in rows]
    
    @staticmethod
    async def add_view(
        pool: asyncpg.Pool,
        story_id: UUID,
        viewer_id: UUID
    ) -> dict:
        """Add view record (idempotent - insert or get existing)"""
        query = """
            INSERT INTO story_views (story_id, viewer_id)
            VALUES ($1, $2)
            ON CONFLICT (story_id, viewer_id) DO NOTHING
            RETURNING story_id, viewer_id, viewed_at
        """
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(query, story_id, viewer_id)
            
            if row:
                return {"is_new_view": True, **dict(row)}
            
            # Already viewed, get existing record
            existing = await conn.fetchrow(
                "SELECT story_id, viewer_id, viewed_at FROM story_views WHERE story_id = $1 AND viewer_id = $2",
                story_id, viewer_id
            )
            return {"is_new_view": False, **dict(existing)}
    
    @staticmethod
    async def add_reaction(
        pool: asyncpg.Pool,
        story_id: UUID,
        user_id: UUID,
        emoji: str
    ) -> dict:
        """Add reaction to story (idempotent)"""
        query = """
            INSERT INTO reactions (story_id, user_id, emoji)
            VALUES ($1, $2, $3)
            ON CONFLICT (story_id, user_id, emoji) DO NOTHING
            RETURNING id, story_id, user_id, emoji, created_at
        """
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(query, story_id, user_id, emoji)
            
            if row:
                return dict(row)
            
            # Already reacted, get existing
            existing = await conn.fetchrow(
                "SELECT id, story_id, user_id, emoji, created_at FROM reactions WHERE story_id = $1 AND user_id = $2 AND emoji = $3",
                story_id, user_id, emoji
            )
            return dict(existing)
    
    @staticmethod
    async def get_user_stats(
        pool: asyncpg.Pool,
        user_id: UUID,
        days: int = 7
    ) -> dict:
        """Get user's story statistics for last N days"""
        query = f"""
            WITH user_stories AS (
                SELECT id FROM stories 
                WHERE author_id = $1 
                  AND created_at > NOW() - INTERVAL '{days} days'
                  AND deleted_at IS NULL
            )
            SELECT
                COUNT(DISTINCT s.id) as posted_count,
                COUNT(DISTINCT sv.viewer_id) as unique_viewers,
                COUNT(sv.viewer_id) as total_views
            FROM user_stories s
            LEFT JOIN story_views sv ON s.id = sv.story_id
        """
        
        reactions_query = f"""
            SELECT r.emoji, COUNT(*) as count
            FROM reactions r
            JOIN stories s ON r.story_id = s.id
            WHERE s.author_id = $1
              AND s.created_at > NOW() - INTERVAL '{days} days'
              AND s.deleted_at IS NULL
            GROUP BY r.emoji
        """
        
        async with pool.acquire() as conn:
            stats = await conn.fetchrow(query, user_id)
            reactions = await conn.fetch(reactions_query, user_id)
            
            return {
                "posted_count": stats["posted_count"] or 0,
                "total_views": stats["total_views"] or 0,
                "unique_viewers": stats["unique_viewers"] or 0,
                "reactions": {row["emoji"]: row["count"] for row in reactions}
            }
    
    @staticmethod
    async def add_story_audience(
        pool: asyncpg.Pool,
        story_id: UUID,
        user_ids: List[UUID]
    ):
        """Add custom audience for friends-only story"""
        query = """
            INSERT INTO story_audience (story_id, user_id)
            VALUES ($1, $2)
            ON CONFLICT DO NOTHING
        """
        
        async with pool.acquire() as conn:
            await conn.executemany(query, [(story_id, uid) for uid in user_ids])

    @staticmethod
    async def get_feed_optimized(
        pool: asyncpg.Pool,
        user_id: UUID,
        followee_ids: List[UUID],
        limit: int = 20,
        offset: int = 0
    ) -> List[dict]:

        """
        Optimized feed query with N+1 prevention
    
        Preloads:
        - Author information (email)
        - View counts (aggregated)
        - Reaction counts (aggregated)
    
        Uses followee_ids from cache to avoid subquery
        """
        # Build followee_ids parameter for SQL IN clause
        # If user doesn't follow anyone, only show public stories and own stories

        if followee_ids:
            followee_placeholders = ",".join([f"${i+2}" for i in range(len(followee_ids))])

            query = f"""
                SELECT
                    s.id,
                    s.author_id,
                    s.text,
                    s.media_key,
                    s.visibility,
                    s.created_at,
                    s.expires_at,
                    u.email as author_email,
                    COALESCE(COUNT(DISTINCT sv.viewer_id), 0) as view_count,
                    COALESCE(COUNT(DISTINCT r.id), 0) as reaction_count
                FROM stories s
                INNER JOIN users u ON s.author_id = u.id
                LEFT JOIN story_views sv ON s.id = sv.story_id
                LEFT JOIN reactions r ON s.id = r.story_id
                WHERE s.deleted_at IS NULL
                  AND s.expires_at > NOW()
                  AND (
                    s.visibility = 'public'
                    OR (s.visibility = 'friends' AND s.author_id IN ({followee_placeholders}))
                    OR s.author_id = $1
              )
              GROUP BY s.id, u.email
              ORDER BY s.created_at DESC
              LIMIT ${len(followee_ids) + 2} OFFSET ${len(followee_ids) + 3}
            """
            params = [user_id] + followee_ids + [limit, offset]
            
        else:
            query = """
            SELECT 
                s.id, 
                s.author_id, 
                s.text, 
                s.media_key, 
                s.visibility,
                s.created_at, 
                s.expires_at,
                u.email as author_email,
                COALESCE(COUNT(DISTINCT sv.viewer_id), 0) as view_count,
                COALESCE(COUNT(DISTINCT r.id), 0) as reaction_count
            FROM stories s
            INNER JOIN users u ON s.author_id = u.id
            LEFT JOIN story_views sv ON s.id = sv.story_id
            LEFT JOIN reactions r ON s.id = r.story_id
            WHERE s.deleted_at IS NULL 
              AND s.expires_at > NOW()
              AND (s.visibility = 'public' OR s.author_id = $1)
            GROUP BY s.id, u.email
            ORDER BY s.created_at DESC
            LIMIT $2 OFFSET $3
        """
        
        params = [user_id, limit, offset]
    
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]

