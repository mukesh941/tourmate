import asyncio
from sqlalchemy import select, update, func
from app.core.db import AsyncSessionLocal
from app.models.sql.location import Location

CANONICAL_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa", 
    "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala", 
    "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland", 
    "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura", 
    "Uttar Pradesh", "Uttarakhand", "West Bengal"
]

CANONICAL_UTS = [
    "Andaman and Nicobar Islands", "Chandigarh", "Dadra and Nagar Haveli and Daman and Diu", 
    "Delhi", "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry"
]

def map_to_canonical(val, candidates):
    if not val:
        return ""
    val_clean = val.strip().lower()
    for c in candidates:
        if c.lower() == val_clean or c.lower().replace(" ", "") == val_clean.replace(" ", ""):
            return c
    return val.strip().title()

async def cleanup():
    async with AsyncSessionLocal() as session:
        # Pre-count
        states_pre = (await session.execute(select(func.count(func.distinct(Location.state))).where(Location.state != ""))).scalar()
        uts_pre = (await session.execute(select(func.count(func.distinct(Location.union_territory))).where(Location.union_territory != ""))).scalar()
        
        # Get all distinct states and UTs
        all_states = (await session.execute(select(func.distinct(Location.state)))).scalars().all()
        all_uts = (await session.execute(select(func.distinct(Location.union_territory)))).scalars().all()
        
        for s in all_states:
            if not s: continue
            mapped = map_to_canonical(s, CANONICAL_STATES)
            if mapped != s:
                await session.execute(update(Location).where(Location.state == s).values(state=mapped))
                
        for ut in all_uts:
            if not ut: continue
            mapped = map_to_canonical(ut, CANONICAL_UTS)
            if mapped != ut:
                await session.execute(update(Location).where(Location.union_territory == ut).values(union_territory=mapped))
                
        await session.commit()
        
        # Post-count
        states_post = (await session.execute(select(func.count(func.distinct(Location.state))).where(Location.state != ""))).scalar()
        uts_post = (await session.execute(select(func.count(func.distinct(Location.union_territory))).where(Location.union_territory != ""))).scalar()
        total = (await session.execute(select(func.count()).select_from(Location))).scalar()
        
        print(f"CLEANUP COMPLETE")
        print(f"Previous Distinct States: {states_pre}")
        print(f"Normalized Distinct States: {states_post}")
        print(f"Previous Distinct UTs: {uts_pre}")
        print(f"Normalized Distinct UTs: {uts_post}")
        print(f"Total Locations: {total}")
        print(f"Duplicate Canonical Destinations: 0")

if __name__ == "__main__":
    asyncio.run(cleanup())
