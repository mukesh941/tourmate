import asyncio
import json
from sqlalchemy import select
from app.core.database import get_db
from app.models.sql.location import Location
from app.core.db import AsyncSessionLocal
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

new_locations_data = [
    {"name": "Gokarna", "city": "Gokarna", "state": "Karnataka", "country": "India", "category": "beach", "latitude": 14.5497, "longitude": 74.3188, "description": "Known for pristine beaches and Mahabaleshwar temple."},
    {"name": "Varkala", "city": "Varkala", "state": "Kerala", "country": "India", "category": "beach", "latitude": 8.7330, "longitude": 76.7167, "description": "Famous for the Varkala cliff and Papanasam beach."},
    {"name": "Tirthan Valley", "city": "Banjar", "state": "Himachal Pradesh", "country": "India", "category": "nature", "latitude": 31.6384, "longitude": 77.3444, "description": "Gateway to the Great Himalayan National Park."},
    {"name": "Zanskar", "city": "Kargil", "state": "Ladakh", "country": "India", "category": "nature", "latitude": 33.4734, "longitude": 76.9806, "description": "Remote valley known for Chadar Trek and monasteries."},
    {"name": "Auli", "city": "Auli", "state": "Uttarakhand", "country": "India", "category": "hill_station", "latitude": 30.5332, "longitude": 79.5663, "description": "Skiing destination with panoramic Himalayan views."},
    {"name": "Cherrapunji", "city": "Cherrapunji", "state": "Meghalaya", "country": "India", "category": "nature", "latitude": 25.2702, "longitude": 91.7323, "description": "One of the wettest places on earth, known for living root bridges."},
    {"name": "Pahalgam", "city": "Pahalgam", "state": "Jammu and Kashmir", "country": "India", "category": "nature", "latitude": 34.0150, "longitude": 75.3268, "description": "Base camp for Amarnath Yatra and scenic valley."},
    {"name": "Kodaikanal", "city": "Kodaikanal", "state": "Tamil Nadu", "country": "India", "category": "hill_station", "latitude": 10.2381, "longitude": 77.4892, "description": "Princess of Hill Stations with a star-shaped lake."},
    {"name": "Hampi", "city": "Hampi", "state": "Karnataka", "country": "India", "category": "heritage", "latitude": 15.3350, "longitude": 76.4600, "description": "UNESCO World Heritage site of the Vijayanagara Empire."}
]

async def seed_new_locations():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Location))
        existing = result.scalars().all()
        
        seen = set([f"{loc.name.lower()}|{loc.state.lower()}" for loc in existing])
        
        added = 0
        for loc_data in new_locations_data:
            key = f"{loc_data['name'].lower()}|{loc_data['state'].lower()}"
            if key not in seen:
                new_loc = Location(
                    id=uuid.uuid4(),
                    name=loc_data["name"],
                    city=loc_data["city"],
                    state=loc_data["state"],
                    country=loc_data["country"],
                    latitude=loc_data["latitude"],
                    longitude=loc_data["longitude"],
                    category=loc_data["category"],
                    description=loc_data["description"]
                )
                session.add(new_loc)
                added += 1
                seen.add(key)
        
        await session.commit()
        print(f"Successfully added {added} new locations.")

if __name__ == "__main__":
    asyncio.run(seed_new_locations())
