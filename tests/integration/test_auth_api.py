# tests/integration/test_auth_api.py
import pytest
from uuid import uuid4


@pytest.mark.integration
class TestAuthAPI:
    """Integration tests for authentication endpoints"""
    
    @pytest.mark.asyncio
    async def test_signup_flow(self, test_client):
        """Test complete signup flow"""
        email = f"integration_{uuid4()}@example.com"
        
        response = await test_client.post(
            "/api/v1/auth/signup",
            json={
                "email": email,
                "password": "testpassword123"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_signup_duplicate_email(self, test_client, test_user):
        """Test signup with existing email"""
        response = await test_client.post(
            "/api/v1/auth/signup",
            json={
                "email": test_user["email"],
                "password": "password123"
            }
        )
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_login_success(self, test_client, test_user):
        """Test successful login"""
        response = await test_client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
    
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, test_client, test_user):
        """Test login with wrong password"""
        response = await test_client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user["email"],
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_current_user(self, test_client, auth_headers):
        """Test getting current user info"""
        response = await test_client.get(
            "/api/v1/auth/me",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "email" in data
        assert "password" not in data
