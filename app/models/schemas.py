from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, UUID4


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


# ===== Story Models (we'll add these in next steps) =====
# Will add later...
