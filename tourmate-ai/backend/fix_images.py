import asyncio
from app.core.db import AsyncSessionLocal
from sqlalchemy import text
from app.services.destination_service import CANONICAL_DESTINATION_METADATA

async def main():
    async with AsyncSessionLocal() as s:
        places = ["Agra Fort", "Amer Fort", "Basilica of Bom Jesus"]
        for p in places:
            meta = CANONICAL_DESTINATION_METADATA.get(p.lower())
            if meta and "cover_image" in meta:
                url = meta["cover_image"]
                await s.execute(
                    text("UPDATE locations SET image = :url WHERE name = :name"),
                    {"url": url, "name": p}
                )
                print(f"Updated {p} with Unsplash URL")
        
        await s.commit()

if __name__ == '__main__':
    asyncio.run(main())
