import asyncio
from app.core.db import AsyncSessionLocal
from app.services.poi_service import get_all_pois

async def main():
    async with AsyncSessionLocal() as s:
        res = await get_all_pois(q='Basilica of Bom Jesus', db=s)
        for r in res:
            print(f"Name: {r.name}, Images: {r.images}")

if __name__ == '__main__':
    asyncio.run(main())
