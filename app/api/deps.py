## JWT dependencies (get_current_user)

from typing import Annotated
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import asyncpg

from app.database import get_db
from app.core.security import decode_token
from app.repositories.user_repo import UserRepository


# HTTP Bearer scheme for extracting JWT from Authorization header
security = HTTPBearer()


async def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> UUID:
    """
    Extract and validate JWT token, return user ID
    
    This dependency can be used on any protected route
    """
    token = credentials.credentials
    user_id_str = decode_token(token)
    
    try:
        return UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token"
        )


async def get_current_user(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    pool: Annotated[asyncpg.Pool, Depends(get_db)]
) -> dict:
    """
    Get full current user data from database
    
    Use this when you need complete user information
    """
    user = await UserRepository.get_user_by_id(pool, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user
