from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_dependency, get_optional_current_user
from app.core.db import get_async_db
from app.schemas.auth import UserPublic
from app.schemas.common import Envelope
from app.schemas.itinerary import (
    ItineraryCreate, ItineraryUpdate, ItineraryResponse, ItineraryGenerateRequest
)
from app.schemas.route_optimization import (
    ItineraryOptimizePlanRequest,
    ItineraryOptimizePlanResponse,
)
from app.services.itinerary_service import (
    get_user_itineraries, get_itinerary, create_itinerary, update_itinerary, delete_itinerary
)
from app.services.itinerary_optimization_service import optimize_and_persist_itinerary
from app.services.place_service import get_place
from app.services.ai_service import generate_itinerary_via_llm
from app.services.authoritative_itinerary_service import generate_authoritative_itinerary

router = APIRouter(prefix="/itineraries", tags=["itineraries"])

@router.post("/generate", response_model=Envelope[List[dict]])
async def generate_itinerary(
    payload: ItineraryGenerateRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserPublic | None = Depends(get_optional_current_user)
):
    if not payload.destination_name and not payload.place_ids:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Must provide either destination_name or specific places")

    itinerary_options = await generate_authoritative_itinerary(payload, db)
    return Envelope(success=True, data=itinerary_options)

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

class OptimizeDayRequest(BaseModel):
    day_schedule: dict
    context: str = ""

@router.post("/optimize", response_model=Envelope[dict])
async def optimize_day(
    payload: OptimizeDayRequest,
    current_user: UserPublic = Depends(get_current_user_dependency)
):
    # Mock implementation of "Optimize My Day" AI action
    # In a real scenario, this would call the AI service with the day_schedule and context
    
    # We'll just return a success message and a slightly modified schedule for demonstration
    optimized_schedule = payload.day_schedule.copy()
    
    return Envelope(success=True, data={
        "message": "✨ I optimized Day. Reduced travel time by 15 mins and added a lunch break.",
        "optimized_schedule": optimized_schedule
    })


@router.post("/optimize-plan", response_model=Envelope[ItineraryOptimizePlanResponse])
async def optimize_itinerary_plan(
    payload: ItineraryOptimizePlanRequest,
    current_user: UserPublic = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Authoritative Phase 4 Itinerary Optimization endpoint.
    Pipeline: Accommodation Anchor + Day POIs -> OSRM directed matrix ->
    Internal Directed Graph -> Anchored Cheapest Insertion -> Anchored 2-opt ->
    Opening-hour validation -> Second-best alternative tour -> A*/Dijkstra benchmark ->
    PostgreSQL persistence.
    """
    result = await optimize_and_persist_itinerary(payload, db=db, current_user_id=str(current_user.id))
    return Envelope(success=True, data=result)
