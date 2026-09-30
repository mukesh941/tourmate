import asyncio
import json
from app.core.db import AsyncSessionLocal
from app.services.authoritative_itinerary_service import generate_authoritative_itinerary
from app.schemas.itinerary import ItineraryGenerateRequest

async def test():
    async with AsyncSessionLocal() as db:
        res = await generate_authoritative_itinerary(ItineraryGenerateRequest(destination_name='Mumbai', days=1, budget='Medium'), db)
        print('Mumbai 1 day cost:', res[0]['total_estimated_cost'])
        print(json.dumps(res[0]['schedule'][0].get('accommodation'), indent=2))
        
asyncio.run(test())
