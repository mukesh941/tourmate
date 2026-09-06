from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from app.api.deps import get_current_user_dependency
from app.schemas.auth import UserPublic
from app.schemas.common import Envelope
from app.schemas.guide import GuideResponse, BookingCreate, BookingResponse
from app.services.guide_service import get_all_guides, get_guide, create_booking, get_user_bookings

router = APIRouter(prefix="/guides", tags=["guides"])

@router.get("", response_model=Envelope[List[GuideResponse]])
async def read_guides(location: Optional[str] = None):
    guides = await get_all_guides(location)
    return Envelope(success=True, data=guides)

@router.get("/{guide_id}", response_model=Envelope[GuideResponse])
async def read_guide(guide_id: str):
    guide = await get_guide(guide_id)
    if not guide:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Guide not found")
    return Envelope(success=True, data=guide)

@router.post("/book", response_model=Envelope[BookingResponse])
async def book_guide(
    payload: BookingCreate,
    current_user: UserPublic = Depends(get_current_user_dependency)
):
    try:
        booking = await create_booking(current_user.id, payload)
        return Envelope(success=True, data=booking)
    except Exception as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))

@router.get("/bookings/me", response_model=Envelope[List[BookingResponse]])
async def read_my_bookings(current_user: UserPublic = Depends(get_current_user_dependency)):
    bookings = await get_user_bookings(current_user.id)
    return Envelope(success=True, data=bookings)
