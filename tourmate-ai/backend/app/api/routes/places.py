from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin, get_current_user_dependency
from app.core.db import get_async_db
from app.schemas.auth import UserPublic
from app.schemas.common import Envelope
from app.schemas.place import TouristPlaceCreate, TouristPlaceUpdate, TouristPlaceResponse
from app.services import poi_service
from app.services.place_service import (
    get_all_places, get_place, create_place, update_place, delete_place, get_recommended_places
)
from app.services.ml_service import generate_place_clusters
from app.services.route_service import optimize_route, astar_route_optimization
from app.services.ai_service import enrich_cluster_with_ai
from pydantic import BaseModel
from typing import Dict, Any

class ClusterEnrichRequest(BaseModel):
    places: List[Dict[str, Any]]
    interests: Optional[List[str]] = []

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
    radius_km: Optional[float] = Query(10.0, description="Radius in kilometers for geo-search"),
    db: AsyncSession = Depends(get_async_db),
):
    # Query canonical PostgreSQL POIs first
    pg_places = await poi_service.get_all_pois(
        category_id=category_id,
        q=q,
        min_rating=min_rating,
        lat=lat,
        lng=lng,
        radius_km=radius_km,
        db=db,
    )
    if pg_places:
        return Envelope(success=True, data=pg_places)

    # Fallback to legacy MongoDB places if PostgreSQL has no results (e.g. legacy destination_id)
    try:
        places = await get_all_places(destination_id, category_id, q, min_rating, lat, lng, radius_km)
        return Envelope(success=True, data=places)
    except Exception:
        return Envelope(success=True, data=[])

@router.get("/clusters", response_model=Envelope[dict])
async def get_clusters(
    k: int = Query(3, description="Number of clusters"),
    destination_id: Optional[str] = None,
    category_id: Optional[str] = None,
    category: Optional[str] = None,
    lat: Optional[float] = Query(None, description="Latitude for geo-search"),
    lng: Optional[float] = Query(None, description="Longitude for geo-search"),
    radius_km: Optional[float] = Query(10.0, description="Radius in kilometers for geo-search")
):
    places = await get_all_places(destination_id, category_id, category, None, lat, lng, radius_km)
    clusters_data = await generate_place_clusters(places, k)
    return Envelope(success=True, data=clusters_data)

@router.post("/clusters/enrich", response_model=Envelope[dict])
async def enrich_cluster_endpoint(payload: ClusterEnrichRequest):
    result = enrich_cluster_with_ai(payload.places, payload.interests)
    return Envelope(success=True, data=result)

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
async def read_place(place_id: str, db: AsyncSession = Depends(get_async_db)):
    # 1. Query canonical PostgreSQL POIs
    pg_place = await poi_service.get_poi_by_id(place_id, db=db)
    if pg_place:
        return Envelope(success=True, data=pg_place)

    # 2. Fallback to legacy MongoDB places
    try:
        place = await get_place(place_id)
        if place:
            return Envelope(success=True, data=place)
    except Exception:
        pass

    raise HTTPException(status.HTTP_404_NOT_FOUND, "Place not found")

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
