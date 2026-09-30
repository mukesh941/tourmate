from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

router = APIRouter(tags=["Chatbot"])

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []

@router.post("/chat")
async def chat_endpoint(payload: ChatRequest):
    # Simulated full contextual RAG + Route + Database API wrapper
    return {
        "success": True,
        "message": "This is a grounded and safe mock response from TourMate AI.",
        "conversation_id": "simulated_context"
    }
