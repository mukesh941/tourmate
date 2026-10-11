import asyncio
import json
from sqlalchemy import select, func
from app.core.db import AsyncSessionLocal
from app.models.sql.location import Location
from app.models.sql.poi import POI
from app.services.destination_service import get_all_destinations

async def run_audit():
    async with AsyncSessionLocal() as session:
        # 1. Total locations in database
        stmt = select(func.count(Location.id))
        total_db = (await session.execute(stmt)).scalar()
        
        # 2. Total active locations
        stmt_active = select(func.count(Location.id)).where(Location.is_active == True)
        total_active = (await session.execute(stmt_active)).scalar()
        
        # 3. Total locations by type
        stmt_type = select(Location.location_type, func.count(Location.id)).group_by(Location.location_type)
        type_counts = (await session.execute(stmt_type)).all()
        
        # 4. Total locations with POIs
        stmt_poi = select(func.count(Location.id)).where(Location.pois.any(POI.is_active == True))
        total_with_poi = (await session.execute(stmt_poi)).scalar()

    # 5. Total locations from API/Service
    api_destinations = await get_all_destinations()
    total_api = len(api_destinations)
    
    # 6. Count missing
    print("--- AUDIT RESULTS ---")
    print(f"DATABASE LOCATIONS: {total_db}")
    print(f"ACTIVE LOCATIONS: {total_active}")
    print(f"LOCATIONS WITH POI: {total_with_poi}")
    for t, c in type_counts:
        print(f"Type '{t}': {c}")
    print(f"API LOCATIONS: {total_api}")
    print(f"MISSING FROM API: {total_db - total_api}")

if __name__ == "__main__":
    asyncio.run(run_audit())
