import asyncio
from app.core.db import AsyncSessionLocal
from app.services.poi_service import get_all_pois

async def main():
    async with AsyncSessionLocal() as s:
        for q in ['Agra Fort', 'Amer Fort']:
            res = await get_all_pois(q=q, db=s)
            for r in res:
                print(f"Name: {r.name}, Images: {r.images}")

if __name__ == '__main__':
    asyncio.run(main())
