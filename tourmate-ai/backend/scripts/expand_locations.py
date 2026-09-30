import asyncio
import json
import os
import sys
import uuid
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.core.db import AsyncSessionLocal

async def expand_locations():
    print("Expanding Locations...")
    async with AsyncSessionLocal() as session:
        # Load datasets
        with open('indian_districts.json', 'r', encoding='utf-8') as f:
            districts_data = json.load(f)['states']
            
        with open('indian_cities.json', 'r', encoding='utf-8') as f:
            cities_data = json.load(f)
            
        # Get existing states/UTs
        res = await session.execute(text("SELECT id, name FROM locations WHERE category IN ('State', 'Union Territory')"))
        state_map = {row.name.lower().strip(): row.id for row in res.fetchall()}
        
        legacy_state_map = {
            "orissa": "odisha",
            "pondicherry": "puducherry",
            "lakshadweep (ut)": "lakshadweep",
            "puducherry (ut)": "puducherry"
        }
        
        # 1. Create Districts
        print("Creating Districts...")
        district_map = {} # (district_name, state_id) -> id
        
        # Check existing districts
        res = await session.execute(text("SELECT id, name, parent_id FROM locations WHERE category = 'District'"))
        for row in res.fetchall():
            district_map[(row.name.lower().strip(), row.parent_id)] = row.id

        new_districts = []
        for s_data in districts_data:
            state_name = s_data['state'].lower().strip()
            state_name = legacy_state_map.get(state_name, state_name)
            
            state_id = state_map.get(state_name)
            if not state_id:
                print(f"Warning: State {state_name} not found in DB.")
                continue
                
            for dist_name in s_data.get('districts', []):
                dist_key = (dist_name.lower().strip(), state_id)
                if dist_key not in district_map:
                    # Create district
                    d_id = uuid.uuid4()
                    new_districts.append({
                        "id": d_id,
                        "name": dist_name,
                        "parent_id": state_id,
                        "cat": "District",
                        "country": "India",
                        "state_val": s_data['state'],
                        "district_val": dist_name
                    })
                    district_map[dist_key] = d_id
                    
        # Insert new districts
        if new_districts:
            await session.execute(
                text("INSERT INTO locations (id, name, parent_id, category, country, latitude, longitude, city, state, union_territory, district) "
                     "VALUES (:id, :name, :parent_id, :cat, :country, 0.0, 0.0, '', :state_val, '', :district_val)"),
                new_districts
            )
            print(f"Inserted {len(new_districts)} new districts.")
            
        # 2. Fix Orphan Cities
        print("Linking Cities...")
        # Create a mapping from city name to state from indian_cities.json
        city_to_state = {}
        for c in cities_data:
            c_name = c['name'].lower().strip()
            c_state = c['state'].lower().strip()
            c_state = legacy_state_map.get(c_state, c_state)
            city_to_state[c_name] = c_state
            
        # Also map from district dataset
        for s_data in districts_data:
            s_name = s_data['state'].lower().strip()
            s_name = legacy_state_map.get(s_name, s_name)
            for d in s_data.get('districts', []):
                d_name = d.lower().strip()
                if d_name not in city_to_state:
                    city_to_state[d_name] = s_name

        # Fetch orphans
        res = await session.execute(text("SELECT id, name FROM locations WHERE category = 'City' AND parent_id IS NULL"))
        orphans = res.fetchall()
        
        updates = []
        for o in orphans:
            c_name = o.name.lower().strip()
            if c_name in city_to_state:
                s_name = city_to_state[c_name]
                s_id = state_map.get(s_name)
                
                # Try to link to district if it matches exactly
                d_key = (c_name, s_id)
                if d_key in district_map:
                    updates.append({"id": o.id, "pid": district_map[d_key], "state_val": s_name})
                elif s_id:
                    updates.append({"id": o.id, "pid": s_id, "state_val": s_name})
                    
        if updates:
            await session.execute(
                text("UPDATE locations SET parent_id = :pid, state = :state_val WHERE id = :id"),
                updates
            )
            print(f"Linked {len(updates)} orphan cities to their States/Districts.")
        
        await session.commit()
        print("Done.")

if __name__ == "__main__":
    asyncio.run(expand_locations())
