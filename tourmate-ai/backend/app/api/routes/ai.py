import uuid
import logging
from fastapi import APIRouter, Depends, Request
from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user_dependency
from app.core.db import get_async_db
from app.schemas.auth import UserPublic
from app.schemas.common import Envelope
from app.services.ai_service import get_ai_response, get_grounded_chat_response, discover_places_along_route
from app.services import poi_service
from app.services.rag_service import (
    retrieve_knowledge_chunks,
    handle_route_interception,
    is_opening_hours_query,
    is_pricing_query,
    get_canonical_poi_details,
)
from app.core.limiter import limiter

logger = logging.getLogger(__name__)

class ChatMessage(BaseModel):
    role: str # "user" or "model"
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []
    place_id: Optional[str] = None
    language: Optional[str] = 'en'
    # Optional user coordinates for "near me" queries
    user_lat: Optional[float] = None
    user_lng: Optional[float] = None

class DiscoverRequest(BaseModel):
    origin: str
    destination: str
    mode: str
    stops: int
    distance: float

router = APIRouter(prefix="/ai", tags=["ai"])

@router.post("/chat", response_model=Envelope[dict])
@limiter.limit("20/minute")
async def chat_endpoint(
    request: Request,
    payload: ChatRequest,
    current_user: UserPublic = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_async_db),
):
    # 1. Authoritative Route / Distance Query Interception (Phase 4 Authority)
    route_result = await handle_route_interception(payload.message, db=db)
    if route_result is not None:
        return Envelope(
            success=True,
            data={
                "response": route_result["response"],
                "answer": route_result["answer"],
                "sources": route_result["sources"],
                "is_grounded": route_result["is_grounded"],
            },
        )

    # ──────────────────────────────────────────────────────────────────────────
    # 2. NEARBY SEARCH FLOW
    # Detect if this is a "find X near Y" / "near me" type query.
    # If yes, resolve location + search for real nearby places via Google Places.
    # This runs BEFORE RAG to avoid the bug where zero local POIs = "unknown location".
    # ──────────────────────────────────────────────────────────────────────────
    from app.services.location_service import is_nearby_search_intent, resolve_location, extract_location_from_query_regex
    from app.services.google_places_service import detect_category_from_query, search_nearby_for_chat

    nearby_data = None  # Will hold the full nearby search result set if triggered

    if is_nearby_search_intent(payload.message):
        detected_category = detect_category_from_query(payload.message) or "tourist"
        resolved_loc = None

        # Handle "near me" — use user-provided coordinates if available
        lower_msg = payload.message.lower()
        is_near_me = "near me" in lower_msg or "around me" in lower_msg

        if is_near_me and payload.user_lat is not None and payload.user_lng is not None:
            resolved_loc = {
                "query": "near me",
                "resolved": True,
                "source": "user_device",
                "name": "Your current location",
                "latitude": payload.user_lat,
                "longitude": payload.user_lng,
            }
        elif is_near_me:
            # Cannot resolve "me" without coordinates — give a helpful prompt
            near_me_msg = (
                "To find places near you, I need your current location. "
                "Please enable location permissions in your browser, or specify a city "
                "or neighborhood (for example: 'cafes near RR Layout')."
            )
            return Envelope(
                success=True,
                data={
                    "response": near_me_msg,
                    "answer": near_me_msg,
                    "sources": [],
                    "is_grounded": True,
                    "intent": "nearby_search",
                    "category": detected_category,
                },
            )
        else:
            # Resolve the named location
            resolved_loc = await resolve_location(payload.message, db)

        if resolved_loc and resolved_loc.get("latitude") and resolved_loc.get("longitude"):
            lat = float(resolved_loc["latitude"])
            lng = float(resolved_loc["longitude"])
            loc_name = resolved_loc.get("name") or resolved_loc.get("query", "the location")

            # Run nearby search
            nearby_places = []
            try:
                nearby_places = await search_nearby_for_chat(
                    lat=lat,
                    lng=lng,
                    category=detected_category,
                    radius_m=5000,
                    max_results=10,
                )
            except Exception as e:
                logger.warning("Nearby search failed for '%s': %s", loc_name, e)

            nearby_data = {
                "resolved_loc": resolved_loc,
                "category": detected_category,
                "places": nearby_places,
                "location_name": loc_name,
            }

        elif resolved_loc is not None and not resolved_loc.get("latitude"):
            # Location resolved but no coordinates (rare edge case)
            nearby_data = {
                "resolved_loc": resolved_loc,
                "category": detected_category,
                "places": [],
                "location_name": resolved_loc.get("name", "the location"),
            }
        else:
            # Location could NOT be resolved at all
            regex_loc = extract_location_from_query_regex(payload.message)
            loc_hint = f"'{regex_loc}'" if regex_loc else "that location"
            unresolved_msg = (
                f"I couldn't find {loc_hint} in my map data. "
                f"Please check the spelling or try a nearby city name "
                f"(for example: 'cafes near Bengaluru')."
            )
            return Envelope(
                success=True,
                data={
                    "response": unresolved_msg,
                    "answer": unresolved_msg,
                    "sources": [],
                    "is_grounded": True,
                    "intent": "nearby_search",
                    "category": detected_category,
                },
            )

    # If we have nearby_data, use the grounded nearby response flow
    if nearby_data is not None:
        history_dicts = [{
            "role": msg.role, "content": msg.content
        } for msg in payload.history]

        result = get_grounded_chat_response(
            user_message=payload.message,
            history=history_dicts,
            retrieved_chunks=[],
            language=payload.language or "en",
            canonical_extra=None,
            resolved_loc=nearby_data["resolved_loc"],
            nearby_places=nearby_data["places"],
            detected_category=nearby_data["category"],
        )

        # Build sources from nearby places
        nearby_sources = []
        for p in nearby_data["places"][:5]:
            nearby_sources.append({
                "id": p.get("id", ""),
                "title": p.get("name", ""),
                "source": p.get("source", "google"),
                "poi_name": p.get("name"),
                "similarity": 1.0,
                "address": p.get("address"),
                "rating": p.get("rating"),
                "distance_km": p.get("distance_km"),
                "google_maps_url": p.get("google_maps_url"),
            })

        return Envelope(
            success=True,
            data={
                "response": result["response"],
                "answer": result.get("answer", result["response"]),
                "sources": nearby_sources,
                "is_grounded": True,
                "intent": "nearby_search",
                "category": nearby_data["category"],
                "location": {
                    "name": nearby_data["resolved_loc"].get("name"),
                    "lat": nearby_data["resolved_loc"].get("latitude"),
                    "lng": nearby_data["resolved_loc"].get("longitude"),
                    "source": nearby_data["resolved_loc"].get("source"),
                },
                "results": [
                    {
                        "name": p.get("name"),
                        "category": p.get("category_name") or nearby_data["category"],
                        "address": p.get("address"),
                        "latitude": p.get("latitude"),
                        "longitude": p.get("longitude"),
                        "rating": p.get("rating"),
                        "distance_km": p.get("distance_km"),
                        "source": p.get("source"),
                        "google_maps_url": p.get("google_maps_url"),
                        "photo_url": p.get("photo_url"),
                    }
                    for p in nearby_data["places"]
                ],
            },
        )

    # ──────────────────────────────────────────────────────────────────────────
    # 3. STANDARD RAG + AI FLOW (for non-nearby queries)
    # ──────────────────────────────────────────────────────────────────────────

    # Resolve canonical POI context if place_id is provided
    poi_uuid: Optional[uuid.UUID] = None
    poi_name: Optional[str] = None
    search_query = payload.message

    if payload.place_id:
        try:
            parsed = uuid.UUID(payload.place_id)
            poi = await poi_service.get_poi_by_id(str(parsed), db=db)
            if poi:
                poi_uuid = parsed
                poi_name = poi.name
                if poi.name.lower() not in payload.message.lower():
                    search_query = f"{poi.name}: {payload.message}"
        except (ValueError, TypeError):
            poi_uuid = None

    # 4. Canonical Database Check for Opening Hours or Price queries
    canonical_extra: Optional[dict] = None
    if poi_uuid and (is_opening_hours_query(payload.message) or is_pricing_query(payload.message)):
        canonical_extra = await get_canonical_poi_details(poi_uuid, db=db)

    history_dicts = [{"role": msg.role, "content": msg.content} for msg in payload.history]

    # ── NEW: Use destination_resolver for intent-aware geographic filtering ──
    from app.services.destination_resolver import (
        full_destination_resolution,
        is_foreign_location,
        get_state_locations,
        INDIA_STATES,
    )
    from app.services.location_service import resolve_location

    resolved_loc = None
    location_name_for_filter = None
    location_id_for_filter = None
    location_state_for_filter = None

    # Try the new resolver first (handles itinerary queries, aliases, etc.)
    try:
        # Extract session_destination from previous user messages
        session_dest = None
        if payload.history:
            for msg_item in reversed(payload.history):
                if msg_item.role == "user":
                    res_tuple = await full_destination_resolution(msg_item.content, db)
                    if res_tuple and res_tuple[0]:
                        if not res_tuple[0].get("is_foreign"):
                            session_dest = res_tuple[0]
                            break
                        
        dest_resolved, intent_info = await full_destination_resolution(payload.message, db, session_destination=session_dest)
        if dest_resolved and not dest_resolved.get("is_foreign"):
            resolved_loc = dest_resolved
            # Use state for filtering when we have a state-level or city-level query
            location_state_for_filter = dest_resolved.get("state")
            location_name_for_filter = dest_resolved.get("name")
            location_id_for_filter = dest_resolved.get("id")
        elif dest_resolved and dest_resolved.get("is_foreign"):
            foreign_name = dest_resolved.get("name", "this destination")
            fallback_msg = (
                f"TourMate currently focuses on travel planning within India. "
                f"I don't have verified data for {foreign_name}. "
                f"I can help you plan amazing trips across Indian states, cities and tourist destinations!"
            )
            return Envelope(
                success=True,
                data={
                    "response": fallback_msg,
                    "answer": fallback_msg,
                    "sources": [],
                    "is_grounded": True,
                }
            )
    except Exception as e:
        logger.warning("destination_resolver failed, falling back to legacy resolve_location: %s", e)

    # Fallback to legacy resolve_location if destination_resolver didn't find anything
    if not resolved_loc:
        try:
            legacy_loc = await resolve_location(payload.message, db)
            if legacy_loc:
                country = (legacy_loc.get("country") or "").lower()
                if country and "india" not in country:
                    fallback_msg = f"I currently focus on travel information within India. I don't have verified TourMate data for {legacy_loc.get('name')}."
                    return Envelope(
                        success=True,
                        data={
                            "response": fallback_msg,
                            "answer": fallback_msg,
                            "sources": [],
                            "is_grounded": True,
                        }
                    )
                resolved_loc = legacy_loc
                location_name_for_filter = legacy_loc.get("city") or legacy_loc.get("name")
                location_id_for_filter = legacy_loc.get("location_id")
                location_state_for_filter = legacy_loc.get("state")
        except Exception as e:
            logger.warning("Legacy resolve_location also failed: %s", e)

    # 5. Retrieve relevant knowledge chunks via pgvector cosine similarity
    # Use state filter for geographic grounding when location_id is unavailable
    retrieved_chunks = await retrieve_knowledge_chunks(
        query=search_query,
        db=db,
        poi_id=poi_uuid,
        location_name=location_name_for_filter,
        location_id=location_id_for_filter,
        location_state=location_state_for_filter,
    )

    # If canonical POI was not in place_id but top retrieved chunk is POI-specific, attempt extra details
    if not canonical_extra and (is_opening_hours_query(payload.message) or is_pricing_query(payload.message)):
        if retrieved_chunks and retrieved_chunks[0].get("poi_id"):
            try:
                top_poi_uuid = uuid.UUID(retrieved_chunks[0]["poi_id"])
                canonical_extra = await get_canonical_poi_details(top_poi_uuid, db=db)
            except Exception:
                pass

    # 6. Formulate grounded response with authority guardrails
    result = get_grounded_chat_response(
        user_message=payload.message,
        history=history_dicts,
        retrieved_chunks=retrieved_chunks,
        language=payload.language or "en",
        canonical_extra=canonical_extra,
        resolved_loc=resolved_loc,
    )

    return Envelope(
        success=True,
        data={
            "response": result["response"],
            "answer": result.get("answer", result["response"]),
            "sources": result["sources"],
            "is_grounded": result["is_grounded"],
            "intent": intent_info.get("intent") if 'intent_info' in dir() else None,
            "resolved_destination": {
                "name": resolved_loc.get("name"),
                "state": resolved_loc.get("state"),
                "type": resolved_loc.get("location_type"),
            } if resolved_loc else None,
        },
    )


from fastapi import UploadFile, File
from app.api.deps import get_optional_current_user
from app.services.ai_service import predict_landmark_from_image
import logging

logger = logging.getLogger(__name__)

@router.post("/recognize-landmark", response_model=Envelope[dict])
@limiter.limit("20/minute")
async def recognize_landmark(
    request: Request,
    file: UploadFile = File(...),
    current_user: Optional[UserPublic] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    if not file or not file.filename:
        return Envelope(success=False, error="No image file provided.")

    content_type = (file.content_type or "").lower()
    allowed_types = ("image/jpeg", "image/jpg", "image/png", "image/webp", "image/bmp", "image/gif")
    allowed_exts = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif")
    if content_type and content_type not in allowed_types and not file.filename.lower().endswith(allowed_exts):
        return Envelope(
            success=False,
            error="Unsupported image format. Please upload a JPEG, PNG, or WebP image."
        )

    try:
        image_bytes = await file.read()
        if not image_bytes or len(image_bytes) == 0:
            return Envelope(success=False, error="Uploaded image file is empty.")
        if len(image_bytes) > 15 * 1024 * 1024:
            return Envelope(success=False, error="Image file too large. Maximum supported size is 15MB.")

        result = await predict_landmark_from_image(image_bytes, db=db)
        return Envelope(success=True, data=result)
    except Exception as e:
        logger.error("Error recognizing landmark: %s", e)
        return Envelope(
            success=False,
            error="Failed to analyze the image. Please ensure it is a valid photo and try again."
        )

@router.post("/discover", response_model=Envelope[dict])
@limiter.limit("20/minute")
async def discover_route(
    request: Request,
    payload: DiscoverRequest,
    current_user: Optional[UserPublic] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    suggestions = await discover_places_along_route(
        origin=payload.origin,
        destination=payload.destination,
        mode=payload.mode,
        stops_count=payload.stops,
        distance_km=payload.distance,
        db=db,
    )
    return Envelope(success=True, data={"suggestions": suggestions})

