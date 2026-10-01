"""
Fix data quality issues for Problem 6:
1. Ensure Chandigarh has state='Chandigarh' and union_territory='Chandigarh'.
2. Fill city = name for records where city is empty.
3. Fix coordinates for records with lat=0, lng=0 using world_cities or state centroid coordinates.
"""
import asyncio
import json
import os
import sys
from sqlalchemy import text

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.core.db import AsyncSessionLocal

STATE_CENTROIDS = {
    "Andhra Pradesh": (15.9129, 79.7400),
    "Arunachal Pradesh": (28.2180, 94.7278),
    "Assam": (26.2006, 92.9376),
    "Bihar": (25.0961, 85.3131),
    "Chhattisgarh": (21.2787, 81.8661),
    "Goa": (15.2993, 74.1240),
    "Gujarat": (22.2587, 71.1924),
    "Haryana": (29.0588, 76.0856),
    "Himachal Pradesh": (31.1048, 77.1734),
    "Jharkhand": (23.6102, 85.2799),
    "Karnataka": (15.3173, 75.7139),
    "Kerala": (10.8505, 76.2711),
    "Madhya Pradesh": (22.9734, 78.6569),
    "Maharashtra": (19.7515, 75.7139),
    "Manipur": (24.6637, 93.9063),
    "Meghalaya": (25.4670, 91.3662),
    "Mizoram": (23.1645, 92.9376),
    "Nagaland": (26.1584, 94.5624),
    "Odisha": (20.9517, 85.0985),
    "Punjab": (31.1471, 75.3412),
    "Rajasthan": (27.0238, 74.2179),
    "Sikkim": (27.5330, 88.5122),
    "Tamil Nadu": (11.1271, 78.6569),
    "Telangana": (18.1124, 79.0193),
    "Tripura": (23.9408, 91.9882),
    "Uttar Pradesh": (26.8467, 80.9462),
    "Uttarakhand": (30.0668, 79.0193),
    "West Bengal": (22.9868, 87.8550),
    "Andaman and Nicobar Islands": (11.7401, 92.6586),
    "Chandigarh": (30.7333, 76.7794),
    "Dadra and Nagar Haveli and Daman and Diu": (20.1809, 73.0169),
    "Delhi": (28.7041, 77.1025),
    "Jammu and Kashmir": (33.7782, 76.5762),
    "Ladakh": (34.1526, 77.5771),
    "Lakshadweep": (10.5667, 72.6417),
    "Puducherry": (11.9416, 79.8083),
}


async def fix_data_quality():
    print("Fixing data quality issues in PostgreSQL...")
    with open('world_cities.json', 'r', encoding='utf-8') as f:
        world_cities = json.load(f)
    city_coords = {c['name'].lower().strip(): (float(c['lat']), float(c['lng'])) for c in world_cities if c.get('country') == 'IN'}

    async with AsyncSessionLocal() as session:
        # 1. Fix Chandigarh state
        await session.execute(text("""
            UPDATE locations 
            SET state = 'Chandigarh', union_territory = 'Chandigarh'
            WHERE name = 'Chandigarh' AND category = 'Union Territory'
        """))

        # 2. Fill empty city field
        await session.execute(text("""
            UPDATE locations
            SET city = name
            WHERE city IS NULL OR city = ''
        """))

        # 3. Fill empty country field
        await session.execute(text("""
            UPDATE locations
            SET country = 'India'
            WHERE country IS NULL OR country = ''
        """))

        # 4. Patch coordinates for records with lat=0 or lng=0 or outside bounds
        res = await session.execute(text("""
            SELECT id, name, state, category FROM locations 
            WHERE latitude < 6.0 OR latitude > 38.0 OR longitude < 68.0 OR longitude > 98.0
        """))
        zero_coords = res.fetchall()
        print(f"Found {len(zero_coords)} records needing coordinates.")

        for row in zero_coords:
            loc_id = row.id
            name = row.name.lower().strip()
            state = row.state.strip()
            
            # Check city_coords
            if name in city_coords:
                lat, lng = city_coords[name]
            elif state in STATE_CENTROIDS:
                lat, lng = STATE_CENTROIDS[state]
            else:
                # Try finding state in STATE_CENTROIDS by fuzzy
                matched_state = None
                for st in STATE_CENTROIDS:
                    if st.lower() in state.lower() or state.lower() in st.lower():
                        matched_state = st
                        break
                if matched_state:
                    lat, lng = STATE_CENTROIDS[matched_state]
                else:
                    lat, lng = (20.5937, 78.9629) # India center fallback

            await session.execute(
                text("UPDATE locations SET latitude = :lat, longitude = :lng WHERE id = :id"),
                {"lat": lat, "lng": lng, "id": loc_id}
            )

        await session.commit()
        print("Data quality fixes successfully committed.")


if __name__ == "__main__":
    asyncio.run(fix_data_quality())
