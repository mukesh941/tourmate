import asyncio
from app.core.db import AsyncSessionLocal
from app.services.destination_resolver import full_destination_resolution

async def test_resolve():
    async with AsyncSessionLocal() as db:
        res = await full_destination_resolution("Plan a trip to Goa for 3 days", db)
        print("Resolved Loc:", res)
        
        res2 = await full_destination_resolution("Plan a trip to Mumbai", db)
        print("Resolved Loc 2:", res2)

if __name__ == "__main__":
    asyncio.run(test_resolve())
