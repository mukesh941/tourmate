from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.common import Envelope
from app.core.db import get_async_db
from app.services import osrm_service, location_service
from app.services.destination_resolver import (
    find_nearby_locations,
    get_state_locations,
    resolve_destination,
    normalize_location_name,
    CITY_ALIASES,
)

router = APIRouter(prefix="/locations", tags=["locations"])

class RouteRequest(BaseModel):
    coordinates: List[Dict[str, float]]
    mode: str = "driving"

@router.get("/search", response_model=Envelope[List[Dict[str, Any]]])
async def search_locations(
    query: str = Query(..., min_length=2, description="Search query for a destination or location"),
    sql_db: AsyncSession = Depends(get_async_db),
):
    results = []

    # 1. Search canonical PostgreSQL locations first
    pg_locs = await location_service.search_postgres_locations(query, sql_db)
    for loc in pg_locs:
        results.append({
            "id": loc["id"],
            "name": f"{loc['name']}, {loc['city']}",
            "type": "location",
            "lat": loc["lat"],
            "lng": loc["lng"],
            "image": "",
        })

    # 2. Search canonical PostgreSQL POIs
    from app.services import poi_service
    pois = await poi_service.get_all_pois(q=query, db=sql_db)
    for p in pois:
        if p.location and p.location.coordinates:
            results.append({
                "id": str(p.id),
                "name": p.name,
                "type": "place",
                "lat": p.location.coordinates[1],
                "lng": p.location.coordinates[0],
                "image": p.images[0] if p.images else "",
            })

    # 3. If no local results, geocode via OpenStreetMap Nominatim
    if not results:
        geo = await osrm_service.geocode(query)
        if geo:
            results.append({
                "id": "geo-" + query.lower().replace(" ", "-"),
                "name": geo.get("display_name", query),
                "type": "location",
                "lat": geo.get("latitude"),
                "lng": geo.get("longitude"),
                "image": "",
            })

    # Deduplicate results if they have lat/lng
    unique_results = []
    seen = set()
    for r in results:
        key = f"{r['name']}_{r['lat']}_{r['lng']}"
        if key not in seen and r['lat'] is not None and r['lng'] is not None:
            seen.add(key)
            unique_results.append(r)
            
    return Envelope(success=True, data=unique_results)

@router.get("/geocode", response_model=Envelope[Dict[str, Any]])
async def geocode_location(query: str = Query(..., min_length=2)):
    result = await osrm_service.geocode(query)
    if not result:
        raise HTTPException(status_code=404, detail="Location not found")
    return Envelope(success=True, data=result)

@router.get("/reverse", response_model=Envelope[Dict[str, str]])
async def reverse_geocode(lat: float, lon: float):
    name = await osrm_service.reverse_geocode(lat, lon)
    if not name:
        name = "Unknown Location"
    return Envelope(success=True, data={"display_name": name})

@router.post("/route", response_model=Envelope[Dict[str, Any]])
async def calculate_route(req: RouteRequest = Body(...)):
    if len(req.coordinates) < 2:
        raise HTTPException(status_code=400, detail="At least 2 coordinates required")
    result = await osrm_service.calculate_route(req.coordinates, req.mode)
    if not result:
        raise HTTPException(status_code=400, detail="Could not calculate route")
    return Envelope(success=True, data=result)


@router.get("/nearby", response_model=Envelope[List[Dict[str, Any]]])
async def get_nearby_locations(
    lat: float = Query(..., description="Latitude of the center point"),
    lng: float = Query(..., description="Longitude of the center point"),
    radius_km: float = Query(50.0, ge=1.0, le=500.0, description="Search radius in km"),
    types: Optional[str] = Query(
        None,
        description="Comma-separated location types to filter: city,tourist_destination,state"
    ),
    limit: int = Query(20, ge=1, le=100),
    sql_db: AsyncSession = Depends(get_async_db),
):
    """
    Find nearby locations within a given radius using Haversine distance.
    Uses the TourMate geographic database (7,030+ Indian locations).
    
    Returns locations sorted by distance ascending.
    All coordinates are for real verified Indian locations.
    """
    # Validate India bounding box (roughly)
    if not (6.0 <= lat <= 38.0 and 68.0 <= lng <= 98.0):
        return Envelope(
            success=False,
            error="Coordinates appear to be outside India. TourMate covers Indian locations only.",
            data=[],
        )

    location_types = None
    if types:
        location_types = [t.strip() for t in types.split(",") if t.strip()]

    nearby = await find_nearby_locations(
        latitude=lat,
        longitude=lng,
        radius_km=radius_km,
        db=sql_db,
        location_types=location_types,
        limit=limit,
    )

    return Envelope(success=True, data=nearby)


@router.get("/destinations", response_model=Envelope[List[Dict[str, Any]]])
async def get_destinations_by_state(
    state: Optional[str] = Query(None, description="Indian state or UT name"),
    types: Optional[str] = Query(
        "tourist_destination,city",
        description="Comma-separated location types"
    ),
    limit: int = Query(30, ge=1, le=100),
    sql_db: AsyncSession = Depends(get_async_db),
):
    """
    Browse tourist destinations and cities by state.
    Returns tourist_destinations first, then cities.
    """
    if not state:
        raise HTTPException(status_code=400, detail="State name is required")

    location_types = None
    if types:
        location_types = [t.strip() for t in types.split(",") if t.strip()]

    results = await get_state_locations(
        state_name=state,
        db=sql_db,
        location_types=location_types,
        limit=limit,
    )

    return Envelope(success=True, data=results)


@router.get("/resolve", response_model=Envelope[Dict[str, Any]])
async def resolve_location_by_name(
    name: str = Query(..., min_length=2, description="Location name to resolve (supports aliases)"),
    sql_db: AsyncSession = Depends(get_async_db),
):
    """
    Resolve a location name to its canonical form in the TourMate database.
    Supports Indian city aliases (Bangalore -> Bengaluru, Bombay -> Mumbai, etc.).
    Returns the canonical location record with coordinates.
    """
    normalized = normalize_location_name(name)
    resolved = await resolve_destination(normalized, sql_db)

    if not resolved:
        # Try direct search
        resolved = await resolve_destination(name, sql_db)

    if not resolved:
        raise HTTPException(
            status_code=404,
            detail=f"Location '{name}' not found in TourMate database. Try a city or state name."
        )

    return Envelope(success=True, data=resolved)
