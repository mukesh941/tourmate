"""
User schemas for API requests and responses.
"""
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.auth import UserPublic


class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    preferred_language: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6, description="Minimum 6 characters")


class UserPreferencesUpdate(BaseModel):
    interests: List[str] = Field(default_factory=list)
    budget_range: Optional[str] = None
    travel_style: Optional[str] = None
    available_time: Optional[str] = None
    preferred_activities: List[str] = Field(default_factory=list)


class UserPreferencesResponse(UserPreferencesUpdate):
    id: str
    user_id: str
