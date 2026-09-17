"""
Google Places API (New) — Backend Proxy Service

Handles all communication with Google Maps Platform APIs.
The API key stays server-side and is never exposed to the browser.

Cost control measures:
- In-memory TTL cache (5 minutes per unique query)
- Field masks: only request needed fields to reduce billing
- Max 20 results per request
- Deduplication by Google Place ID
"""
import hashlib
import json
import time
import httpx
from typing import List, Dict, Any, Optional
from app.core.config import settings

# ─── In-Memory Cache ───────────────────────────────────────────────────────────
_cache: Dict[str, Dict] = {}
CACHE_TTL_SECONDS = 300  # 5 minutes


def _cache_key(*args) -> str:
    raw = json.dumps(args, sort_keys=True, default=str)
    return hashlib.md5(raw.encode()).hexdigest()


def _cache_get(key: str):
    entry = _cache.get(key)
    if entry and (time.time() - entry["ts"]) < CACHE_TTL_SECONDS:
        return entry["data"]
    return None


def _cache_set(key: str, data: Any):
    _cache[key] = {"ts": time.time(), "data": data}


# ─── Category Mapping ──────────────────────────────────────────────────────────
# Maps Google Places types → TourMate categories
GOOGLE_TYPE_TO_CATEGORY: Dict[str, str] = {
    # Heritage / History
    "tourist_attraction": "heritage",
    "historical_landmark": "heritage",
    "monument": "heritage",
    "museum": "heritage",
    "art_museum": "heritage",
    "history_museum": "heritage",
    "national_monument": "heritage",
    "archaeological_site": "heritage",
    "castle": "heritage",
    "fort": "heritage",
    "ruins": "heritage",
    # Nature
    "park": "nature",
    "national_park": "nature",
    "state_park": "nature",
    "nature_reserve": "nature",
    "botanical_garden": "nature",
    "beach": "nature",
    "waterfall": "nature",
    "wildlife_refuge": "nature",
    "zoo": "nature",
    "aquarium": "nature",
    "campground": "nature",
    "hiking_area": "nature",
    "garden": "nature",
    # Food
    "restaurant": "food",
    "food": "food",
    "cafe": "food",
    "bakery": "food",
    "bar": "food",
    "meal_takeaway": "food",
    "meal_delivery": "food",
    "street_food": "food",
    "fast_food_restaurant": "food",
    "indian_restaurant": "food",
    # Shopping
    "shopping_mall": "shopping",
    "market": "shopping",
    "store": "shopping",
    "clothing_store": "shopping",
    "jewelry_store": "shopping",
    "gift_shop": "shopping",
    "bazaar": "shopping",
    # Culture / Art
    "art_gallery": "culture",
    "cultural_center": "culture",
    "performing_arts_theater": "culture",
    "theater": "culture",
    "library": "culture",
    "stadium": "culture",
    # Religious
    "hindu_temple": "religious",
    "place_of_worship": "religious",
    "mosque": "religious",
    "church": "religious",
    "synagogue": "religious",
    "temple": "religious",
    "shrine": "religious",
    "monastery": "religious",
    "gurdwara": "religious",
    # Adventure
    "amusement_park": "adventure",
    "adventure_sports_center": "adventure",
    "water_park": "adventure",
    "sports_club": "adventure",
    "ski_resort": "adventure",
    # Architecture
    "architecture": "architecture",
    "government_building": "architecture",
    "palace": "architecture",
    "stadium": "architecture",
    # Entertainment
    "movie_theater": "entertainment",
    "night_club": "entertainment",
    "casino": "entertainment",
    "bowling_alley": "entertainment",
    "amusement_center": "entertainment",
}

# TourMate categories → Google Places includedTypes for Nearby Search
CATEGORY_TO_GOOGLE_TYPES: Dict[str, List[str]] = {
    "heritage": ["tourist_attraction", "historical_landmark", "museum", "monument", "national_monument", "archaeological_site"],
    "nature": ["park", "national_park", "beach", "botanical_garden", "nature_reserve", "wildlife_refuge", "waterfall"],
    "food": ["restaurant", "cafe", "bakery", "bar", "food"],
    "culture": ["art_gallery", "cultural_center", "performing_arts_theater", "museum"],
    "shopping": ["shopping_mall", "market", "store"],
    "adventure": ["amusement_park", "adventure_sports_center", "water_park"],
    "religious": ["hindu_temple", "place_of_worship", "mosque", "church", "monastery", "shrine"],
    "architecture": ["tourist_attraction", "historical_landmark"],
    "entertainment": ["movie_theater", "night_club", "amusement_center"],
    "all": ["tourist_attraction", "historical_landmark", "museum", "park", "beach", "restaurant", "hindu_temple", "place_of_worship", "art_gallery", "shopping_mall"],
}

# Default types to use when no category filter is applied
DEFAULT_PLACE_TYPES = [
    "tourist_attraction",
    "historical_landmark",
    "museum",
    "park",
    "hindu_temple",
    "place_of_worship",
    "beach",
    "national_park",
]


def _map_category(google_types: List[str]) -> str:
    """Map list of Google types to the best TourMate category."""
    for t in google_types:
        if t in GOOGLE_TYPE_TO_CATEGORY:
            return GOOGLE_TYPE_TO_CATEGORY[t]
    return "heritage"


def _normalize_place(gplace: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize a Google Places API (New) response object into a
    common NormalizedPlace dict that the cluster engine can use.
    """
    place_id = gplace.get("id") or gplace.get("place_id", "")
    name = gplace.get("displayName", {}).get("text", "") or gplace.get("name", "")
    
    location = gplace.get("location", {})
    lat = location.get("latitude")
    lng = location.get("longitude")
    
    types = gplace.get("types", [])
    category = _map_category(types)
    
    rating = gplace.get("rating")
    address = gplace.get("formattedAddress") or gplace.get("vicinity", "")
    
    # Build Google Maps URL
    maps_url = f"https://www.google.com/maps/place/?q=place_id:{place_id}" if place_id else None
    
    # Photo (first one only if available)
    photo_url = None
    photos = gplace.get("photos", [])
    if photos:
        photo_ref = photos[0].get("name", "")
        if photo_ref and settings.google_maps_api_key:
            photo_url = (
                f"https://places.googleapis.com/v1/{photo_ref}/media"
                f"?maxHeightPx=400&maxWidthPx=400&key={settings.google_maps_api_key}"
            )

    return {
        "id": f"google-{place_id}",
        "source": "google",
        "external_id": place_id,
        "name": name,
        "latitude": lat,
        "longitude": lng,
        # Provide location in the same format as TouristPlaceResponse for compatibility
        "location": {"type": "Point", "coordinates": [lng, lat]} if lat and lng else None,
        "category": {"name": category},
        "category_name": category,
        "rating": rating,
        "address": address,
        "google_maps_url": maps_url,
        "photo_url": photo_url,
        "types": types,
        "description": gplace.get("editorialSummary", {}).get("text", ""),
    }


async def nearby_search(
    lat: float,
    lng: float,
    radius_m: int = 5000,
    included_types: Optional[List[str]] = None,
    max_results: int = 20,
) -> List[Dict[str, Any]]:
    """
    Google Places API (New) — Nearby Search.
    Returns up to max_results normalized places.
    Results are cached for CACHE_TTL_SECONDS.
    """
    api_key = settings.google_maps_api_key
    if not api_key:
        return []

    types = included_types or DEFAULT_PLACE_TYPES
    ck = _cache_key("nearby", lat, lng, radius_m, sorted(types), max_results)
    cached = _cache_get(ck)
    if cached is not None:
        return cached

    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": (
            "places.id,places.displayName,places.location,"
            "places.types,places.rating,places.formattedAddress,"
            "places.photos,places.editorialSummary"
        ),
    }
    body = {
        "includedTypes": types[:10],  # API max is 50 types but we keep it focused
        "maxResultCount": min(max_results, 20),
        "locationRestriction": {
            "circle": {
                "center": {"latitude": lat, "longitude": lng},
                "radius": float(min(radius_m, 50000)),  # API max 50km
            }
        },
        "languageCode": "en",
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=body, headers=headers)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        print(f"[Google Places] Nearby Search error: {e}")
        return []

    raw_places = data.get("places", [])
    normalized = [_normalize_place(p) for p in raw_places]
    # Filter out places with no coordinates
    normalized = [p for p in normalized if p["latitude"] and p["longitude"]]

    _cache_set(ck, normalized)
    return normalized


async def text_search(
    query: str,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    radius_m: int = 50000,
    max_results: int = 20,
) -> List[Dict[str, Any]]:
    """
    Google Places API (New) — Text Search.
    Used for destination search (e.g. "tourist places in Jaipur").
    """
    api_key = settings.google_maps_api_key
    if not api_key:
        return []

    ck = _cache_key("text", query, lat, lng, radius_m, max_results)
    cached = _cache_get(ck)
    if cached is not None:
        return cached

    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": (
            "places.id,places.displayName,places.location,"
            "places.types,places.rating,places.formattedAddress,"
            "places.photos,places.editorialSummary"
        ),
    }
    body: Dict[str, Any] = {
        "textQuery": query,
        "maxResultCount": min(max_results, 20),
        "languageCode": "en",
        # Restrict to India
        "locationBias": {
            "circle": {
                "center": {"latitude": lat if lat else 20.5937, "longitude": lng if lng else 78.9629},
                "radius": float(radius_m),
            }
        } if lat else {
            "rectangle": {
                "low": {"latitude": 6.0, "longitude": 68.0},
                "high": {"latitude": 37.5, "longitude": 97.5},
            }
        },
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=body, headers=headers)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        print(f"[Google Places] Text Search error: {e}")
        return []

    raw_places = data.get("places", [])
    normalized = [_normalize_place(p) for p in raw_places]
    normalized = [p for p in normalized if p["latitude"] and p["longitude"]]

    _cache_set(ck, normalized)
    return normalized


async def get_place_details(place_id: str) -> Optional[Dict[str, Any]]:
    """
    Google Places API (New) — Place Details.
    Returns full details for a single place.
    """
    api_key = settings.google_maps_api_key
    if not api_key:
        return None

    ck = _cache_key("details", place_id)
    cached = _cache_get(ck)
    if cached is not None:
        return cached

    url = f"https://places.googleapis.com/v1/places/{place_id}"
    headers = {
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": (
            "id,displayName,location,types,rating,formattedAddress,"
            "photos,editorialSummary,regularOpeningHours,websiteUri,nationalPhoneNumber"
        ),
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        print(f"[Google Places] Details error: {e}")
        return None

    normalized = _normalize_place(data)
    _cache_set(ck, normalized)
    return normalized


def deduplicate_places(places: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate places by external_id (Google Place ID)."""
    seen = set()
    result = []
    for p in places:
        pid = p.get("external_id") or p.get("id", "")
        if pid not in seen:
            seen.add(pid)
            result.append(p)
    return result


def get_types_for_category(category: str) -> List[str]:
    """Return Google Places types for a given TourMate category."""
    return CATEGORY_TO_GOOGLE_TYPES.get(category.lower(), DEFAULT_PLACE_TYPES)
