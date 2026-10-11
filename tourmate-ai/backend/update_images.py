import asyncio
from app.core.db import AsyncSessionLocal
from sqlalchemy import text

async def main():
    async with AsyncSessionLocal() as s:
        # Static URLs
        urls = {
            "Agra Fort": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6f/Agra_Fort_in_Agra.jpg/1280px-Agra_Fort_in_Agra.jpg",
            "Amer Fort": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/Amber_Fort_03_2016_2991.jpg/1280px-Amber_Fort_03_2016_2991.jpg",
            "Basilica of Bom Jesus": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ec/Basilica_of_Bom_Jesus.jpg/1280px-Basilica_of_Bom_Jesus.jpg"
        }
        
        for name, url in urls.items():
            await s.execute(
                text("UPDATE locations SET image = :url WHERE name = :name"),
                {"url": url, "name": name}
            )
            print(f"Updated {name}")
        
        await s.commit()
        print("Updated locations with static images")

if __name__ == '__main__':
    asyncio.run(main())
