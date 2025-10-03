# tests/conftest.py
import pytest
import asyncio
import asyncpg
from httpx import AsyncClient, ASGITransport
from uuid import uuid4
from typing import AsyncGenerator

from app.main import app
from app.config import settings
from app.database import db
from app.core.redis_client import redis_client


# Fixtures for async tests
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_db_pool():
    """Create test database connection pool"""
    pool = await asyncpg.create_pool(
        settings.DATABASE_URL,
        min_size=2,
        max_size=5
    )
    yield pool
    await pool.close()


@pytest.fixture
async def test_client() -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
async def test_user(test_db_pool):
    """Create a test user"""
    from app.services.auth_service import AuthService
    
    email = f"test_{uuid4()}@example.com"
    password = "testpassword123"
    
    result = await AuthService.signup(test_db_pool, email, password)
    
    yield {
        "id": result["user"]["id"],
        "email": email,
        "password": password,
        "token": result["access_token"]
    }
    
    # Cleanup
    async with test_db_pool.acquire() as conn:
        await conn.execute("DELETE FROM users WHERE email = $1", email)


@pytest.fixture
async def auth_headers(test_user):
    """Create authorization headers"""
    return {"Authorization": f"Bearer {test_user['token']}"}


@pytest.fixture
async def cleanup_redis():
    """Cleanup Redis after tests"""
    yield
    # Clean up test data
    await redis_client.redis.flushdb()
