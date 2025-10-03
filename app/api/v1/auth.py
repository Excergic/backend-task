from typing import Annotated
from fastapi import APIRouter, Depends, status
import asyncpg

from app.database import get_db
from app.api.deps import get_current_user
from app.models.schemas import UserSignupRequest, UserLoginRequest, TokenResponse, UserResponse
from app.services.auth_service import AuthService


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    data: UserSignupRequest,
    pool: Annotated[asyncpg.Pool, Depends(get_db)]
):
    """
    Register new user account
    
    - **email**: Valid email address
    - **password**: Minimum 8 characters
    """
    result = await AuthService.signup(pool, data.email, data.password)
    return TokenResponse(access_token=result["access_token"])


@router.post("/login", response_model=TokenResponse)
async def login(
    data: UserLoginRequest,
    pool: Annotated[asyncpg.Pool, Depends(get_db)]
):
    """
    Login with email and password
    
    Returns JWT token for authenticated requests
    """
    result = await AuthService.login(pool, data.email, data.password)
    return TokenResponse(access_token=result["access_token"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    user: Annotated[dict, Depends(get_current_user)]
):
    """
    Get current authenticated user information
    
    Requires valid JWT token in Authorization header
    """
    return UserResponse(**user)
