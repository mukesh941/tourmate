"""
Mongo document shape for `users` (Pydantic model for internal use, not the wire schema).
Mirrors §6 of the Phase 0 plan.
"""
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class UserRole(str, Enum):
    user = "user"
    admin = "admin"


class UserInDB(BaseModel):
    name: str
    email: EmailStr
    password_hash: str
    role: UserRole = UserRole.user
    preferred_language: str = "en"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
