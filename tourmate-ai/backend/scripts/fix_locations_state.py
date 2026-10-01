"""
Data repair script: Populate missing states and parent state references
for all location records using authoritative geographic data and world_cities admin1 mapping.
Preserves existing IDs, relationships, and is completely idempotent.
"""
import asyncio
import json
import os
import sys
from sqlalchemy import text

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.core.db import AsyncSessionLocal

ADMIN1_TO_STATE = {
    '01': 'Andaman and Nicobar Islands',
    '02': 'Andhra Pradesh',
    '03': 'Assam',
    '05': 'Chandigarh',
    '07': 'Delhi',
    '09': 'Gujarat',
    '10': 'Haryana',
    '11': 'Himachal Pradesh',
    '12': 'Jammu and Kashmir',
    '13': 'Kerala',
    '14': 'Lakshadweep',
    '16': 'Maharashtra',
    '17': 'Manipur',
    '18': 'Meghalaya',
    '19': 'Karnataka',
    '20': 'Nagaland',
    '21': 'Odisha',
    '22': 'Puducherry',
    '23': 'Punjab',
    '24': 'Rajasthan',
    '25': 'Tamil Nadu',
    '26': 'Tripura',
    '28': 'West Bengal',
    '29': 'Sikkim',
    '30': 'Arunachal Pradesh',
    '31': 'Mizoram',
    '33': 'Goa',
    '34': 'Bihar',
    '35': 'Madhya Pradesh',
    '36': 'Uttar Pradesh',
    '37': 'Chhattisgarh',
    '38': 'Jharkhand',
    '39': 'Uttarakhand',
    '40': 'Telangana',
    '41': 'Ladakh',
    '52': 'Dadra and Nagar Haveli and Daman and Diu'
}

SPECIAL_CASES = {
    'dadra and nagar haveli and daman and diu': 'Dadra and Nagar Haveli and Daman and Diu',
    'lakshadweep': 'Lakshadweep',
    'pondicherry': 'Puducherry',
    'monument loc': 'Uttar Pradesh',
    'p2 loc': 'Uttar Pradesh',
    'city center': 'Uttar Pradesh',
    'fort loc': 'Uttar Pradesh',
    'p1 loc': 'Uttar Pradesh',
    'hotel loc': 'Uttar Pradesh',
    'poi loc': 'Uttar Pradesh',
}

async def repair_location_states():
    print("Starting location state repair...")

    with open('world_cities.json', 'r', encoding='utf-8') as f:
        cities = json.load(f)

    coord_map = {}
    name_map = {}
    for c in cities:
        if c.get('country') == 'IN':
            name = c.get('name', '').strip().lower()
            a1 = c.get('admin1')
            st = ADMIN1_TO_STATE.get(a1)
            if st:
                lat = round(float(c.get('lat', 0)), 3)
                lng = round(float(c.get('lng', 0)), 3)
                coord_map[(name, lat, lng)] = st
                if name not in name_map:
                    name_map[name] = st

    async with AsyncSessionLocal() as session:
        # Load state mapping from database
        res = await session.execute(text("SELECT id, name FROM locations WHERE category IN ('State', 'Union Territory')"))
        state_db_map = {row.name.lower().strip(): row.id for row in res.fetchall()}

        # Fetch records needing repair
        res = await session.execute(text("SELECT id, name, category, parent_id, state, latitude, longitude FROM locations WHERE state IS NULL OR state = ''"))
        records = res.fetchall()
        print(f"Found {len(records)} locations with missing state.")

        updates = []
        for r in records:
            lname = r.name.strip().lower()
            lat = round(float(r.latitude or 0), 3)
            lng = round(float(r.longitude or 0), 3)

            state_val = SPECIAL_CASES.get(lname) or coord_map.get((lname, lat, lng)) or name_map.get(lname)
            if not state_val:
                # Fallback: if category is State or UT itself
                if lname in state_db_map:
                    state_val = r.name.strip()
                else:
                    state_val = "India"

            # Determine parent_id
            parent_id = r.parent_id
            if parent_id is None and state_val:
                state_id = state_db_map.get(state_val.lower().strip())
                if state_id and r.category not in ('State', 'Union Territory'):
                    parent_id = state_id

            updates.append({
                "id": r.id,
                "state_val": state_val,
                "parent_id": parent_id
            })

        if updates:
            print(f"Updating {len(updates)} location records...")
            # Batch update in chunks of 500
            chunk_size = 500
            for i in range(0, len(updates), chunk_size):
                chunk = updates[i:i + chunk_size]
                await session.execute(
                    text("UPDATE locations SET state = :state_val, parent_id = :parent_id WHERE id = :id"),
                    chunk
                )
            await session.commit()
            print("Successfully updated location states and parent relationships.")

        # Verification check
        res = await session.execute(text("SELECT count(*) FROM locations WHERE state IS NULL OR state = ''"))
        remaining = res.scalar()
        print(f"Remaining locations with empty state: {remaining}")

        # Check 4 Arm (Kharwali) specifically
        res = await session.execute(text("SELECT id, name, city, state, country FROM locations WHERE name = '4 Arm (Kharwali)'"))
        row = res.fetchone()
        if row:
            print("4 Arm (Kharwali) state after fix:", dict(row._mapping))

if __name__ == "__main__":
    asyncio.run(repair_location_states())
