import httpx
from typing import List, Dict, Any, Optional

OSRM_BASE_URL = "http://router.project-osrm.org/route/v1"
NOMINATIM_BASE_URL = "https://nominatim.openstreetmap.org"

USER_AGENT = "TourMateAI/1.0"

async def geocode(query: str) -> Optional[Dict[str, float]]:
    """
    Search for a location string and return its latitude/longitude using Nominatim.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{NOMINATIM_BASE_URL}/search",
                params={"q": query, "format": "json", "limit": 1},
                headers={"User-Agent": USER_AGENT}
            )
            response.raise_for_status()
            data = response.json()
            if data and len(data) > 0:
                return {
                    "latitude": float(data[0]["lat"]),
                    "longitude": float(data[0]["lon"]),
                    "display_name": data[0]["display_name"]
                }
            return None
        except Exception as e:
            print(f"Geocoding error: {e}")
            return None

async def reverse_geocode(lat: float, lon: float) -> Optional[str]:
    """
    Reverse geocode a coordinate into a human-readable address/city.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{NOMINATIM_BASE_URL}/reverse",
                params={"lat": lat, "lon": lon, "format": "json"},
                headers={"User-Agent": USER_AGENT}
            )
            response.raise_for_status()
            data = response.json()
            if data and "display_name" in data:
                # Extract a shorter version if possible
                addr = data.get("address", {})
                city = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("county")
                state = addr.get("state")
                if city and state:
                    return f"{city}, {state}"
                return data["display_name"]
            return None
        except Exception as e:
            print(f"Reverse geocoding error: {e}")
            return None

async def calculate_route(
    coordinates: List[Dict[str, float]], 
    mode: str = "driving"
) -> Optional[Dict[str, Any]]:
    """
    Calculate a route using OSRM given a list of coordinates (lat, lon).
    Mode can be 'driving', 'walking', 'cycling'.
    """
    if len(coordinates) < 2:
        return None

    # OSRM profile mapping
    osrm_profile = mode
    if mode == "car":
        osrm_profile = "driving"
    elif mode == "bike":
        osrm_profile = "cycling"
    elif mode == "walk" or mode == "walking":
        osrm_profile = "foot"
    else:
        osrm_profile = "driving"
        
    # OSRM takes lon,lat format
    coords_str = ";".join([f"{c['longitude']},{c['latitude']}" for c in coordinates])
    
    url = f"{OSRM_BASE_URL}/{osrm_profile}/{coords_str}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                url,
                params={
                    "overview": "full",
                    "geometries": "geojson",
                    "steps": "true"
                }
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") != "Ok":
                return None
                
            route = data["routes"][0]
            
            # Extract turn-by-turn instructions
            steps = []
            for leg in route["legs"]:
                for step in leg["steps"]:
                    # Basic instruction extraction
                    inst = step.get("maneuver", {}).get("type", "")
                    mod = step.get("maneuver", {}).get("modifier", "")
                    name = step.get("name", "")
                    
                    if inst == "turn":
                        text = f"Turn {mod} onto {name}" if name else f"Turn {mod}"
                    elif inst == "depart":
                        text = f"Head {mod} on {name}" if name else f"Head {mod}"
                    elif inst == "arrive":
                        text = "Arrive at destination"
                    else:
                        text = f"Continue on {name}" if name else "Continue"
                        
                    steps.append({
                        "instruction": text,
                        "distance_m": step.get("distance", 0),
                        "duration_s": step.get("duration", 0),
                        "location": step.get("maneuver", {}).get("location", [])
                    })
            
            return {
                "distance_km": round(route["distance"] / 1000, 2),
                "duration_minutes": round(route["duration"] / 60),
                "transport_mode": mode,
                "geometry": route["geometry"],
                "steps": steps,
                "origin": coordinates[0],
                "destination": coordinates[-1],
                "stops": coordinates[1:-1] if len(coordinates) > 2 else []
            }
            
        except Exception as e:
            print(f"OSRM Routing error: {e}")
            return None
