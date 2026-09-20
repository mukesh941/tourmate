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
from app.services.rag_service import retrieve_knowledge_chunks
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
    # Resolve canonical POI context if place_id is a valid UUID
    poi_uuid: Optional[uuid.UUID] = None
    search_query = payload.message
    if payload.place_id:
        try:
            parsed = uuid.UUID(payload.place_id)
            poi = await poi_service.get_poi_by_id(str(parsed), db=db)
            if poi:
                poi_uuid = parsed
                if poi.name.lower() not in payload.message.lower():
                    search_query = f"{poi.name}: {payload.message}"
        except (ValueError, TypeError):
            poi_uuid = None

    history_dicts = [{"role": msg.role, "content": msg.content} for msg in payload.history]

    # Retrieve relevant knowledge chunks via pgvector cosine similarity
    retrieved_chunks = await retrieve_knowledge_chunks(
        query=search_query,
        db=db,
        poi_id=poi_uuid,
    )

    # Formulate grounded response with authority guardrails
    result = get_grounded_chat_response(
        user_message=payload.message,
        history=history_dicts,
        retrieved_chunks=retrieved_chunks,
        language=payload.language or "en",
    )

    return Envelope(
        success=True,
        data={
            "response": result["response"],
            "sources": result["sources"],
            "is_grounded": result["is_grounded"],
        },
    )

from fastapi import UploadFile, File
from app.services.ai_service import predict_landmark_from_image

@router.post("/recognize-landmark", response_model=Envelope[dict])
@limiter.limit("10/minute")
async def recognize_landmark(
    request: Request,
    file: UploadFile = File(...),
    current_user: UserPublic = Depends(get_current_user_dependency)
):
    try:
        image_bytes = await file.read()
        result = predict_landmark_from_image(image_bytes)
        return Envelope(success=True, data=result)
    except Exception as e:
        print(f"Error predicting landmark: {e}")
        return Envelope(success=False, error="Failed to recognize landmark. Please try again.")

@router.post("/discover", response_model=Envelope[dict])
@limiter.limit("10/minute")
async def discover_route(request: Request, payload: DiscoverRequest, current_user: UserPublic = Depends(get_current_user_dependency)):
    prompt = f"I am taking a {payload.mode} trip from {payload.origin} to {payload.destination} ({payload.distance} km) with {payload.stops} stops. Suggest 3 interesting places to discover along the route, categorized by Food, Nature, and Attraction. Keep the response very concise."
    
    ai_text = get_ai_response(prompt, [], None, "en")
    
    return Envelope(success=True, data={"suggestions": ai_text})
