from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.api.deps import get_current_user_dependency
from app.schemas.auth import UserPublic
from app.schemas.common import Envelope
from app.schemas.itinerary import (
    ItineraryCreate, ItineraryUpdate, ItineraryResponse, ItineraryGenerateRequest
)
from app.services.itinerary_service import (
    get_user_itineraries, get_itinerary, create_itinerary, update_itinerary, delete_itinerary
)
from app.services.place_service import get_place
from app.services.ai_service import generate_itinerary_via_llm

router = APIRouter(prefix="/itineraries", tags=["itineraries"])

@router.post("/generate", response_model=Envelope[List[dict]])
async def generate_itinerary(
    payload: ItineraryGenerateRequest,
    current_user: UserPublic = Depends(get_current_user_dependency)
):
    if not payload.destination_name and not payload.place_ids:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Must provide either destination_name or specific places")

    places_info = []
    if payload.place_ids:
        for pid in payload.place_ids:
            place = await get_place(pid)
            if place:
                places_info.append({
                    "id": place.id,
                    "name": place.name,
                    "description": place.description,
                    "category_id": place.category_id,
                    "visit_duration_minutes": place.visit_duration_minutes
                })
        
    generated_schedule = generate_itinerary_via_llm(
        places_info=places_info,
        days=payload.days,
        start_time=payload.start_time,
        end_time=payload.end_time,
        accommodation=payload.accommodation,
        energy_level=payload.energy_level,
        destination_name=payload.destination_name
    )
    
    return Envelope(success=True, data=generated_schedule)

@router.get("", response_model=Envelope[List[ItineraryResponse]])
async def read_itineraries(current_user: UserPublic = Depends(get_current_user_dependency)):
    itineraries = await get_user_itineraries(current_user.id)
    return Envelope(success=True, data=itineraries)

@router.post("", response_model=Envelope[ItineraryResponse])
async def add_itinerary(
    payload: ItineraryCreate,
    current_user: UserPublic = Depends(get_current_user_dependency)
):
    itinerary = await create_itinerary(current_user.id, payload)
    return Envelope(success=True, data=itinerary)

@router.get("/{itinerary_id}", response_model=Envelope[ItineraryResponse])
async def read_itinerary(
    itinerary_id: str,
    current_user: UserPublic = Depends(get_current_user_dependency)
):
    itinerary = await get_itinerary(itinerary_id, current_user.id)
    if not itinerary:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Itinerary not found")
    return Envelope(success=True, data=itinerary)

@router.put("/{itinerary_id}", response_model=Envelope[ItineraryResponse])
async def edit_itinerary(
    itinerary_id: str,
    payload: ItineraryUpdate,
    current_user: UserPublic = Depends(get_current_user_dependency)
):
    itinerary = await update_itinerary(itinerary_id, current_user.id, payload)
    if not itinerary:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Itinerary not found")
    return Envelope(success=True, data=itinerary)

@router.delete("/{itinerary_id}", response_model=Envelope[bool])
async def remove_itinerary(
    itinerary_id: str,
    current_user: UserPublic = Depends(get_current_user_dependency)
):
    success = await delete_itinerary(itinerary_id, current_user.id)
    if not success:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Itinerary not found")
    return Envelope(success=True, data=True)
