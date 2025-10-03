from typing import Optional
import asyncpg
from uuid import UUID


class UserRepository:
    """Database operations for users"""
    
    @staticmethod
    async def create_user(
        pool: asyncpg.Pool,
        email: str,
        password_hash: str
    ) -> dict:
        """Create new user and return user data"""
        query = """
            INSERT INTO users (email, password_hash)
            VALUES ($1, $2)
            RETURNING id, email, created_at
        """
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(query, email, password_hash)
            return dict(row)
    
    @staticmethod
    async def get_user_by_email(
        pool: asyncpg.Pool,
        email: str
    ) -> Optional[dict]:
        """Get user by email"""
        query = """
            SELECT id, email, password_hash, created_at
            FROM users
            WHERE email = $1
        """
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(query, email)
            return dict(row) if row else None
    
    @staticmethod
    async def get_user_by_id(
        pool: asyncpg.Pool,
        user_id: UUID
    ) -> Optional[dict]:
        """Get user by ID"""
        query = """
            SELECT id, email, created_at
            FROM users
            WHERE id = $1
        """
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(query, user_id)
            return dict(row) if row else None
