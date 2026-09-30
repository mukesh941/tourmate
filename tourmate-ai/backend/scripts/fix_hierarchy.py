import asyncio
import os
import sys
import uuid
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.core.db import AsyncSessionLocal
from app.models.sql.location import Location

STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", 
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", 
    "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", 
    "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan", 
    "Sikkim", "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", 
    "Uttarakhand", "West Bengal"
]

UTS = [
    "Andaman and Nicobar Islands", "Chandigarh", "Dadra and Nagar Haveli and Daman and Diu",
    "Delhi", "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry"
]

async def fix_hierarchy():
    print("Fixing Hierarchy...")
    async with AsyncSessionLocal() as session:
        # Step 1: Normalize States and UTs
        # Get all existing states
        res = await session.execute(text("SELECT id, name FROM locations WHERE category = 'State' OR category = 'Union Territory' OR name = ANY(:names)"), {"names": list(STATES + UTS)})
        existing_states_db = res.fetchall()
        
        state_map = {}
        for row in existing_states_db:
            # We will standardize names
            name = row.name.strip()
            # Handle variations if any
            if name == "Orissa": name = "Odisha"
            if name == "Pondicherry": name = "Puducherry"
            # Add to map
            state_map[name.lower()] = row.id

        # Insert missing states/UTs and update existing ones
        for state_name in STATES + UTS:
            is_ut = state_name in UTS
            category = 'Union Territory' if is_ut else 'State'
            key = state_name.lower()
            
            if key in state_map:
                # Update existing
                await session.execute(text(
                    "UPDATE locations SET category = :cat, parent_id = NULL, country = 'India' WHERE id = :id"
                ), {"cat": category, "id": state_map[key]})
            else:
                # Insert new
                new_id = uuid.uuid4()
                await session.execute(text(
                    "INSERT INTO locations (id, name, category, country, latitude, longitude, city, state, union_territory, district) "
                    "VALUES (:id, :name, :cat, 'India', 0.0, 0.0, '', :state_val, :ut_val, '')"
                ), {
                    "id": new_id, 
                    "name": state_name, 
                    "cat": category,
                    "state_val": state_name if not is_ut else "",
                    "ut_val": state_name if is_ut else ""
                })
                state_map[key] = new_id
                
        # Handle some legacy/incorrect states
        legacy_mapping = {
            "orissa": "odisha",
            "pondicherry": "puducherry",
            "delhi ncr": "delhi"
        }
        
        # Step 2: Fix City references to point to correct parent_id
        # We need to map string 'state' field in cities to actual state IDs
        # Fetch all cities
        res = await session.execute(text("SELECT id, state, union_territory FROM locations WHERE category = 'City' OR category = '' OR category = 'Alias'"))
        cities = res.fetchall()
        
        updates = []
        for city in cities:
            state_str = city.state.strip().lower() if city.state else ""
            ut_str = city.union_territory.strip().lower() if city.union_territory else ""
            
            state_match = state_str if state_str else ut_str
            state_match = legacy_mapping.get(state_match, state_match)
            
            parent_id = state_map.get(state_match)
            
            if parent_id:
                updates.append({"id": city.id, "pid": parent_id, "cat": "City"})
            else:
                # If we cannot resolve state, we at least set category to City and parent_id = NULL
                updates.append({"id": city.id, "pid": None, "cat": "City"})
                
        # Batch update
        for u in updates:
            await session.execute(text("UPDATE locations SET parent_id = :pid, category = :cat WHERE id = :id"), u)
            
        # Clean up empty/weird categories
        await session.execute(text("UPDATE locations SET category = 'City' WHERE category NOT IN ('State', 'Union Territory', 'City', 'Town', 'Tourist Destination', 'District') AND location_type != 'poi'"))
        
        await session.commit()
        print("Hierarchy fixed and committed.")

if __name__ == "__main__":
    asyncio.run(fix_hierarchy())
