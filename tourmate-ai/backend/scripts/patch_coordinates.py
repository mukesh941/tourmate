import asyncio
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from sqlalchemy import text
from app.core.db import AsyncSessionLocal

COORDS = {
    "Leh": (34.1526, 77.5771),
    "Aurangabad": (19.8762, 75.3433),
    "Rajahmundry": (17.0005, 81.8040),
    "Bengaluru": (12.9716, 77.5946),
    "Mysuru": (12.2958, 76.6394),
    "Delhi": (28.7041, 77.1025),
    "Mumbai": (19.0760, 72.8777),
    "Udupi": (13.3409, 74.7421),
    "Jaipur": (26.9124, 75.7873),
    "Varanasi": (25.3176, 82.9739),
    "Mangaluru": (12.9141, 74.8560),
    "Ajmer": (26.4499, 74.6399),
    "Prayagraj": (25.4358, 81.8463)
}

async def patch_coords():
    async with AsyncSessionLocal() as session:
        for name, (lat, lng) in COORDS.items():
            # See if it exists
            res = await session.execute(text("SELECT id FROM locations WHERE name = :name LIMIT 1"), {"name": name})
            row = res.fetchone()
            if row:
                await session.execute(text("UPDATE locations SET latitude = :lat, longitude = :lng WHERE id = :id"), {"lat": lat, "lng": lng, "id": row.id})
                print(f"Patched {name}")
            else:
                # Insert if missing
                print(f"Inserting missing {name}")
                await session.execute(text(
                    "INSERT INTO locations (id, name, city, latitude, longitude, state, country, category) "
                    "VALUES (gen_random_uuid(), :name, :name, :lat, :lng, 'Unknown', 'India', 'City')"
                ), {"name": name, "lat": lat, "lng": lng})
        await session.commit()
        print("Done")

if __name__ == "__main__":
    asyncio.run(patch_coords())
