from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status, Query, Body
from pydantic import BaseModel

from app.schemas.common import Envelope
from app.core.database import get_db
from app.services import osrm_service

router = APIRouter(prefix="/locations", tags=["locations"])

class RouteRequest(BaseModel):
    coordinates: List[Dict[str, float]]
    mode: str = "driving"

@router.get("/search", response_model=Envelope[List[Dict[str, Any]]])
async def search_locations(
    query: str = Query(..., min_length=2, description="Search query for a destination or location")
):
    db = get_db()
    
    # Text search in Destinations and Places to find a matching area
    # In a real app we might use MapBox/Google Maps geocoding API.
    # For now, we return matching Destinations or TouristPlaces that have a location.
    
    results = []
    
    # 1. Search Destinations
    dest_cursor = db.destinations.find({
        "$or": [
            {"name": {"$regex": query, "$options": "i"}},
            {"state": {"$regex": query, "$options": "i"}},
            {"country": {"$regex": query, "$options": "i"}}
        ]
    }).limit(3)
    
    async for dest in dest_cursor:
        # Destinations might have lat/lng directly on the document now.
        lat = dest.get("lat")
        lng = dest.get("lng")
        if lat is None or lng is None:
            if "location" in dest and dest["location"] and "coordinates" in dest["location"]:
                lng, lat = dest["location"]["coordinates"]
        
        results.append({
            "id": str(dest["_id"]),
            "name": dest.get("name"),
            "type": "destination",
            "lat": lat,
            "lng": lng,
            "image": dest.get("cover_image", "")
        })

    # 2. Search Places
    place_cursor = db.tourist_places.find({
        "name": {"$regex": query, "$options": "i"},
        "location": {"$exists": True}
    }).limit(5)
    
    async for place in place_cursor:
        lat, lng = None, None
        if "location" in place and place["location"] and "coordinates" in place["location"]:
            lng, lat = place["location"]["coordinates"]
        
        results.append({
            "id": str(place["_id"]),
            "name": place.get("name"),
            "type": "place",
            "lat": lat,
            "lng": lng,
            "image": place.get("images", [""])[0] if place.get("images") else ""
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
