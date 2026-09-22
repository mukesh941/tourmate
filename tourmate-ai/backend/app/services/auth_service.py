"""
Business logic for registration/login/current-user lookup.
Routes stay thin controllers; this is where DB + security helpers are orchestrated.
Backed by PostgreSQL + pgvector (app.models.sql.user.User).
"""
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import AsyncSessionLocal
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.models.sql.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserPublic


class AuthError(Exception):
    """Raised for any auth failure the API layer should turn into a 4xx."""


def _to_public(user: User) -> UserPublic:
    return UserPublic(
        id=str(user.id),
        name=user.name,
        email=user.email,
        role=user.role,
        preferred_language=user.preferred_language,
    )


async def _execute_register(payload: RegisterRequest, db: AsyncSession) -> UserPublic:
    stmt = select(User).where(User.email == payload.email)
    res = await db.execute(stmt)
    existing = res.scalar_one_or_none()
    if existing:
        raise AuthError("An account with this email already exists.")

    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role="user",  # Public registration MUST ALWAYS assign 'user' role. Never trust client-supplied role or is_admin fields.
        preferred_language="en",
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return _to_public(user)


async def register_user(payload: RegisterRequest, db: AsyncSession | None = None) -> UserPublic:
    if db is not None:
        return await _execute_register(payload, db)
    async with AsyncSessionLocal() as session:
        return await _execute_register(payload, session)


async def _execute_login(payload: LoginRequest, db: AsyncSession) -> TokenResponse:
    stmt = select(User).where(User.email == payload.email)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise AuthError("Incorrect email or password.")

    if not user.is_active:
        raise AuthError("Account is deactivated.")

    subject = str(user.id)
    return TokenResponse(
        access_token=create_access_token(subject),
        refresh_token=create_refresh_token(subject),
    )


async def login_user(payload: LoginRequest, db: AsyncSession | None = None) -> TokenResponse:
    if db is not None:
        return await _execute_login(payload, db)
    async with AsyncSessionLocal() as session:
        return await _execute_login(payload, session)


async def _execute_get_current_user(user_id: str, db: AsyncSession) -> UserPublic:
    try:
        uid = uuid.UUID(str(user_id))
    except (ValueError, TypeError) as exc:
        raise AuthError("Invalid user id in token.") from exc

    stmt = select(User).where(User.id == uid)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    if not user or not user.is_active:
        raise AuthError("User not found or inactive.")
    return _to_public(user)


async def get_current_user(user_id: str, db: AsyncSession | None = None) -> UserPublic:
    if db is not None:
        return await _execute_get_current_user(user_id, db)
    async with AsyncSessionLocal() as session:
        return await _execute_get_current_user(user_id, session)
