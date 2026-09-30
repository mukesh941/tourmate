"""
Destination Resolver Service for TourMate AI.

Handles:
- Intent detection (itinerary, destination, state/city/POI questions)
- Destination extraction from natural language
- Alias normalization (Bangalore to Bengaluru, Bombay to Mumbai, etc.)
- Canonical location resolution from PostgreSQL (uses state + name fields)
- Foreign-location protection (non-India destinations)
- Destination locking context for multi-turn conversations

This is the single authoritative module for "What place does the user mean?"
"""
import re
import logging
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import select, func, or_, and_, text, case
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.sql.location import Location

logger = logging.getLogger(__name__)

# ── City/Location Name Aliases ────────────────────────────────────────────────
CITY_ALIASES: Dict[str, str] = {
    # Colonial name -> official name
    "bangalore": "Bengaluru",
    "bombay": "Mumbai",
    "calcutta": "Kolkata",
    "madras": "Chennai",
    "cochin": "Kochi",
    "mysore": "Mysuru",
    "trivandrum": "Thiruvananthapuram",
    "pondicherry": "Puducherry",
    "banaras": "Varanasi",
    "benaras": "Varanasi",
    "poona": "Pune",
    "baroda": "Vadodara",
    "gurgaon": "Gurugram",
    # Spelling variants / typos
    "banglore": "Bengaluru",
    "bangaluru": "Bengaluru",
    "bengalore": "Bengaluru",
    "dehli": "Delhi",
    "dilli": "Delhi",
    "new delhi": "Delhi",
    "kolkatta": "Kolkata",
    "kolkota": "Kolkata",
    "hydrabad": "Hyderabad",
    "mubai": "Mumbai",
    "chenai": "Chennai",
    "amrestar": "Amritsar",
    "udaipur": "Udaipur",
    "jaisalmer": "Jaisalmer",
    "jaipur": "Jaipur",
    "varanasi": "Varanasi",
    "lucknow": "Lucknow",
    "agra": "Agra",
    "manali": "Manali",
    "shimla": "Shimla",
    "darjeeling": "Darjeeling",
    "goa": "Goa",
    "rishikesh": "Rishikesh",
    "haridwar": "Haridwar",
    "leh": "Leh",
    "ladakh": "Leh",
    "ooty": "Ooty",
    "munnar": "Munnar",
    "coorg": "Madikeri",
    "kodagu": "Madikeri",
    "kodaikanal": "Kodaikanal",
    "hampi": "Hampi",
    "udupi": "Udupi",
    "mangalore": "Mangaluru",
    "mangaluru": "Mangaluru",
    "hubli": "Hubballi",
    "dharwad": "Dharwad",
    "kochi": "Kochi",
    "thiruvananthapuram": "Thiruvananthapuram",
    "ernakulam": "Kochi",
    "puri": "Puri",
    "bhubaneswar": "Bhubaneswar",
    "guwahati": "Guwahati",
    "shillong": "Shillong",
    "aizawl": "Aizawl",
    "imphal": "Imphal",
    "kohima": "Kohima",
    "itanagar": "Itanagar",
    "patna": "Patna",
    "ranchi": "Ranchi",
    "raipur": "Raipur",
    "bhopal": "Bhopal",
    "indore": "Indore",
    "nagpur": "Nagpur",
    "pune": "Pune",
    "nashik": "Nashik",
    "aurangabad": "Aurangabad",
    "surat": "Surat",
    "ahmedabad": "Ahmedabad",
    "gandhinagar": "Gandhinagar",
    "rajkot": "Rajkot",
    "jodhpur": "Jodhpur",
    "bikaner": "Bikaner",
    "ajmer": "Ajmer",
    "kota": "Kota",
    "chandigarh": "Chandigarh",
    "ludhiana": "Ludhiana",
    "amritsar": "Amritsar",
    "jammu": "Jammu",
    "srinagar": "Srinagar",
    "dehradun": "Dehradun",
    "nainital": "Nainital",
    "mussoorie": "Mussoorie",
    "tirupati": "Tirupati",
    "vijayawada": "Vijayawada",
    "visakhapatnam": "Visakhapatnam",
    "vizag": "Visakhapatnam",
    "warangal": "Warangal",
    "madurai": "Madurai",
    "coimbatore": "Coimbatore",
    "trichy": "Tiruchirappalli",
    "salem": "Salem",
    "tiruchirappalli": "Tiruchirappalli",
    "tanjore": "Thanjavur",
    "thanjavur": "Thanjavur",
    "chikmagalur": "Chikmagalur",
    "chikkamagaluru": "Chikmagalur",
    "kasaragod": "Kasaragod",
    "kannur": "Kannur",
    "calicut": "Kozhikode",
    "kozhikode": "Kozhikode",
    "thrissur": "Thrissur",
    "alappuzha": "Alappuzha",
    "alleppey": "Alappuzha",
    "kollam": "Kollam",
    "varkala": "Varkala",
    "kovalam": "Kovalam",
    "cherrapunji": "Cherrapunjee",
    "cherrapunjee": "Cherrapunjee",
    "dibrugarh": "Dibrugarh",
    "jorhat": "Jorhat",
    "ziro": "Ziro",
    "tawang": "Tawang",
    "diu": "Diu",
    "daman": "Daman",
    "silvassa": "Silvassa",
    "kargil": "Kargil",
    "spiti": "Kaza",
    "majuli": "Majuli",
    "kanyakumari": "Kanyakumari",
    "rameswaram": "Rameswaram",
    "andaman": "Port Blair",
    "neil island": "Neil Island",
    "havelock island": "Havelock Island",
}

FOREIGN_CITIES = frozenset([
    "paris", "london", "new york", "newyork", "tokyo", "dubai", "singapore",
    "bangkok", "berlin", "rome", "amsterdam", "sydney", "toronto", "los angeles",
    "chicago", "washington", "san francisco", "madrid", "barcelona", "vienna",
    "prague", "zurich", "stockholm", "oslo", "seoul", "beijing", "shanghai",
    "hong kong", "taipei", "kuala lumpur", "jakarta", "manila", "cairo",
    "istanbul", "moscow", "johannesburg", "nairobi", "lagos", "accra",
    "buenos aires", "sao paulo", "rio de janeiro", "mexico city", "bogota",
    "lima", "santiago", "cape town", "abu dhabi", "doha", "riyadh",
    "muscat", "karachi", "lahore", "islamabad", "dhaka", "colombo", "kathmandu",
    "kabul", "yangon", "phnom penh", "vientiane", "thimphu",
])

INDIA_STATES = frozenset([
    "andhra pradesh", "arunachal pradesh", "assam", "bihar", "chhattisgarh",
    "goa", "gujarat", "haryana", "himachal pradesh", "jharkhand", "karnataka",
    "kerala", "madhya pradesh", "maharashtra", "manipur", "meghalaya",
    "mizoram", "nagaland", "odisha", "punjab", "rajasthan", "sikkim",
    "tamil nadu", "telangana", "tripura", "uttar pradesh", "uttarakhand",
    "west bengal",
    "andaman and nicobar islands", "chandigarh", "dadra and nagar haveli",
    "daman and diu", "delhi", "jammu and kashmir", "ladakh", "lakshadweep",
    "puducherry",
])

_ITINERARY_PATTERNS = [
    r"\bplan\s+(a\s+)?(trip|tour|visit|holiday|vacation|getaway)\s+to\b",
    r"\b(plan|plan\s+my|help\s+me\s+plan|create|make|build|generate|draft)\s+(a\s+)?(trip|tour|itinerary)\s+(to|for|in|at)\b",
    r"\b(\d+)[- ]day\s+(trip|tour|visit|itinerary|plan)\s+(to|in|at|for)\b",
    r"\b(trip|tour|visit|itinerary|travel)\s+(to|in)\s+\w",
    r"\b(weekend|week[- ]long|day[- ]trip)\s+(to|in|at)\b",
    r"\bgive\s+me\s+(a\s+)?(\d+)[- ]day\b",
    r"\b(what|where)\s+(should|can)\s+i\s+(visit|see|do|go)\s+(in|to|at)\b",
    r"\b(best|top)\s+places\s+to\s+(visit|see|go)\s+(in|to|at)\b",
    r"\btourist\s+places?\s+(in|near|around)\b",
    r"\bthings\s+to\s+do\s+(in|near|around)\b",
    r"\battraction\s*(s)?\s+(in|near)\b",
]

_DESTINATION_EXTRACTION_PATTERNS = [
    r"\b(?:trip|tour|visit|travel|go|going)\s+(?:to|in|at)\s+([A-Za-z][A-Za-z\s]{1,30}?)(?:\s+for|\s+\d|\s+with|$|,|\.)",
    r"\b\d+[- ]day\s+(?:trip|tour|itinerary|visit)\s+(?:to|in|at)\s+([A-Za-z][A-Za-z\s]{1,30}?)(?:\s+for|\s+with|$|,|\.)",
    r"\b(?:places?|attractions?|things?\s+to\s+do|sites?|sights?)\s+(?:in|near|around)\s+([A-Za-z][A-Za-z\s]{1,30}?)(?:\s+for|\s+with|$|,|\.|\?)",
    r"\b(?:visit|see|do|explore)\s+(?:in|to|at)\s+([A-Za-z][A-Za-z\s]{1,30}?)(?:\s+for|\s+with|$|,|\.|\?)",
    r"\b(?:tell|know|learn|show)\s+(?:me\s+)?(?:about|regarding)\s+([A-Za-z][A-Za-z\s]{1,30}?)(?:\s+for|\s+with|$|,|\.|\?)",
    r"\bI\s+(?:want|would\s+like|plan)\s+to\s+(?:visit|go\s+to|travel\s+to)\s+([A-Za-z][A-Za-z\s]{1,30}?)(?:\s+for|\s+with|$|,|\.|\?)",
]


def normalize_location_name(name: str) -> str:
    """Normalize a location name applying alias map."""
    if not name:
        return ""
    clean = name.strip().lower()
    for prefix in ("the ", "a ", "an "):
        if clean.startswith(prefix):
            clean = clean[len(prefix):]
    if clean in CITY_ALIASES:
        return CITY_ALIASES[clean]
    return name.strip()


def is_foreign_location(name: str) -> bool:
    """Returns True if the location name is a well-known non-Indian city."""
    clean = name.strip().lower()
    return clean in FOREIGN_CITIES


def is_itinerary_or_destination_query(message: str) -> bool:
    """Returns True if the message is asking about travel to a specific destination."""
    lower = message.lower()
    return any(re.search(p, lower) for p in _ITINERARY_PATTERNS)


def extract_destination_from_message(message: str) -> Optional[str]:
    """
    Extract the destination name from a natural language message.
    Returns the normalized canonical name or None.
    """
    for pattern in _DESTINATION_EXTRACTION_PATTERNS:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            candidate = match.group(1).strip().rstrip(".,!?")
            noise = {"me", "you", "us", "them", "this", "that", "here", "there",
                     "my", "your", "our", "a", "an", "the", "it", "they"}
            if candidate.lower() not in noise and len(candidate) >= 2:
                return normalize_location_name(candidate)

    lower = message.lower()
    # Sort by length descending to match longest first
    sorted_aliases = sorted(CITY_ALIASES.keys(), key=len, reverse=True)
    for alias in sorted_aliases:
        if re.search(r'\b' + re.escape(alias) + r'\b', lower):
            return CITY_ALIASES[alias]

    return None


def _location_to_dict(loc: Location) -> Dict[str, Any]:
    """Convert a Location ORM object to a standardized dict."""
    return {
        "id": str(loc.id),
        "name": loc.name,
        "canonical_name": loc.canonical_name or loc.name,
        "location_type": loc.location_type,
        "city": loc.city,
        "state": loc.state,
        "district": loc.district,
        "country": loc.country,
        "latitude": loc.latitude,
        "longitude": loc.longitude,
        "parent_id": str(loc.parent_id) if loc.parent_id else None,
        "source": "tourmate_database",
        "resolved": True,
        "is_foreign": False,
    }


async def resolve_destination(
    name: str,
    db: AsyncSession,
    prefer_types: Optional[List[str]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Resolve a destination name to a canonical location record.
    Priority: tourist_destination > city > state > fuzzy match
    """
    if not name or len(name.strip()) < 2:
        return None
        
    if is_foreign_location(name):
        return None

    normalized = normalize_location_name(name)
    search_names = list(dict.fromkeys([normalized, name.strip()]))  # deduplicated, order preserved

    preferred_types = prefer_types or ["tourist_destination", "city", "state", "town", "district"]

    # 1. Exact name match by preferred type order
    for search_name in search_names:
        for loc_type in preferred_types:
            stmt = (
                select(Location)
                .where(
                    and_(
                        func.lower(Location.name) == search_name.lower(),
                        Location.location_type == loc_type,
                    )
                )
                .limit(1)
            )
            result = await db.execute(stmt)
            loc = result.scalar_one_or_none()
            if loc:
                return _location_to_dict(loc)

    # 2. Exact name match across all types, ordered by type priority
    for search_name in search_names:
        stmt = (
            select(Location)
            .where(func.lower(Location.name) == search_name.lower())
            .order_by(
                case(
                    (Location.location_type == "tourist_destination", 1),
                    (Location.location_type == "city", 2),
                    (Location.location_type == "state", 3),
                    else_=4,
                )
            )
            .limit(1)
        )
        result = await db.execute(stmt)
        loc = result.scalar_one_or_none()
        if loc:
            return _location_to_dict(loc)

    # 3. canonical_name match
    for search_name in search_names:
        stmt = (
            select(Location)
            .where(func.lower(Location.canonical_name) == search_name.lower())
            .limit(1)
        )
        result = await db.execute(stmt)
        loc = result.scalar_one_or_none()
        if loc:
            return _location_to_dict(loc)

    # 4. ILIKE match
    for search_name in search_names:
        pattern = f"%{search_name}%"
        stmt = (
            select(Location)
            .where(
                or_(
                    Location.name.ilike(pattern),
                    Location.city.ilike(pattern),
                    Location.canonical_name.ilike(pattern),
                )
            )
            .order_by(
                case(
                    (Location.location_type == "tourist_destination", 1),
                    (Location.location_type == "city", 2),
                    (Location.location_type == "state", 3),
                    else_=4,
                )
            )
            .limit(1)
        )
        result = await db.execute(stmt)
        loc = result.scalar_one_or_none()
        if loc:
            return _location_to_dict(loc)

    # 5. State name match
    for search_name in search_names:
        stmt = (
            select(Location)
            .where(
                and_(
                    or_(
                        func.lower(Location.name) == search_name.lower(),
                        func.lower(Location.state) == search_name.lower(),
                    ),
                    Location.location_type == "state",
                )
            )
            .limit(1)
        )
        result = await db.execute(stmt)
        loc = result.scalar_one_or_none()
        if loc:
            return _location_to_dict(loc)

    return None


async def get_state_record(state_name: str, db: AsyncSession) -> Optional[Dict[str, Any]]:
    """Retrieve the state-level location record by state name."""
    stmt = (
        select(Location)
        .where(
            and_(
                Location.location_type == "state",
                or_(
                    func.lower(Location.name) == state_name.lower(),
                    func.lower(Location.state) == state_name.lower(),
                ),
            )
        )
        .limit(1)
    )
    result = await db.execute(stmt)
    loc = result.scalar_one_or_none()
    return _location_to_dict(loc) if loc else None


async def get_state_locations(
    state_name: str,
    db: AsyncSession,
    location_types: Optional[List[str]] = None,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """
    Get all locations in a state using the `state` column.
    Ordered: tourist_destination first, then city.
    """
    where_clauses = [func.lower(Location.state) == state_name.lower()]
    if location_types:
        where_clauses.append(Location.location_type.in_(location_types))

    stmt = (
        select(Location)
        .where(and_(*where_clauses))
        .order_by(
            case(
                (Location.location_type == "tourist_destination", 1),
                (Location.location_type == "city", 2),
                else_=3,
            )
        )
        .limit(limit)
    )
    result = await db.execute(stmt)
    locs = result.scalars().all()
    return [_location_to_dict(loc) for loc in locs]


async def find_nearby_locations(
    latitude: float,
    longitude: float,
    radius_km: float,
    db: AsyncSession,
    location_types: Optional[List[str]] = None,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """
    Find locations within radius_km of (latitude, longitude) using Haversine.
    Results ordered by distance ascending. Strictly enforces radius.
    """
    type_filter = ""
    params: Dict[str, Any] = {
        "lat": latitude,
        "lng": longitude,
        "radius_km": radius_km,
        "limit": limit,
    }

    if location_types:
        type_filter = "AND location_type = ANY(:types)"
        params["types"] = location_types

    haversine_sql = text(f"""
        SELECT
            id, name, canonical_name, location_type, city, state, district, country,
            latitude, longitude, parent_id,
            (
                6371 * acos(LEAST(1.0,
                    cos(radians(:lat)) * cos(radians(latitude)) *
                    cos(radians(longitude) - radians(:lng)) +
                    sin(radians(:lat)) * sin(radians(latitude))
                ))
            ) AS distance_km
        FROM locations
        WHERE latitude IS NOT NULL
          AND longitude IS NOT NULL
          AND latitude != 0
          AND longitude != 0
          {type_filter}
        HAVING (
            6371 * acos(LEAST(1.0,
                cos(radians(:lat)) * cos(radians(latitude)) *
                cos(radians(longitude) - radians(:lng)) +
                sin(radians(:lat)) * sin(radians(latitude))
            ))
        ) <= :radius_km
        ORDER BY distance_km ASC
        LIMIT :limit
    """)

    try:
        result = await db.execute(haversine_sql, params)
        rows = result.fetchall()
        return [
            {
                "id": str(row.id),
                "name": row.name,
                "canonical_name": row.canonical_name or row.name,
                "location_type": row.location_type,
                "city": row.city,
                "state": row.state,
                "district": row.district,
                "country": row.country,
                "latitude": row.latitude,
                "longitude": row.longitude,
                "distance_km": round(float(row.distance_km), 2),
                "source": "tourmate_database",
            }
            for row in rows
        ]
    except Exception as e:
        logger.warning("Haversine nearby search failed: %s", e)
        return []


def detect_query_intent(message: str) -> Dict[str, Any]:
    """
    Detects the high-level intent of a travel query.
    Returns dict with intent, destination, days, state, is_foreign.
    """
    lower = message.lower()
    result: Dict[str, Any] = {
        "intent": "general",
        "destination": None,
        "days": None,
        "state": None,
        "is_foreign": False,
    }

    day_match = re.search(r'\b(\d+)[- ]day', lower)
    if day_match:
        result["days"] = int(day_match.group(1))

    if is_itinerary_or_destination_query(message):
        result["intent"] = "itinerary"

    for state in INDIA_STATES:
        if re.search(r'\b' + re.escape(state) + r'\b', lower):
            result["state"] = state
            if result["intent"] == "general":
                result["intent"] = "state_query"
            break

    dest = extract_destination_from_message(message)
    if dest:
        result["destination"] = dest
        if is_foreign_location(dest):
            result["is_foreign"] = True

    if re.search(r'\b(hotel|hotels|accommodation|stay|lodge)\b', lower):
        if result["intent"] == "general":
            result["intent"] = "hotel"

    if re.search(r'\b(guide|local expert|local guide)\b', lower):
        if result["intent"] == "general":
            result["intent"] = "guide"

    return result


async def full_destination_resolution(
    message: str,
    db: AsyncSession,
    session_destination: Optional[Dict[str, Any]] = None,
) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
    """
    Main entry point for chatbot destination resolution.

    Returns: (resolved_location, intent_info)
    """
    intent = detect_query_intent(message)

    # Session lock: re-use locked destination for follow-up messages
    if session_destination and not intent.get("destination") and not intent.get("state"):
        return session_destination, intent

    dest_name = intent.get("destination") or intent.get("state")
    if not dest_name:
        return None, intent

    # Foreign location protection
    if is_foreign_location(dest_name):
        foreign_loc = {
            "id": None,
            "name": dest_name,
            "country": "Unknown (foreign)",
            "is_foreign": True,
            "resolved": False,
            "source": "foreign_detection",
        }
        intent["is_foreign"] = True
        return foreign_loc, intent

    resolved = await resolve_destination(dest_name, db)
    if resolved:
        country = (resolved.get("country") or "").lower()
        if country and "india" not in country:
            resolved["is_foreign"] = True
            intent["is_foreign"] = True
        else:
            resolved["is_foreign"] = False

    return resolved, intent