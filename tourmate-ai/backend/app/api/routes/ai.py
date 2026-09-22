import uuid
from fastapi import APIRouter, Depends, Request
from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user_dependency
from app.core.db import get_async_db
from app.schemas.auth import UserPublic
from app.schemas.common import Envelope
from app.services.ai_service import get_ai_response, get_grounded_chat_response
from app.services import poi_service
from app.services.rag_service import (
    retrieve_knowledge_chunks,
    handle_route_interception,
    is_opening_hours_query,
    is_pricing_query,
    get_canonical_poi_details,
)
from app.core.limiter import limiter

class ChatMessage(BaseModel):
    role: str # "user" or "model"
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []
    place_id: Optional[str] = None
    language: Optional[str] = 'en'

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

    # 2. Resolve canonical POI context if place_id is provided or POI name mentioned
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

    # 3. Canonical Database Check for Opening Hours or Price queries
    canonical_extra: Optional[dict] = None
    if poi_uuid and (is_opening_hours_query(payload.message) or is_pricing_query(payload.message)):
        canonical_extra = await get_canonical_poi_details(poi_uuid, db=db)

    history_dicts = [{"role": msg.role, "content": msg.content} for msg in payload.history]

    # 4. Retrieve relevant knowledge chunks via pgvector cosine similarity
    retrieved_chunks = await retrieve_knowledge_chunks(
        query=search_query,
        db=db,
        poi_id=poi_uuid,
    )

    # If canonical POI was not in place_id but top retrieved chunk is POI-specific, attempt extra details
    if not canonical_extra and (is_opening_hours_query(payload.message) or is_pricing_query(payload.message)):
        if retrieved_chunks and retrieved_chunks[0].get("poi_id"):
            try:
                top_poi_uuid = uuid.UUID(retrieved_chunks[0]["poi_id"])
                canonical_extra = await get_canonical_poi_details(top_poi_uuid, db=db)
            except Exception:
                pass

    # 5. Formulate grounded response with authority guardrails
    result = get_grounded_chat_response(
        user_message=payload.message,
        history=history_dicts,
        retrieved_chunks=retrieved_chunks,
        language=payload.language or "en",
        canonical_extra=canonical_extra,
    )

    return Envelope(
        success=True,
        data={
            "response": result["response"],
            "answer": result.get("answer", result["response"]),
            "sources": result["sources"],
            "is_grounded": result["is_grounded"],
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
@limiter.limit("10/minute")
async def discover_route(request: Request, payload: DiscoverRequest, current_user: UserPublic = Depends(get_current_user_dependency)):
    prompt = f"I am taking a {payload.mode} trip from {payload.origin} to {payload.destination} ({payload.distance} km) with {payload.stops} stops. Suggest 3 interesting places to discover along the route, categorized by Food, Nature, and Attraction. Keep the response very concise."
    
    ai_text = get_ai_response(prompt, [], None, "en")
    
    return Envelope(success=True, data={"suggestions": ai_text})
