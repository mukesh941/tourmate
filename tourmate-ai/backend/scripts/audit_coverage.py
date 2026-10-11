import asyncio
import httpx
from sqlalchemy import select, func
from app.core.db import AsyncSessionLocal
from app.models.sql.location import Location
from app.services.destination_service import get_all_destinations

async def run_coverage_audit():
    async with AsyncSessionLocal() as session:
        stmt = select(Location).where(Location.is_active == True)
        all_locs = (await session.execute(stmt)).scalars().all()
        db_count = len(all_locs)
        
    # Get total from API using service directly
    api_response = await get_all_destinations(page=1, page_size=1)
    api_count = api_response.total
    
    missing = db_count - api_count
    
    # We can also check unsearchable by fetching all with a big limit
    all_api_response = await get_all_destinations(page=1, page_size=10000)
    frontend_accessible = all_api_response.total
    
    # Search for an obscure location
    search_response = await get_all_destinations(page=1, page_size=10, search="Kharwali")
    unsearchable = 0 if len(search_response.results) > 0 else 1
    
    without_images = 0
    with_images = 0
    for res in all_api_response.results:
        if not res.cover_image or 'data:image' in res.cover_image:
            without_images += 1
        else:
            with_images += 1
            
    print("DATABASE LOCATIONS:", db_count)
    print("API LOCATIONS:", api_count)
    print("MISSING FROM API:", missing)
    print("FRONTEND ACCESSIBLE LOCATIONS:", frontend_accessible)
    print("UNSEARCHABLE LOCATIONS:", unsearchable)
    print("LOCATIONS WITHOUT IMAGES:", without_images)
    print("LOCATIONS WITH VALID IMAGES:", with_images)

if __name__ == "__main__":
    asyncio.run(run_coverage_audit())
