from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, UUID4
from enum import Enum

# ===== Auth Models =====
class UserSignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: UUID4
    email: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# Story Models 

class VisibilityEnum(str, Enum):
    public = "public"
    friends = "friends"
    private = "private"


class CreateStoryRequest(BaseModel):
    text: Optional[str] = Field(None, max_length=500)
    media_key: Optional[str] = Field(None, max_length=255)
    visibility: VisibilityEnum = VisibilityEnum.public
    audience_user_ids: Optional[List[UUID4]] = None
    
    class Config:
        use_enum_values = True


class StoryResponse(BaseModel):
    id: UUID4
    author_id: UUID4
    author_email: Optional[str] = None
    text: Optional[str]
    media_key: Optional[str]
    visibility: str
    created_at: datetime
    expires_at: datetime
    view_count: Optional[int] = 0
    reaction_count: Optional[int] = 0
    
    class Config:
        from_attributes = True


# ===== Media Upload Models ===== 
# ADD THESE CLASSES BELOW:

class GenerateUploadUrlRequest(BaseModel):
    content_type: str = Field(
        ..., 
        description="MIME type (image/jpeg, video/mp4, etc.)",
        examples=["image/jpeg", "video/mp4"]
    )
    file_extension: str = Field(
        ..., 
        max_length=10, 
        description="File extension without dot",
        examples=["jpg", "mp4", "png"]
    )


class GenerateUploadUrlResponse(BaseModel):
    upload_url: str = Field(description="MinIO endpoint for upload")
    fields: dict = Field(description="Form fields for presigned POST")
    media_key: str = Field(description="Unique key to reference uploaded media")
    expires_in: int = Field(description="Seconds until URL expires")
    
    class Config:
        json_schema_extra = {
            "example": {
                "upload_url": "http://localhost:9000/stories-media",
                "fields": {
                    "key": "stories/550e8400-e29b-41d4-a716-446655440000.jpg",
                    "Content-Type": "image/jpeg",
                    "policy": "eyJleHBpcmF0aW9uIjoi...",
                    "x-amz-algorithm": "AWS4-HMAC-SHA256",
                    "x-amz-credential": "minioadmin/20251003/us-east-1/s3/aws4_request",
                    "x-amz-date": "20251003T110000Z",
                    "x-amz-signature": "abcdef1234567890"
                },
                "media_key": "stories/550e8400-e29b-41d4-a716-446655440000.jpg",
                "expires_in": 3600
            }
        }


class GetDownloadUrlRequest(BaseModel):
    media_key: str = Field(
        ..., 
        description="Media key from upload response",
        examples=["stories/550e8400-e29b-41d4-a716-446655440000.jpg"]
    )


class GetDownloadUrlResponse(BaseModel):
    download_url: str = Field(description="Presigned MinIO URL for downloading")
    expires_in: int = Field(default=3600, description="Seconds until URL expires")


# ===== Social Models (for later) =====
class ViewStoryRequest(BaseModel):
    """Empty body for idempotent view tracking"""
    pass


class ViewStoryResponse(BaseModel):
    story_id: UUID4
    viewer_id: UUID4
    viewed_at: datetime
    is_new_view: bool


class ReactionRequest(BaseModel):
    emoji: str = Field(..., pattern="^(👍|❤️|😂|😮|😢|🔥)$")


class ReactionResponse(BaseModel):
    id: UUID4
    story_id: UUID4
    user_id: UUID4
    emoji: str
    created_at: datetime


class UserStatsResponse(BaseModel):
    posted_count: int
    total_views: int
    unique_viewers: int
    reactions: dict


class FollowResponse(BaseModel):
    follower_id: UUID4
    followee_id: UUID4
    created_at: datetime
