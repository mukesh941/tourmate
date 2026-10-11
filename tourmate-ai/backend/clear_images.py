import asyncio
from app.core.db import AsyncSessionLocal
from sqlalchemy import text

async def main():
    async with AsyncSessionLocal() as s:
        # Clear the images to empty string so it falls back to CANONICAL_DESTINATION_METADATA
        await s.execute(
            text("UPDATE locations SET image = '' WHERE name IN ('Agra Fort', 'Amer Fort', 'Basilica of Bom Jesus')")
        )
        await s.commit()
        print("Cleared images for the three places.")

if __name__ == '__main__':
    asyncio.run(main())
