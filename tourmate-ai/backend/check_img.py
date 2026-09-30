import asyncio
from sqlalchemy import select, create_engine
from sqlalchemy.orm import sessionmaker, selectinload
from app.core.config import settings
from app.models.sql.poi import POI
from app.models.sql.media import POIImage, Image

engine = create_engine(settings.sync_database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def check():
    with SessionLocal() as db:
        poi = db.execute(select(POI).where(POI.name == 'Qutub Minar').options(selectinload(POI.poi_images).selectinload(POIImage.image))).scalars().first()
        if not poi:
            print("POI not found")
            return
        print(f"POI Images count: {len(poi.poi_images)}")
        if poi.poi_images:
            pi = poi.poi_images[0]
            print(f"Has image attr: {hasattr(pi, 'image')}")
            if hasattr(pi, "image") and pi.image:
                print(f"URL: {pi.image.url}")
            else:
                print("No image object attached")

if __name__ == "__main__":
    check()
