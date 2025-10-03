# tests/conftest.py
import pytest
import asyncio
import asyncpg
from httpx import AsyncClient, ASGITransport
from uuid import uuid4
from typing import AsyncGenerator
from unittest.mock import Mock, patch

from app.config import settings


# Mock MinIO before importing app
@pytest.fixture(scope="session", autouse=True)
def mock_minio():
    """Mock MinIO storage for all tests"""
    with patch('app.services.storage_service.MinIOStorageService') as mock:
        mock_instance = Mock()
        mock_instance.minio_client = Mock()
        mock.return_value = mock_instance
        yield mock


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
    try:
        pool = await asyncpg.create_pool(
            settings.DATABASE_URL,
            min_size=2,
            max_size=5
        )
        yield pool
        await pool.close()
    except Exception as e:
        pytest.skip(f"Database not available: {e}")


@pytest.fixture
async def test_client() -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client"""
    # Delay import to allow mocking
    from app.main import app
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
async def test_user(test_db_pool):
    """Create a test user"""
    if test_db_pool is None:
        pytest.skip("Database not available")
    
    from app.services.auth_service import AuthService
    
    email = f"test_{uuid4()}@example.com"
    password = "testpassword123"
    
    try:
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
    except Exception as e:
        pytest.skip(f"Could not create test user: {e}")


@pytest.fixture
async def auth_headers(test_user):
    """Create authorization headers"""
    return {"Authorization": f"Bearer {test_user['token']}"}


@pytest.fixture
async def cleanup_redis():
    """Cleanup Redis after tests"""
    yield
    try:
        from app.core.redis_client import redis_client
        await redis_client.redis.flushdb()
    except:
        pass
