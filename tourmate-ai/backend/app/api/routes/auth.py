"""
Auth endpoints: POST /api/auth/register, POST /api/auth/login, GET /api/auth/me
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_dependency
from app.core.db import get_async_db
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserPublic
from app.schemas.common import Envelope
from app.services.auth_service import AuthError, login_user, register_user
from app.core.limiter import limiter

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Envelope[UserPublic], status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def register(
    request: Request,
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_async_db),
):
    try:
        user = await register_user(payload, db=db)
    except AuthError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    return Envelope(success=True, data=user)


@router.post("/login", response_model=Envelope[TokenResponse])
@limiter.limit("5/minute")
async def login(
    request: Request,
    payload: LoginRequest,
    db: AsyncSession = Depends(get_async_db),
):
    try:
        try:
            tokens = await login_user(payload, db=db)
        except TypeError:
            tokens = await login_user(payload)
    except AuthError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc
    return Envelope(success=True, data=tokens)


@router.get("/me", response_model=Envelope[UserPublic])
async def me(current_user: UserPublic = Depends(get_current_user_dependency)):
    return Envelope(success=True, data=current_user)
