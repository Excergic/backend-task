# tests/unit/test_auth_service.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

from app.services.auth_service import AuthService
from fastapi import HTTPException


@pytest.mark.unit
class TestAuthService:
    """Unit tests for authentication service"""
    
    @pytest.mark.asyncio
    async def test_signup_success(self):
        """Test successful user signup"""
        mock_pool = AsyncMock()
        
        test_user = {
            "id": uuid4(),
            "email": "test@example.com",
            "created_at": "2025-10-03T12:00:00"
        }
        
        with patch('app.services.auth_service.UserRepository') as mock_user_repo, \
             patch('app.services.auth_service.structured_logger') as mock_logger, \
             patch('app.services.auth_service.auth_attempts_total') as mock_metric:
            
            # Mock: user doesn't exist (return async mock)
            mock_user_repo.get_user_by_email = AsyncMock(return_value=None)
            # Mock: user created successfully (return async mock)
            mock_user_repo.create_user = AsyncMock(return_value=test_user)
            
            result = await AuthService.signup(
                mock_pool,
                "test@example.com",
                "password123"
            )
            
            assert "user" in result
            assert "access_token" in result
            assert result["user"]["email"] == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_signup_duplicate_email(self):
        """Test signup with existing email"""
        mock_pool = AsyncMock()
        
        with patch('app.services.auth_service.UserRepository') as mock_user_repo, \
             patch('app.services.auth_service.structured_logger') as mock_logger, \
             patch('app.services.auth_service.auth_attempts_total') as mock_metric:
            
            # Mock: user already exists (return async mock)
            mock_user_repo.get_user_by_email = AsyncMock(return_value={"id": uuid4()})
            
            with pytest.raises(HTTPException) as exc_info:
                await AuthService.signup(
                    mock_pool,
                    "existing@example.com",
                    "password123"
                )
            
            assert exc_info.value.status_code == 400
            assert "already registered" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_login_success(self):
        """Test successful login"""
        mock_pool = AsyncMock()
        
        test_user = {
            "id": uuid4(),
            "email": "test@example.com",
            "password_hash": "$2b$12$KIXxJ5Wk5vZ9Yj0qZ5QZ5e.8Z5QZ5e.8Z5QZ5e.8Z5QZ5e",
            "created_at": "2025-10-03T12:00:00"
        }
        
        with patch('app.services.auth_service.UserRepository') as mock_user_repo, \
             patch('app.services.auth_service.verify_password') as mock_verify, \
             patch('app.services.auth_service.structured_logger') as mock_logger, \
             patch('app.services.auth_service.auth_attempts_total') as mock_metric:
            
            mock_user_repo.get_user_by_email = AsyncMock(return_value=test_user)
            mock_verify.return_value = True
            
            result = await AuthService.login(
                mock_pool,
                "test@example.com",
                "password123"
            )
            
            assert "user" in result
            assert "access_token" in result
            assert "password_hash" not in result["user"]
    
    @pytest.mark.asyncio
    async def test_login_invalid_password(self):
        """Test login with wrong password"""
        mock_pool = AsyncMock()
        
        test_user = {
            "id": uuid4(),
            "email": "test@example.com",
            "password_hash": "hashed_password"
        }
        
        with patch('app.services.auth_service.UserRepository') as mock_user_repo, \
             patch('app.services.auth_service.verify_password') as mock_verify, \
             patch('app.services.auth_service.structured_logger') as mock_logger, \
             patch('app.services.auth_service.auth_attempts_total') as mock_metric:
            
            mock_user_repo.get_user_by_email = AsyncMock(return_value=test_user)
            mock_verify.return_value = False
            
            with pytest.raises(HTTPException) as exc_info:
                await AuthService.login(
                    mock_pool,
                    "test@example.com",
                    "wrongpassword"
                )
            
            assert exc_info.value.status_code == 401
