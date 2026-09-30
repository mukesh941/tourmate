import asyncio
from app.services.rag_service import retrieve_knowledge_chunks
from app.core.db import AsyncSessionLocal

async def run():
    async with AsyncSessionLocal() as db:
        res = await retrieve_knowledge_chunks('hii i want cafe near by rr layout', db)
        print(len(res))
        if res:
            print(res[0])

asyncio.run(run())
