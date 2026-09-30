"""
Location service for querying canonical PostgreSQL locations and geocoding.
"""
import re
import json
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.sql.location import Location
from app.core.config import settings

logger = logging.getLogger(__name__)

# ─── Common preposition patterns used to extract location from queries ──────────
_NEAR_PATTERNS = [
    re.compile(r"\bnear\s+(.+?)(?:\s*$|\s+\b(?:for|please|and|,))", re.IGNORECASE),
    re.compile(r"\baround\s+(.+?)(?:\s*$|\s+\b(?:for|please|and|,))", re.IGNORECASE),
    re.compile(r"\bin\s+(.+?)(?:\s*$|\s+\b(?:for|please|and|,))", re.IGNORECASE),
    re.compile(r"\bat\s+(.+?)(?:\s*$|\s+\b(?:for|please|and|,))", re.IGNORECASE),
    re.compile(r"\bclose to\s+(.+?)(?:\s*$|\s+\b(?:for|please|and|,))", re.IGNORECASE),
    re.compile(r"\bwithin\s+\S+\s+(?:km|miles?)?\s+of\s+(.+?)(?:\s*$|\s+\b(?:for|please|and|,))", re.IGNORECASE),
]

def _apply_typomap(text: str) -> str:
    """
    Normalizes common alternate names for Indian cities.
    Extensible dictionary mapping approach.
    """
    clean_text = text.lower().strip()
    typomap = {
        "bangalore": "bengaluru",
        "bombay": "mumbai",
        "calcutta": "kolkata",
        "madras": "chennai",
        "delhi": "new delhi",
        "dehli": "new delhi",
        "pondicherry": "puducherry",
        "trivandrum": "thiruvananthapuram",
        "cochin": "kochi",
        "banaras": "varanasi",
        "benaras": "varanasi",
        "baroda": "vadodara",
        "poona": "pune",
        "mysore": "mysuru",
        "gurgaon": "gurugram"
    }
    return typomap.get(clean_text, clean_text)


def is_nearby_search_intent(message: str) -> bool:
    """
    Returns True if the user message appears to be requesting nearby places.
    Example triggers:
      - "cafe near RR Layout"
      - "restaurants around Bengaluru"
      - "hotels near me"
      - "tourist places near Delhi"
      - "places near me"
      - "find food near me"
    IMPORTANT: Should NOT trigger for general questions like:
      - "What are the best historical places in Delhi?"
      - "Tell me about places in Goa"
      - "What is near the Taj Mahal?" (ambiguous but handled)
    """
    lower = message.lower()

    # --- Negative filters: these are NOT nearby-search queries ---
    general_question_prefixes = [
        "what are the best",
        "what is the best",
        "tell me about",
        "how to reach",
        "how far is",
        "what is the history",
        "can you tell me",
        "i want to know",
        "what is",
    ]
    for prefix in general_question_prefixes:
        if lower.startswith(prefix):
            return False

    patterns = [
        r"\bnear\s+me\b",
        r"\baround\s+me\b",
        r"\bfind\s+\w+\s+near\b",
        r"\bshow\s+\w+\s+near\b",
        r"\bplaces?\s+near\s+\w",
        r"\bplaces?\s+around\s+\w",
        # POI-type + near/around + location pattern:
        r"\b(cafe|cafes|caf\u00e9|coffee|restaurant|restaurants|hotel|hotels|resort|hostel|food|tourist|sightseeing|attraction|monument|temple|museum|park|beach|bar|shop|mall)s?\s+(near|around|close to|in)\s+\w",
        r"\bclose\s+to\s+\w",
        r"\bwithin\s+\d",
    ]
    return any(re.search(p, lower) for p in patterns)


def extract_location_from_query_regex(query: str) -> Optional[str]:
    """
    Use regex patterns to extract the location name from a nearby-search query.
    For example:
      "cafe near RR Layout"       → "RR Layout"
      "restaurants near Bengaluru" → "Bengaluru"
      "hotels near me"             → "me"  (caller must handle "me" specially)
    Returns None if no pattern matches.
    """
    # Try each pattern and return the first match
    for pat in _NEAR_PATTERNS:
        m = pat.search(query)
        if m:
            loc = m.group(1).strip().rstrip(".,!?")
            if loc and len(loc) >= 2:
                return loc
    return None


async def search_postgres_locations(query: str, db: AsyncSession, limit: int = 10, exact_only: bool = False) -> List[Dict[str, Any]]:
    """Search canonical locations in PostgreSQL by name, city, state, or country."""
    if not query or len(query.strip()) < 2:
        return []

    exact_stmt = (
        select(Location)
        .where(
            or_(
                func.lower(Location.name) == query.strip().lower(),
                func.lower(Location.city) == query.strip().lower(),
                func.lower(Location.canonical_name) == query.strip().lower(),
            )
        )
        .limit(limit)
    )
    result = await db.execute(exact_stmt)
    locations = result.scalars().all()
    
    if not locations and not exact_only:
        pattern = f"%{query.strip().lower()}%"
        stmt = (
            select(Location)
            .where(
                or_(
                    func.lower(Location.name).like(pattern),
                    func.lower(Location.city).like(pattern),
                    func.lower(Location.state).like(pattern),
                    func.lower(Location.country).like(pattern),
                    func.lower(Location.address).like(pattern),
                )
            )
            .limit(limit)
        )
        result = await db.execute(stmt)
        locations = result.scalars().all()

    return [
        {
            "id": str(loc.id),
            "name": loc.name,
            "canonical_name": getattr(loc, "canonical_name", ""),
            "type": "location",
            "location_type": getattr(loc, "location_type", "poi"),
            "city": loc.city,
            "state": loc.state,
            "country": loc.country,
            "lat": loc.latitude,
            "lng": loc.longitude,
            "address": loc.address,
        }
        for loc in locations
    ]


async def geocode_with_nominatim(location_name: str, country_bias: str = "India") -> Optional[Dict[str, Any]]:
    """
    Geocode a location name using OpenStreetMap Nominatim.
    Returns a dict with lat/lng and metadata, or None on failure.

    Args:
        location_name: The location to geocode.
        country_bias: Appended to the query to bias geocoding (default: India).
                      Pass None or empty string to disable.

    IMPORTANT: Always use a descriptive User-Agent per Nominatim usage policy.
    """
    import httpx
    if not location_name or len(location_name.strip()) < 2:
        return None

    # Build the query with country bias for short/ambiguous names
    query = location_name.strip()
    if country_bias and len(query.split()) <= 4:
        # Append country bias for short queries to avoid wrong-country matches
        if country_bias.lower() not in query.lower():
            query = query + ", " + country_bias

    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": query,
        "format": "json",
        "limit": 1,
        "addressdetails": 1,
    }
    headers = {"User-Agent": "TourMate-AI/1.0 (travel assistant; contact: support@tourmate.app)"}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        if not data or len(data) == 0:
            logger.info("Nominatim returned no results for '%s'", query)
            return None

        p = data[0]
        addr = p.get("address", {})
        return {
            "name": p.get("name") or location_name,
            "display_name": p.get("display_name", ""),
            "lat": float(p.get("lat", 0)),
            "lng": float(p.get("lon", 0)),
            "city": addr.get("city") or addr.get("town") or addr.get("village") or addr.get("suburb") or "",
            "state": addr.get("state") or "",
            "country": addr.get("country") or "",
            "source": "openstreetmap",
        }
    except Exception as e:
        logger.warning("Nominatim geocoding failed for '%s': %s", query, e)
        return None


async def resolve_location_name(
    loc_name: str,
    db: AsyncSession,
) -> Optional[Dict[str, Any]]:
    """
    Resolves a plain location name string to coordinates using this priority:
    1. PostgreSQL canonical locations
    2. OpenStreetMap Nominatim

    Returns a resolved location dict or None.
    Does NOT crash the chat endpoint on failure.

    This is called AFTER the location name is extracted from the user query.
    """
    from app.services.geocoding_service import resolve_location as geocoder_resolve
    return await geocoder_resolve(loc_name, db)


async def resolve_location(user_message: str, db: AsyncSession) -> Optional[Dict[str, Any]]:
    """
    Extracts location from user query and resolves it against:
    1. Regex extraction (for "near X" patterns)
    2. TourMate database
    3. Google Places
    4. OpenStreetMap / Nominatim

    This is the main entry point called from the chat endpoint.
    """
    # Fast path 1: try regex-based location extraction for "near X" style queries
    regex_loc = extract_location_from_query_regex(user_message)
    if regex_loc and regex_loc.lower() != "me":
        result = await resolve_location_name(regex_loc, db)
        if result:
            return result

    # Fast path 2 removed: We rely on Gemini and DB for extensible normalization

    # Slow path: use Gemini to extract location name
    if not settings.gemini_api_key:
        # Cannot extract via AI, try regex on the whole message again
        if regex_loc:
            return await resolve_location_name(regex_loc, db)
        return None

    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.gemini_api_key)
        model_name = getattr(settings, "gemini_model", "gemini-1.5-flash")
        model = genai.GenerativeModel(model_name)
        prompt = (
            f'Extract the specific location or neighborhood name from this travel query. '
            f'Return strictly JSON {{"location": "extracted name"}} or {{"location": ""}} if none found. '
            f'Query: "{user_message}"'
        )
        res = model.generate_content(prompt)
        text = res.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]

        extracted = json.loads(text.strip())
        loc_name = (extracted.get("location") or "").strip()

        if not loc_name or loc_name.lower() in ("me", "here", "nearby"):
            return None

        return await resolve_location_name(loc_name, db)

    except Exception as e:
        logger.warning("Gemini location extraction failed: %s", e)
        # Last resort: if regex gave us something, try to resolve it
        if regex_loc:
            return await resolve_location_name(regex_loc, db)
        return None

