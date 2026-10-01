"""
Business logic for registration/login/current-user lookup.
Routes stay thin controllers; this is where DB + security helpers are orchestrated.
Backed by PostgreSQL + pgvector (app.models.sql.user.User).
"""
import uuid
import secrets
import hashlib
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import AsyncSessionLocal
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.models.sql.user import User, EmailVerificationToken
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserPublic
from app.services.email_service import send_verification_email


class AuthError(Exception):
    """Raised for any auth failure the API layer should turn into a 4xx."""
    def __init__(self, message: str, code: str = None):
        super().__init__(message)
        self.code = code


def _to_public(user: User) -> UserPublic:
    return UserPublic(
        id=str(user.id),
        name=user.name,
        email=user.email,
        role=user.role,
        preferred_language=user.preferred_language,
        is_email_verified=user.is_email_verified,
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
        is_email_verified=False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Generate token
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

    verification_token = EmailVerificationToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db.add(verification_token)
    await db.commit()

    # Send email
    await send_verification_email(user.email, token)

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

    if not user.is_email_verified:
        raise AuthError("Please verify your email before logging in.", code="email_unverified")

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


async def _execute_verify_email(token: str, db: AsyncSession) -> None:
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    stmt = select(EmailVerificationToken).where(
        EmailVerificationToken.token_hash == token_hash,
        EmailVerificationToken.used_at.is_(None)
    )
    res = await db.execute(stmt)
    verification_token = res.scalar_one_or_none()
    
    if not verification_token:
        raise AuthError("Invalid or already used verification token.")
        
    if verification_token.expires_at < datetime.now(timezone.utc):
        raise AuthError("Verification token has expired.")
        
    stmt = select(User).where(User.id == verification_token.user_id)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    
    if not user:
        raise AuthError("User not found.")
        
    if user.is_email_verified:
        raise AuthError("Email is already verified.")
        
    user.is_email_verified = True
    user.email_verified_at = datetime.now(timezone.utc)
    verification_token.used_at = datetime.now(timezone.utc)
    
    await db.commit()


async def verify_email(token: str, db: AsyncSession | None = None) -> None:
    if db is not None:
        return await _execute_verify_email(token, db)
    async with AsyncSessionLocal() as session:
        return await _execute_verify_email(token, session)


async def _execute_resend_verification(email: str, db: AsyncSession) -> None:
    stmt = select(User).where(User.email == email)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    
    if not user:
        # Do not reveal whether account exists
        return
        
    if user.is_email_verified:
        return
        
    # Invalidate previous active tokens
    stmt = select(EmailVerificationToken).where(
        EmailVerificationToken.user_id == user.id,
        EmailVerificationToken.used_at.is_(None)
    )
    res = await db.execute(stmt)
    active_tokens = res.scalars().all()
    for t in active_tokens:
        t.used_at = datetime.now(timezone.utc)
        
    # Generate new token
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

    verification_token = EmailVerificationToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db.add(verification_token)
    await db.commit()

    # Send email
    await send_verification_email(user.email, token)


async def resend_verification(email: str, db: AsyncSession | None = None) -> None:
    if db is not None:
        return await _execute_resend_verification(email, db)
    async with AsyncSessionLocal() as session:
        return await _execute_resend_verification(email, session)
