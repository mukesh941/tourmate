import asyncio
from app.core.db import AsyncSessionLocal
from app.services.destination_service import get_all_destinations

async def main():
    async with AsyncSessionLocal() as s:
        res = await get_all_destinations(db=s, page=1, page_size=20)
        missing = [d.name for d in res.results if d.cover_image.startswith('data:')]
        print(f"Destinations with placeholder images: {missing}")

if __name__ == '__main__':
    asyncio.run(main())
