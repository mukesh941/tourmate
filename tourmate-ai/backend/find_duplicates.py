import asyncio
from sqlalchemy import select
from app.core.db import AsyncSessionLocal
from app.models.sql.location import Location
from app.models.sql.poi import POI
from app.models.sql.accommodation import Accommodation
from app.models.sql.transport import TransportOption
from app.models.sql.trip import Trip

async def find_duplicates():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Location))
        locations = result.scalars().all()
        
        seen = {}
        duplicates = []
        for loc in locations:
            key = f"{loc.name.lower()}|{loc.state.lower()}"
            if key in seen:
                duplicates.append((seen[key], loc))
            else:
                seen[key] = loc
                
        print(f"Found {len(duplicates)} duplicate pairs in PostgreSQL")
        for orig, dup in duplicates:
            print(f"Duplicate: {dup.name}, {dup.state}")
            print(f"  Orig ID: {orig.id}, Lat/Lng: {orig.latitude}/{orig.longitude}")
            print(f"  Dup ID:  {dup.id}, Lat/Lng: {dup.latitude}/{dup.longitude}")
            print(f"  Orig Cat: {orig.category}, Dup Cat: {dup.category}")
            print("---")

if __name__ == "__main__":
    asyncio.run(find_duplicates())
