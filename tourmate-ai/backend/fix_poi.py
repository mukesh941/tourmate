import asyncio
from app.core.db import AsyncSessionLocal
from sqlalchemy import select, update
from app.models.sql.poi import POI
from app.models.sql.media import POIImage, Image

async def main():
    async with AsyncSessionLocal() as s:
        stmt = select(POI).where(POI.name == 'Basilica of Bom Jesus')
        res = await s.execute(stmt)
        poi = res.scalars().first()
        
        if poi:
            print(f"Found POI: {poi.name}, ID: {poi.id}")
            stmt2 = select(POIImage).where(POIImage.poi_id == poi.id)
            res2 = await s.execute(stmt2)
            poi_images = res2.scalars().all()
            for pi in poi_images:
                print(f"Updating Image ID: {pi.image_id}")
                await s.execute(
                    update(Image)
                    .where(Image.id == pi.image_id)
                    .values(url='https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?auto=format&fit=crop&w=1200&q=80')
                )
            
            await s.commit()
            print("Successfully updated POI image to Unsplash URL.")
        else:
            print("POI not found")

if __name__ == '__main__':
    asyncio.run(main())
