import asyncio
from app.core.db import AsyncSessionLocal
from app.api.routes.ai import chat_endpoint, ChatRequest
from fastapi import Request
import traceback
import sys

class DummyUser:
    pass

class DummyRequest:
    def __init__(self):
        self.scope = {"type": "http", "path": "/ai/chat"}
        
async def test_chat(query: str):
    async with AsyncSessionLocal() as db:
        req = ChatRequest(message=query, history=[])
        dummy_req = DummyRequest()
        try:
            res = await chat_endpoint(dummy_req, req, current_user=DummyUser(), db=db)
            print("Response:", res.data["response"])
        except Exception as e:
            traceback.print_exc()

if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "Plan a trip to Paris"
    asyncio.run(test_chat(query))
