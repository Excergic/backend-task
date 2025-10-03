import asyncpg
from fastapi import HTTPException, status

from app.core.security import hash_password, verify_password, create_access_token
from app.repositories.user_repo import UserRepository


class AuthService:
    """Authentication business logic"""
    
    @staticmethod
    async def signup(pool: asyncpg.Pool, email: str, password: str) -> dict:
        """
        Register new user
        
        Returns:
            dict with user data and access token
        """
        # Check if user already exists
        existing_user = await UserRepository.get_user_by_email(pool, email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash password
        password_hash = hash_password(password)
        
        # Create user
        user = await UserRepository.create_user(pool, email, password_hash)
        
        # Generate JWT token
        access_token = create_access_token(str(user["id"]))
        
        return {
            "user": user,
            "access_token": access_token
        }
    
    @staticmethod
    async def login(pool: asyncpg.Pool, email: str, password: str) -> dict:
        """
        Login user
        
        Returns:
            dict with user data and access token
        """
        # Get user
        user = await UserRepository.get_user_by_email(pool, email)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password
        if not verify_password(password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Generate JWT token
        access_token = create_access_token(str(user["id"]))
        
        # Remove password_hash from response
        user.pop("password_hash")
        
        return {
            "user": user,
            "access_token": access_token
        }
