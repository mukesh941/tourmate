import asyncio
from app.core.db import AsyncSessionLocal
from app.services.destination_service import get_all_destinations

async def main():
    async with AsyncSessionLocal() as s:
        res = await get_all_destinations(db=s, page=1, page_size=20)
        for d in res.results:
            print(f"{d.name}: {d.cover_image[:60]}...")

if __name__ == '__main__':
    asyncio.run(main())
