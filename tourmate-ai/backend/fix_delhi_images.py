import asyncio
from sqlalchemy import select, update
from app.core.db import AsyncSessionLocal
from app.models.sql.poi import POI
from app.models.sql.media import POIImage, Image

# Hardcoded Unsplash URLs for Delhi attractions to avoid Wikimedia 403s
WIKI_TO_UNSPLASH = {
    "Qutub Minar": "https://images.unsplash.com/photo-1574768399557-4fb8e95fa6f1?auto=format&fit=crop&w=1200&q=80",
    "Red Fort": "https://images.unsplash.com/photo-1587595431973-160d0d94add1?auto=format&fit=crop&w=1200&q=80",
    "India Gate": "https://images.unsplash.com/photo-1585135445207-8898160840b2?auto=format&fit=crop&w=1200&q=80",
    "Humayun's Tomb": "https://images.unsplash.com/photo-1574169208507-84376144848b?auto=format&fit=crop&w=1200&q=80",
    "Lotus Temple": "https://images.unsplash.com/photo-1590050752112-92144ddf3301?auto=format&fit=crop&w=1200&q=80",
    "Akshardham Temple": "https://images.unsplash.com/photo-1603522198007-8e6f1f44a30f?auto=format&fit=crop&w=1200&q=80",
    "Swaminarayan Akshardham": "https://images.unsplash.com/photo-1603522198007-8e6f1f44a30f?auto=format&fit=crop&w=1200&q=80",
    "Jama Masjid": "https://images.unsplash.com/photo-1555310931-15b50df4779a?auto=format&fit=crop&w=1200&q=80",
    "Chandni Chowk": "https://images.unsplash.com/photo-1585828068970-1b752ebc6604?auto=format&fit=crop&w=1200&q=80"
}

async def update_images():
    async with AsyncSessionLocal() as session:
        for poi_name, new_url in WIKI_TO_UNSPLASH.items():
            result = await session.execute(select(POI).where(POI.name.ilike(f"%{poi_name}%")))
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
        print("Updated images successfully.")

if __name__ == "__main__":
    asyncio.run(update_images())
