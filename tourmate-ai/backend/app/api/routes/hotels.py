from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_dependency
from app.core.db import get_async_db
from app.schemas.auth import UserPublic
from app.schemas.common import Envelope
from app.schemas.hotel import HotelResponse, HotelBookingCreate, HotelBookingResponse
from app.services.hotel_service import (
    get_all_hotels,
    get_hotel_by_id,
    create_hotel_booking,
    check_availability
)

router = APIRouter(prefix="/hotels", tags=["hotels"])

@router.get("", response_model=Envelope[List[HotelResponse]])
async def list_hotels(
    city: Optional[str] = Query(None, description="Filter by destination city"),
    q: Optional[str] = Query(None, description="Search keyword"),
    min_price: Optional[float] = Query(None, description="Minimum price per night"),
    max_price: Optional[float] = Query(None, description="Maximum price per night"),
    min_rating: Optional[float] = Query(None, description="Minimum star rating"),
    amenity: Optional[str] = Query(None, description="Required amenity"),
    lat: Optional[float] = Query(None, description="Latitude for geo-search"),
    lng: Optional[float] = Query(None, description="Longitude for geo-search"),
    radius_km: Optional[float] = Query(10.0, description="Radius in kilometers for geo-search"),
    db: AsyncSession = Depends(get_async_db),
):
    hotels = await get_all_hotels(
        city=city,
        query=q,
        min_price=min_price,
        max_price=max_price,
        min_rating=min_rating,
        amenity=amenity,
        lat=lat,
        lng=lng,
        radius_km=radius_km,
        db=db,
    )
    return Envelope(success=True, data=hotels)

@router.get("/{hotel_id}", response_model=Envelope[HotelResponse])
async def get_hotel(hotel_id: str, db: AsyncSession = Depends(get_async_db)):
    hotel = await get_hotel_by_id(hotel_id, db=db)
    if not hotel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hotel not found")
    return Envelope(success=True, data=hotel)

@router.get("/{hotel_id}/availability", response_model=Envelope[dict])
async def get_hotel_availability(
    hotel_id: str,
    check_in: str = Query(...),
    check_out: str = Query(...),
    rooms: int = Query(1),
    db: AsyncSession = Depends(get_async_db)
):
    avail = await check_availability(hotel_id, check_in, check_out, rooms, db=db)
    if "error" in avail:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=avail["error"])
    return Envelope(success=True, data=avail)


@router.post("/{hotel_id}/bookings", response_model=Envelope[HotelBookingResponse])
async def book_hotel_stay(
    hotel_id: str,
    payload: HotelBookingCreate,
    current_user: UserPublic = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_async_db)
):
    try:
        # Override hotel_id in payload if passed in URL
        payload.hotel_id = hotel_id
        booking = await create_hotel_booking(
            user_id=str(current_user.id),
            user_name=current_user.name,
            user_email=current_user.email,
            payload=payload,
            db=db
        )
        return Envelope(success=True, data=booking)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create booking")

# Keep old endpoints for backwards compatibility temporarily
@router.post("/book", response_model=Envelope[HotelBookingResponse])
async def legacy_book_hotel_stay(
    payload: HotelBookingCreate,
    current_user: UserPublic = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_async_db)
):
    try:
        booking = await create_hotel_booking(
            user_id=str(current_user.id),
            user_name=current_user.name,
            user_email=current_user.email,
            payload=payload,
            db=db
        )
        return Envelope(success=True, data=booking)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create booking")
