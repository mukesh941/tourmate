from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.common import Envelope
from app.core.db import get_async_db
from app.services import osrm_service, location_service

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
