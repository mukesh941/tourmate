import asyncio
import os
import sys
import json
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.core.db import AsyncSessionLocal

# India approx bounding box: Lat 6.5 to 37.5, Lng 68.0 to 97.5
LAT_MIN, LAT_MAX = 6.5, 37.5
LNG_MIN, LNG_MAX = 68.0, 97.5

async def clean_locations():
    print("Cleaning Locations...")
    async with AsyncSessionLocal() as session:
        # 1. Remove locations outside India bounding box
        print("Removing locations outside India bounding box...")
        # Note: We skip districts/states that might have 0.0, 0.0 coordinates for now
        res = await session.execute(text(
            "DELETE FROM locations WHERE (latitude != 0.0 OR longitude != 0.0) AND (latitude < :lat_min OR latitude > :lat_max OR longitude < :lng_min OR longitude > :lng_max)"
        ), {"lat_min": LAT_MIN, "lat_max": LAT_MAX, "lng_min": LNG_MIN, "lng_max": LNG_MAX})
        print(f"Deleted {res.rowcount} locations outside bounding box.")
        
        # 2. Skip deleting orphan cities to avoid FK constraint violations and because they might be valid data
        print("Skipping deletion of orphan cities...")
        
        # 3. Add aliases
        print("Adding aliases...")
        aliases_map = {
            "mumbai": ["bombay"],
            "chennai": ["madras"],
            "bengaluru": ["bangalore"],
            "kolkata": ["calcutta"],
            "pune": ["poona"],
            "gurugram": ["gurgaon"],
            "mysuru": ["mysore"],
            "kochi": ["cochin"],
            "thiruvananthapuram": ["trivandrum"],
            "puducherry": ["pondicherry"],
            "odisha": ["orissa"],
            "prayagraj": ["allahabad"],
            "varanasi": ["banaras", "kashi"],
            "vadodara": ["baroda"],
            "guwahati": ["gauhati"],
            "belagavi": ["belgaum"],
            "mangaluru": ["mangalore"],
            "shivamogga": ["shimoga"],
            "hubballi": ["hubli"],
            "vijayawada": ["bezawada"]
        }
        
        res = await session.execute(text("SELECT id, name FROM locations"))
        locations = res.fetchall()
        
        updates = []
        for loc in locations:
            lname = loc.name.lower().strip()
            if lname in aliases_map:
                updates.append({"id": loc.id, "aliases": json.dumps(aliases_map[lname])})
                
        if updates:
            await session.execute(text("UPDATE locations SET aliases = :aliases WHERE id = :id"), updates)
            print(f"Added aliases for {len(updates)} locations.")
            
        # 4. Cleanup extra states
        # There should only be 28 states and 8 UTs. (Total 36)
        res = await session.execute(text("SELECT id, name FROM locations WHERE category IN ('State', 'Union Territory')"))
        states = res.fetchall()
        print(f"Found {len(states)} States/UTs.")
        
        # Keep only the valid ones, delete duplicates/invalid
        VALID_STATES = [
            "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", 
            "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", 
            "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", 
            "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan", 
            "Sikkim", "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", 
            "Uttarakhand", "West Bengal",
            "Andaman and Nicobar Islands", "Chandigarh", "Dadra and Nagar Haveli and Daman and Diu",
            "Delhi", "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry"
        ]
        valid_lower = set(s.lower() for s in VALID_STATES)
        
        seen = set()
        to_delete = []
        for s in states:
            sname = s.name.lower().strip()
            if sname not in valid_lower or sname in seen:
                to_delete.append(s.id)
            else:
                seen.add(sname)
                
        if to_delete:
            # Reassign children to NULL before deleting to avoid constraint errors (or cascade)
            # Actually just delete them and let cascade do it if configured, or manually
            await session.execute(text("UPDATE locations SET parent_id = NULL WHERE parent_id = ANY(:ids)"), {"ids": to_delete})
            res = await session.execute(text("DELETE FROM locations WHERE id = ANY(:ids)"), {"ids": to_delete})
            print(f"Deleted {res.rowcount} invalid/duplicate states/UTs.")

        await session.commit()
        print("Done cleaning.")

if __name__ == "__main__":
    asyncio.run(clean_locations())
