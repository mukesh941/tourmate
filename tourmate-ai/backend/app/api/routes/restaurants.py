from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Query

from app.schemas.common import Envelope
from app.schemas.restaurant import RestaurantResponse
from app.services.restaurant_service import (
    get_all_restaurants,
    get_restaurant_by_id
)

router = APIRouter(prefix="/restaurants", tags=["restaurants"])

@router.get("", response_model=Envelope[List[RestaurantResponse]])
async def list_restaurants(
    city: Optional[str] = Query(None, description="Filter by destination city"),
    q: Optional[str] = Query(None, description="Search keyword"),
    min_rating: Optional[float] = Query(None, description="Minimum star rating"),
    cuisine: Optional[str] = Query(None, description="Required cuisine type"),
    lat: Optional[float] = Query(None, description="Latitude for geo-search"),
    lng: Optional[float] = Query(None, description="Longitude for geo-search"),
    radius_km: Optional[float] = Query(10.0, description="Radius in kilometers for geo-search")
):
    restaurants = await get_all_restaurants(
        city=city,
        query=q,
        min_rating=min_rating,
        cuisine=cuisine,
        lat=lat,
        lng=lng,
        radius_km=radius_km
    )
    return Envelope(success=True, data=restaurants)

@router.get("/{restaurant_id}", response_model=Envelope[RestaurantResponse])
async def get_restaurant(restaurant_id: str):
    restaurant = await get_restaurant_by_id(restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")
    return Envelope(success=True, data=restaurant)
