from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional

from app.api.deps import require_admin, get_current_user_dependency
from app.schemas.auth import UserPublic
from app.schemas.common import Envelope
from app.schemas.place import TouristPlaceCreate, TouristPlaceUpdate, TouristPlaceResponse
from app.services.place_service import (
    get_all_places, get_place, create_place, update_place, delete_place, get_recommended_places
)
from app.services.ml_service import generate_place_clusters
from app.services.route_service import optimize_route, astar_route_optimization
from pydantic import BaseModel

class RouteOptimizeRequest(BaseModel):
    place_ids: List[str]
    algorithm: Optional[str] = "astar"

router = APIRouter(prefix="/places", tags=["places"])

@router.get("", response_model=Envelope[List[TouristPlaceResponse]])
async def read_places(
    destination_id: Optional[str] = None,
    category_id: Optional[str] = None,
    q: Optional[str] = None,
    min_rating: Optional[float] = None,
    lat: Optional[float] = Query(None, description="Latitude for geo-search"),
    lng: Optional[float] = Query(None, description="Longitude for geo-search"),
    radius_km: Optional[float] = Query(10.0, description="Radius in kilometers for geo-search")
):
    places = await get_all_places(destination_id, category_id, q, min_rating, lat, lng, radius_km)
    return Envelope(success=True, data=places)

@router.get("/clusters", response_model=Envelope[dict])
async def get_clusters(k: int = Query(3, description="Number of clusters")):
    places = await get_all_places()
    clusters_data = await generate_place_clusters(places, k)
    return Envelope(success=True, data=clusters_data)

@router.get("/recommendations", response_model=Envelope[List[TouristPlaceResponse]])
async def get_recommendations(current_user: UserPublic = Depends(get_current_user_dependency)):
    places = await get_recommended_places(current_user.id)
    return Envelope(success=True, data=places)

@router.post("/route/optimize", response_model=Envelope[dict])
async def optimize_route_endpoint(payload: RouteOptimizeRequest):
    places = []
    for pid in payload.place_ids:
        p = await get_place(pid)
        if p:
            places.append(p)
            
    res = astar_route_optimization(places)
    
    return Envelope(success=True, data=res)

@router.get("/{place_id}", response_model=Envelope[TouristPlaceResponse])
async def read_place(place_id: str):
    place = await get_place(place_id)
    if not place:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Place not found")
    return Envelope(success=True, data=place)

@router.post("", response_model=Envelope[TouristPlaceResponse], dependencies=[Depends(require_admin)])
async def add_place(payload: TouristPlaceCreate):
    place = await create_place(payload)
    return Envelope(success=True, data=place)

@router.put("/{place_id}", response_model=Envelope[TouristPlaceResponse], dependencies=[Depends(require_admin)])
async def edit_place(place_id: str, payload: TouristPlaceUpdate):
    place = await update_place(place_id, payload)
    if not place:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Place not found")
    return Envelope(success=True, data=place)

@router.delete("/{place_id}", response_model=Envelope[bool], dependencies=[Depends(require_admin)])
async def remove_place(place_id: str):
    success = await delete_place(place_id)
    if not success:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Place not found")
    return Envelope(success=True, data=True)
