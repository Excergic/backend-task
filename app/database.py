import asyncpg
from app.config import settings


class Database:
    """Database connection manager with connection pooling"""
    
    def __init__(self):
        self.pool: asyncpg.Pool | None = None
    
    async def connect(self):
        """Initialize connection pool"""
        self.pool = await asyncpg.create_pool(
            settings.DATABASE_URL,
            min_size=settings.DB_POOL_MIN_SIZE,
            max_size=settings.DB_POOL_MAX_SIZE,
            max_inactive_connection_lifetime=300,
            command_timeout=60
        )
        print("Database pool connected")
    
    async def disconnect(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            print("Database pool closed")
    
    async def execute_migration(self, sql: str):
        """Execute migration SQL"""
        async with self.pool.acquire() as conn:
            await conn.execute(sql)


# Global database instance
db = Database()


# Dependency for FastAPI routes
async def get_db() -> asyncpg.Pool:
    """Dependency to get database pool"""
    return db.pool
