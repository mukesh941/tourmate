from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Query

from app.schemas.common import Envelope
from app.schemas.activity import ActivityResponse
from app.services.activity_service import (
    get_all_activities,
    get_activity_by_id
)

router = APIRouter(prefix="/activities", tags=["activities"])

@router.get("", response_model=Envelope[List[ActivityResponse]])
async def list_activities(
    city: Optional[str] = Query(None, description="Filter by destination city"),
    q: Optional[str] = Query(None, description="Search keyword"),
    min_rating: Optional[float] = Query(None, description="Minimum star rating"),
    activity_type: Optional[str] = Query(None, description="Required activity type"),
    lat: Optional[float] = Query(None, description="Latitude for geo-search"),
    lng: Optional[float] = Query(None, description="Longitude for geo-search"),
    radius_km: Optional[float] = Query(10.0, description="Radius in kilometers for geo-search")
):
    activities = await get_all_activities(
        city=city,
        query=q,
        min_rating=min_rating,
        activity_type=activity_type,
        lat=lat,
        lng=lng,
        radius_km=radius_km
    )
    return Envelope(success=True, data=activities)

@router.get("/{activity_id}", response_model=Envelope[ActivityResponse])
async def get_activity(activity_id: str):
    activity = await get_activity_by_id(activity_id)
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")
    return Envelope(success=True, data=activity)
