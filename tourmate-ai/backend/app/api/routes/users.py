from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user_dependency
from app.schemas.auth import UserPublic
from app.schemas.common import Envelope
from app.schemas.user import UserPreferencesResponse, UserPreferencesUpdate, UserProfileUpdate
from app.services.user_service import get_user_preferences, update_user_preferences, update_user_profile

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/profile", response_model=Envelope[UserPublic])
async def get_profile(current_user: UserPublic = Depends(get_current_user_dependency)):
    return Envelope(success=True, data=current_user)


@router.put("/profile", response_model=Envelope[UserPublic])
async def update_profile(
    payload: UserProfileUpdate,
    current_user: UserPublic = Depends(get_current_user_dependency)
):
    try:
        updated_user = await update_user_profile(current_user.id, payload)
        return Envelope(success=True, data=updated_user)
    except Exception as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc


@router.get("/preferences", response_model=Envelope[UserPreferencesResponse | None])
async def get_preferences(current_user: UserPublic = Depends(get_current_user_dependency)):
    try:
        prefs = await get_user_preferences(current_user.id)
        return Envelope(success=True, data=prefs)
    except Exception as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc


@router.put("/preferences", response_model=Envelope[UserPreferencesResponse])
async def update_preferences(
    payload: UserPreferencesUpdate,
    current_user: UserPublic = Depends(get_current_user_dependency)
):
    try:
        prefs = await update_user_preferences(current_user.id, payload)
        return Envelope(success=True, data=prefs)
    except Exception as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
