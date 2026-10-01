"""
Google Places API — Backend Proxy Routes

All Google Places/Maps API calls go through this backend proxy.
The API key is NEVER exposed to the browser.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from app.api.deps import get_current_user_dependency
from app.core.db import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.auth import UserPublic
from app.schemas.common import Envelope
from app.services.google_places_service import (
    nearby_search,
    text_search,
    get_place_details,
    deduplicate_places,
    get_types_for_category,
)
from app.services.ml_service import generate_place_clusters
from app.services.ai_service import enrich_cluster_with_ai
from app.services.poi_service import get_all_pois
from app.services.location_service import search_postgres_locations
from app.core.config import settings

router = APIRouter(prefix="/google", tags=["google-places"])


# ── Request/Response Models ────────────────────────────────────────────────────

class TextSearchRequest(BaseModel):
    query: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    radius_km: float = 50.0
    category: Optional[str] = None
    max_results: int = 20


class ClusterRequest(BaseModel):
    places: List[Dict[str, Any]]
    k: int = 4
    interests: Optional[List[str]] = []


class EnrichRequest(BaseModel):
    places: List[Dict[str, Any]]
    interests: Optional[List[str]] = []


# ── Helpers ───────────────────────────────────────────────────────────────────

def _check_api_key():
    if not settings.google_maps_api_key:
        # Instead of 503, we just warn. The services will handle graceful fallbacks
        import logging
        logging.getLogger(__name__).warning("Google Maps API key is not configured.")
        return False
    return True


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/places/nearby", response_model=Envelope[dict])
async def get_nearby_places(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    radius_km: float = Query(5.0, description="Search radius in kilometers"),
    category: Optional[str] = Query(None, description="TourMate category filter"),
    max_results: int = Query(20, le=20),
    current_user: UserPublic = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Nearby Search via Google Places API (New).
    Requires authentication. API key stays server-side.
    """
    _check_api_key()

    included_types = get_types_for_category(category) if category and category != "all" else None
    radius_m = int(min(radius_km * 1000, 50000))  # Google max is 50km

    places = await nearby_search(
        lat=lat,
        lng=lng,
        radius_m=radius_m,
        included_types=included_types,
        max_results=max_results,
    )
    
    if not places:
        # Fallback to Postgres
        poi_results = await get_all_pois(
            lat=lat, lng=lng, radius_km=radius_km, category_id=category if category and category != "all" else None, db=db
        )
        # convert TouristPlaceResponse to dict format expected
        places = [p.model_dump() for p in poi_results[:max_results]]
            
    places = deduplicate_places(places)

    return Envelope(success=True, data={"places": places, "count": len(places)})


@router.post("/places/search", response_model=Envelope[dict])
async def search_places_by_text(
    payload: TextSearchRequest,
    current_user: UserPublic = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Text Search via Google Places API (New).
    Used when user searches for a city/destination/attraction.
    """
    _check_api_key()

    # Build a tourism-focused query
    category_hint = ""
    if payload.category and payload.category not in ("all", ""):
        category_hint = f" {payload.category} places"

    query = f"tourist attractions{category_hint} in {payload.query}"

    places = await text_search(
        query=query,
        lat=payload.lat,
        lng=payload.lng,
        radius_m=int(payload.radius_km * 1000),
        max_results=min(payload.max_results, 20),
    )
    
    if not places:
        # Fallback to TourMate Database
        places = await search_postgres_locations(payload.query, db, limit=payload.max_results)

    places = deduplicate_places(places)

    return Envelope(success=True, data={"places": places, "count": len(places)})


@router.get("/places/details/{place_id}", response_model=Envelope[dict])
async def get_google_place_details(
    place_id: str,
    current_user: UserPublic = Depends(get_current_user_dependency),
):
    """
    Place Details via Google Places API (New).
    """
    _check_api_key()

    place = await get_place_details(place_id)
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")
    return Envelope(success=True, data=place)


@router.post("/places/cluster", response_model=Envelope[dict])
async def cluster_google_places(
    payload: ClusterRequest,
    current_user: UserPublic = Depends(get_current_user_dependency),
):
    """
    Cluster a list of normalized Google Places using K-Means.
    Adapts the Google places format for the existing ml_service cluster engine.
    """
    if not payload.places:
        return Envelope(success=True, data={"k": 0, "clusters": [], "skipped": 0})

    # Build adapter objects that ml_service.generate_place_clusters can work with
    # ml_service expects objects with .location.coordinates = [lng, lat]
    class _FakeLocation:
        def __init__(self, lng, lat):
            self.coordinates = [lng, lat]

    class _FakePlace:
        def __init__(self, p):
            self.id = p.get("id", "")
            self.name = p.get("name", "")
            lng = p.get("longitude") or p.get("lng") or (p.get("location") or {}).get("coordinates", [None, None])[0]
            lat = p.get("latitude") or p.get("lat") or (p.get("location") or {}).get("coordinates", [None, None])[1]
            self.location = _FakeLocation(lng, lat) if lng and lat else None
            self.category = type("Cat", (), {"name": p.get("category_name", p.get("category", {}).get("name", ""))})()
            # Keep all original fields accessible
            self._raw = p

        def dict(self):
            return self._raw

    fake_places = [_FakePlace(p) for p in payload.places]
    result = await generate_place_clusters(fake_places, payload.k)

    # Convert cluster places back to dicts
    for cluster in result.get("clusters", []):
        cluster["places"] = [
            p._raw if hasattr(p, "_raw") else p.dict() if hasattr(p, "dict") else p
            for p in cluster.get("places", [])
        ]

    return Envelope(success=True, data=result)


@router.post("/places/cluster/enrich", response_model=Envelope[dict])
async def enrich_google_cluster(
    payload: EnrichRequest,
    current_user: UserPublic = Depends(get_current_user_dependency),
):
    """
    AI-enrich a cluster of Google Places using Gemini.
    Reuses the existing ai_service.enrich_cluster_with_ai function.
    """
    result = enrich_cluster_with_ai(payload.places, payload.interests)
    return Envelope(success=True, data=result)
