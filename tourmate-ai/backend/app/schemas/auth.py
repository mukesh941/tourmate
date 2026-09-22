"""
Request/response schemas for the auth API - kept separate from the Mongo model
per the layering rule in §4 of the Phase 0 plan.
"""
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    # Administrative fields are permitted in the schema for compatibility but are strictly ignored server-side
    is_admin: Optional[bool] = None
    role: Optional[str] = None

    model_config = {"extra": "ignore"}


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserPublic(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: str
    preferred_language: str
