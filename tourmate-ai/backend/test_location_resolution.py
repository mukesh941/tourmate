import asyncio
from app.core.db import AsyncSessionLocal
from app.services.location_service import resolve_location_name

async def test_locations():
    locations_to_test = [
        "Bangalore", "Bengaluru", "Bombay", "Mumbai", "Madras", "Chennai",
        "Calcutta", "Kolkata", "Cochin", "Kochi", "Mysore", "Mysuru",
        "Trivandrum", "Thiruvananthapuram", "Banaras", "Varanasi",
        "Pondicherry", "Puducherry", "Delhi", "New Delhi", "Goa", "Ladakh",
        "Andaman and Nicobar Islands"
    ]
    
    async with AsyncSessionLocal() as session:
        for loc in locations_to_test:
            res = await resolve_location_name(loc, session)
            if res:
                print(f"[OK] {loc:20} -> {res.get('name')} (Source: {res.get('source')}, Country: {res.get('country')})")
            else:
                print(f"[FAIL] {loc:20} -> NOT RESOLVED")

if __name__ == "__main__":
    asyncio.run(test_locations())
