import asyncio
from app.services.location_service import resolve_location
from app.core.db import AsyncSessionLocal

async def run():
    async with AsyncSessionLocal() as db:
        res = await resolve_location('hii i want cafe near by rr layout', db)
        print(res)

asyncio.run(run())
