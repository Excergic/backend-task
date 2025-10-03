from uuid import UUID
import asyncpg
from typing import List


class FollowRepository:
    """Database operations for follows (social graph)"""
    
    @staticmethod
    async def follow_user(
        pool: asyncpg.Pool,
        follower_id: UUID,
        followee_id: UUID
    ) -> dict:
        """Follow a user and invalidate followees cache"""
        query = """
            INSERT INTO follows (follower_id, followee_id)
            VALUES ($1, $2)
            ON CONFLICT (follower_id, followee_id) DO NOTHING
            RETURNING follower_id, followee_id, created_at
        """
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(query, follower_id, followee_id)
            
            # Import here to avoid circular dependency
            from app.services.cache_service import cache_service
            
            # Invalidate followees cache
            await cache_service.invalidate_user_followees(follower_id)
            # Invalidate feed cache
            await cache_service.invalidate_user_feed(follower_id)
            
            if row:
                return dict(row)
            
            existing = await conn.fetchrow(
                "SELECT follower_id, followee_id, created_at FROM follows WHERE follower_id = $1 AND followee_id = $2",
                follower_id, followee_id
            )
            return dict(existing)
    
    @staticmethod
    async def unfollow_user(
        pool: asyncpg.Pool,
        follower_id: UUID,
        followee_id: UUID
    ) -> bool:
        """Unfollow a user and invalidate followees cache"""
        query = """
            DELETE FROM follows
            WHERE follower_id = $1 AND followee_id = $2
        """
        
        async with pool.acquire() as conn:
            result = await conn.execute(query, follower_id, followee_id)
            
            # Import here to avoid circular dependency
            from app.services.cache_service import cache_service
            
            # Invalidate followees cache
            await cache_service.invalidate_user_followees(follower_id)
            # Invalidate feed cache
            await cache_service.invalidate_user_feed(follower_id)
            
            return result.split()[-1] != "0"
    
    @staticmethod
    async def is_following(
        pool: asyncpg.Pool,
        follower_id: UUID,
        followee_id: UUID
    ) -> bool:
        """
        Check if follower_id is following followee_id
        
        Returns:
            True if following, False otherwise
        """
        query = """
            SELECT EXISTS(
                SELECT 1 FROM follows 
                WHERE follower_id = $1 AND followee_id = $2
            )
        """
        
        async with pool.acquire() as conn:
            exists = await conn.fetchval(query, follower_id, followee_id)
            return exists
    
    @staticmethod
    async def get_followers(
        pool: asyncpg.Pool,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> list[dict]:
        """
        Get list of users following the specified user
        
        Returns list of follower user info
        """
        query = """
            SELECT u.id, u.email, u.created_at, f.created_at as followed_at
            FROM follows f
            JOIN users u ON f.follower_id = u.id
            WHERE f.followee_id = $1
            ORDER BY f.created_at DESC
            LIMIT $2 OFFSET $3
        """
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, user_id, limit, offset)
            return [dict(row) for row in rows]
    
    @staticmethod
    async def get_following(
        pool: asyncpg.Pool,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> list[dict]:
        """
        Get list of users that the specified user is following
        
        Returns list of followee user info
        """
        query = """
            SELECT u.id, u.email, u.created_at, f.created_at as followed_at
            FROM follows f
            JOIN users u ON f.followee_id = u.id
            WHERE f.follower_id = $1
            ORDER BY f.created_at DESC
            LIMIT $2 OFFSET $3
        """
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, user_id, limit, offset)
            return [dict(row) for row in rows]
    
    @staticmethod
    async def get_follower_count(
        pool: asyncpg.Pool,
        user_id: UUID
    ) -> int:
        """Get count of users following this user"""
        query = """
            SELECT COUNT(*) 
            FROM follows 
            WHERE followee_id = $1
        """
        
        async with pool.acquire() as conn:
            count = await conn.fetchval(query, user_id)
            return count
    
    @staticmethod
    async def get_following_count(
        pool: asyncpg.Pool,
        user_id: UUID
    ) -> int:
        """Get count of users this user is following"""
        query = """
            SELECT COUNT(*) 
            FROM follows 
            WHERE follower_id = $1
        """
        
        async with pool.acquire() as conn:
            count = await conn.fetchval(query, user_id)
            return count
    
    @staticmethod
    async def get_mutual_follows(
        pool: asyncpg.Pool,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> list[dict]:
        """
        Get mutual follows (users who follow each other)
        
        Returns list of users who both follow and are followed by user_id
        """
        query = """
            SELECT DISTINCT u.id, u.email, u.created_at
            FROM follows f1
            JOIN follows f2 ON f1.follower_id = f2.followee_id 
                           AND f1.followee_id = f2.follower_id
            JOIN users u ON f1.followee_id = u.id
            WHERE f1.follower_id = $1
            ORDER BY u.created_at DESC
            LIMIT $2 OFFSET $3
        """
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, user_id, limit, offset)
            return [dict(row) for row in rows]
    
    @staticmethod
    async def get_followee_ids(
        pool: asyncpg.Pool,
        user_id: UUID
    ) -> List[UUID]:
        """
        Get list of user ids that user_id follows

        Optimized query for caching
        """
        query = """
            SELECT followee_id
            FROM follows
            WHERE follower_id = $1
        """

        async with pool.acquire() as conn:
            rows = await conn.fetch(query, user_id)
            return [row["followee_id"] for row in rows]