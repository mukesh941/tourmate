import asyncio
from app.core.db import AsyncSessionLocal
from app.services.destination_service import get_all_destinations, CANONICAL_DESTINATION_METADATA

async def main():
    async with AsyncSessionLocal() as s:
        res = await get_all_destinations(db=s, page=1, page_size=20)
        for d in res.results:
            if d.name in ["Agra Fort", "Amer Fort", "Basilica of Bom Jesus"]:
                print(f"Name: {d.name}, city_key lookup: {d.name.strip().lower()}, cover_image: {d.cover_image}")
                print(f"Meta dict lookup: {CANONICAL_DESTINATION_METADATA.get(d.name.strip().lower())}")

if __name__ == '__main__':
    asyncio.run(main())
