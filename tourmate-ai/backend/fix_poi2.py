import asyncio
from app.core.db import AsyncSessionLocal
from sqlalchemy import select, update
from app.models.sql.poi import POI
from app.models.sql.media import POIImage, Image
from app.services.destination_service import CANONICAL_DESTINATION_METADATA

async def main():
    async with AsyncSessionLocal() as s:
        for p in ['Agra Fort', 'Amer Fort']:
            stmt = select(POI).where(POI.name == p)
            res = await s.execute(stmt)
            poi = res.scalars().first()
            
            if poi:
                meta = CANONICAL_DESTINATION_METADATA.get(p.lower())
                url = meta["cover_image"]
                
                stmt2 = select(POIImage).where(POIImage.poi_id == poi.id)
                res2 = await s.execute(stmt2)
                poi_images = res2.scalars().all()
                for pi in poi_images:
                    await s.execute(
                        update(Image)
                        .where(Image.id == pi.image_id)
                        .values(url=url)
                    )
                
                print(f"Updated {p} to {url}")
        
        await s.commit()

if __name__ == '__main__':
    asyncio.run(main())
