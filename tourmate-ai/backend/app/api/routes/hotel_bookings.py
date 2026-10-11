from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.api.deps import get_current_user_dependency
from app.core.db import get_async_db
from app.schemas.auth import UserPublic
from app.schemas.common import Envelope
from app.schemas.hotel import HotelBookingResponse
from app.services.hotel_service import get_user_hotel_bookings, cancel_hotel_booking
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.sql.hotel import HotelBooking

router = APIRouter(prefix="/hotel-bookings", tags=["hotel-bookings"])

@router.get("/my", response_model=Envelope[List[HotelBookingResponse]])
async def my_hotel_bookings(
    current_user: UserPublic = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_async_db)
):
    bookings = await get_user_hotel_bookings(current_user.id, db=db)
    return Envelope(success=True, data=bookings)

@router.get("/{booking_id}", response_model=Envelope[HotelBookingResponse])
async def get_booking_details(
    booking_id: str,
    current_user: UserPublic = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_async_db)
):
    stmt = select(HotelBooking).options(
        selectinload(HotelBooking.hotel),
        selectinload(HotelBooking.room_type),
        selectinload(HotelBooking.user)
    ).where(HotelBooking.id == uuid.UUID(booking_id))
    
    result = await db.execute(stmt)
    b = result.scalar_one_or_none()
    
    if not b:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
        
    if str(b.user_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this booking")
        
    nights = (b.check_out - b.check_in).days
    
    resp = HotelBookingResponse(
        id=str(b.id),
        user_id=str(b.user_id),
        user_name=b.user.name,
        user_email=b.user.email,
        hotel_id=str(b.hotel_id),
        hotel_name=b.hotel.name,
        hotel_city=b.hotel.city,
        hotel_image=b.hotel.images[0] if b.hotel.images else "",
        room_name=b.room_type.name,
        check_in_date=b.check_in.strftime("%Y-%m-%d"),
        check_out_date=b.check_out.strftime("%Y-%m-%d"),
        nights=nights,
        rooms=b.rooms_booked,
        guests=b.adults,
        price_per_night=float(b.total_price / nights / b.rooms_booked) if nights > 0 and b.rooms_booked > 0 else 0,
        total_price=float(b.total_price),
        status=b.status,
        special_requests="",
        created_at=b.created_at.isoformat()
    )
    
    return Envelope(success=True, data=resp)


@router.post("/{booking_id}/cancel", response_model=Envelope[dict])
async def cancel_booking(
    booking_id: str,
    current_user: UserPublic = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_async_db)
):
    success = await cancel_hotel_booking(booking_id, current_user.id, db=db)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found or already cancelled")
    return Envelope(success=True, data={"message": "Hotel reservation cancelled successfully"})
