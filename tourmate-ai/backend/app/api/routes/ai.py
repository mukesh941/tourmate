from fastapi import APIRouter, Depends, Request
from typing import List, Optional
from pydantic import BaseModel
from app.api.deps import get_current_user_dependency
from app.schemas.auth import UserPublic
from app.schemas.common import Envelope
from app.services.ai_service import get_ai_response
from app.services.place_service import get_place
from app.core.limiter import limiter

class ChatMessage(BaseModel):
    role: str # "user" or "model"
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []
    place_id: Optional[str] = None
    language: Optional[str] = 'en'

router = APIRouter(prefix="/ai", tags=["ai"])

@router.post("/chat", response_model=Envelope[dict])
@limiter.limit("20/minute")
async def chat_endpoint(request: Request, payload: ChatRequest, current_user: UserPublic = Depends(get_current_user_dependency)):
    context = None
    if payload.place_id:
        place = await get_place(payload.place_id)
        if place:
            context = f"Place Name: {place.name}\nDescription: {place.description}\nCategory: {place.category.name if place.category else 'N/A'}"
            
    history_dicts = [{"role": msg.role, "content": msg.content} for msg in payload.history]
    
    ai_text = get_ai_response(payload.message, history_dicts, context, payload.language)
    
    return Envelope(success=True, data={"response": ai_text})

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
