import asyncio
from sqlalchemy import select, update
from app.core.db import AsyncSessionLocal
from app.models.sql.poi import POI
from app.models.sql.media import POIImage, Image
import urllib.parse

PRIMARY_ATTRACTIONS = [
    "Qutub Minar",
    "Red Fort",
    "India Gate",
    "Humayun's Tomb",
    "Lotus Temple",
    "Akshardham",
    "Jama Masjid",
    "Chandni Chowk"
]

async def update_images():
    async with AsyncSessionLocal() as session:
        for name in PRIMARY_ATTRACTIONS:
            search_query = f"{name} Delhi landmark"
            query_encoded = urllib.parse.quote_plus(search_query)
            new_url = f"https://tse1.mm.bing.net/th?q={query_encoded}"
            
            result = await session.execute(select(POI).where(POI.name.ilike(f"%{name}%")))
            pois = result.scalars().all()
            for poi in pois:
                pi_res = await session.execute(select(POIImage).where(POIImage.poi_id == poi.id))
                poi_images = pi_res.scalars().all()
                for pi in poi_images:
                    await session.execute(
                        update(Image)
                        .where(Image.id == pi.image_id)
                        .values(url=new_url, thumbnail_url=new_url)
                    )
        await session.commit()
        print("Updated primary attractions with Bing image URLs.")

if __name__ == "__main__":
    asyncio.run(update_images())
