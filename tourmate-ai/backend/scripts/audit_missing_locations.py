import asyncio
from sqlalchemy import select
from app.core.db import AsyncSessionLocal
from app.models.sql.location import Location
from app.services.destination_service import get_all_destinations

async def run_missing_audit():
    async with AsyncSessionLocal() as session:
        stmt = select(Location).where(Location.is_active == True)
        all_locs = (await session.execute(stmt)).scalars().all()
        
    api_destinations = await get_all_destinations()
    api_ids = {d.id for d in api_destinations}
    
    missing_locs = []
    for loc in all_locs:
        # get_all_destinations uses loc.city as the ID
        city = (loc.city or "").strip()
        if not city or city not in api_ids:
            missing_locs.append(loc)
            
    print(f"Total active DB locations: {len(all_locs)}")
    print(f"Total API destinations: {len(api_destinations)}")
    print(f"Total missing: {len(missing_locs)}")
    
    # Sample a few missing
    print("Sample missing locations:")
    for loc in missing_locs[:10]:
        print(f"ID: {loc.id}, Name: {loc.name}, City: {loc.city}, Type: {loc.location_type}")

if __name__ == "__main__":
    asyncio.run(run_missing_audit())
