# from typing import Annotated
# from fastapi import APIRouter, Depends, HTTPException, status
# from uuid import UUID
# import asyncpg

# from app.database import get_db
# from app.api.deps import get_current_user_id
# from app.models.schemas import FollowResponse
# from app.repositories.follow_repo import FollowRepository
# from app.repositories.user_repo import UserRepository


# router = APIRouter(prefix="/follow", tags=["Social"])


# @router.post("/{user_id}", response_model=FollowResponse, status_code=status.HTTP_201_CREATED)
# async def follow_user(
#     user_id: UUID,
#     current_user_id: Annotated[UUID, Depends(get_current_user_id)],
#     pool: Annotated[asyncpg.Pool, Depends(get_db)]
# ):
#     """
#     Follow a user
    
#     - Can't follow yourself
#     - Idempotent: Already following = returns existing record
#     """
#     # Can't follow yourself
#     if user_id == current_user_id:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="You cannot follow yourself"
#         )
    
#     # Check if user exists
#     target_user = await UserRepository.get_user_by_id(pool, user_id)
#     if not target_user:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="User not found"
#         )
    
#     # Follow user
#     follow = await FollowRepository.follow_user(
#         pool=pool,
#         follower_id=current_user_id,
#         followee_id=user_id
#     )
    
#     return FollowResponse(**follow)


# @router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
# async def unfollow_user(
#     user_id: UUID,
#     current_user_id: Annotated[UUID, Depends(get_current_user_id)],
#     pool: Annotated[asyncpg.Pool, Depends(get_db)]
# ):
#     """
#     Unfollow a user
    
#     Returns 204 even if not following (idempotent)
#     """
#     await FollowRepository.unfollow_user(
#         pool=pool,
#         follower_id=current_user_id,
#         followee_id=user_id
#     )
    
#     return None


# @router.get("/{user_id}/status")
# async def get_follow_status(
#     user_id: UUID,
#     current_user_id: Annotated[UUID, Depends(get_current_user_id)],
#     pool: Annotated[asyncpg.Pool, Depends(get_db)]
# ):
#     """
#     Check if current user is following target user
#     """
#     is_following = await FollowRepository.is_following(
#         pool=pool,
#         follower_id=current_user_id,
#         followee_id=user_id
#     )
    
#     return {
#         "user_id": user_id,
#         "is_following": is_following
#     }


from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
import asyncpg

from app.database import get_db
from app.api.deps import get_current_user_id
from app.api.rate_limit_deps import rate_limit_follow
from app.models.schemas import FollowResponse
from app.repositories.follow_repo import FollowRepository
from app.repositories.user_repo import UserRepository


router = APIRouter(prefix="/follow", tags=["Social"])


@router.post(
    "/{user_id}",
    response_model=FollowResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit_follow)]  # Add rate limiting
)
async def follow_user(
    user_id: UUID,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    pool: Annotated[asyncpg.Pool, Depends(get_db)]
):
    """
    Follow a user
    
    **Rate Limit:** 30 requests per minute per user
    
    **Design: One-Way Follow Model**
    - You follow them → You see their "friends" stories
    - Does NOT require them to follow you back
    - Idempotent: Already following returns existing record
    
    **Rules:**
    - Cannot follow yourself
    - User must exist
    """
    # Can't follow yourself
    if user_id == current_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot follow yourself"
        )
    
    # Check if user exists
    target_user = await UserRepository.get_user_by_id(pool, user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Follow user
    follow = await FollowRepository.follow_user(
        pool=pool,
        follower_id=current_user_id,
        followee_id=user_id
    )
    
    return FollowResponse(**follow)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unfollow_user(
    user_id: UUID,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    pool: Annotated[asyncpg.Pool, Depends(get_db)]
):
    """
    Unfollow a user
    
    **Idempotent:** Returns 204 even if not following
    """
    await FollowRepository.unfollow_user(
        pool=pool,
        follower_id=current_user_id,
        followee_id=user_id
    )
    
    return None
