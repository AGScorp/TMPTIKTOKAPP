# Pydantic schemas for TikTok API payloads/responses.
from pydantic import BaseModel, Field
from typing import Optional

class HealthResponse(BaseModel):
    status: str

# Display API schemas
class UserStats(BaseModel):
    follower_count: int = Field(0, description="Total followers")
    following_count: int = Field(0, description="Total following")
    likes_count: int = Field(0, description="Total likes")
    video_count: int = Field(0, description="Total videos")

class UserProfile(BaseModel):
    open_id: str = Field(..., description="TikTok user's open_id")
    display_name: Optional[str] = Field(None, description="Display name")
    profile_image_url: Optional[str] = Field(None, description="Profile image URL")
    stats: Optional[UserStats] = Field(None, description="Aggregated stats")

class DisplayUserResponse(BaseModel):
    placeholder: Optional[bool] = Field(None, description="True when using dev stub")
    data: dict

# OAuth/token related schemas
class TokenInfo(BaseModel):
    token_type: Optional[str] = Field(None, description="e.g., Bearer")
    expires_in: Optional[int] = Field(None, description="Seconds until expiration")
    scope: Optional[str] = Field(None, description="Granted scopes")

class ClientTokenResponse(BaseModel):
    message: str
    token: dict

class RefreshTokenResponse(BaseModel):
    message: str
    token: dict

class RevokeTokenResponse(BaseModel):
    message: str
    result: dict
