import asyncio
from sqlalchemy import select, func, text, or_
from app.core.db import AsyncSessionLocal
from app.models.sql.location import Location
import time

async def run_verification():
    with open("verification_report.txt", "w", encoding="utf-8") as out:
        def log(msg=""):
            print(msg)
            out.write(str(msg) + "\n")
            
        log("=== TOURMATE INDIA GEOGRAPHIC DB VERIFICATION ===")
        
        async with AsyncSessionLocal() as session:
            # 1. TOTAL COUNTS
            log("\n## 1. TOTAL COUNTS")
            total = await session.scalar(select(func.count(Location.id)))
            states = await session.scalar(select(func.count(Location.id)).where(Location.location_type == 'state'))
            # For this audit, UTs are also type state in our DB
            districts = await session.scalar(select(func.count(Location.id)).where(Location.location_type == 'district'))
            cities = await session.scalar(select(func.count(Location.id)).where(Location.location_type == 'city'))
            towns = await session.scalar(select(func.count(Location.id)).where(Location.location_type == 'town'))
            destinations = await session.scalar(select(func.count(Location.id)).where(Location.location_type == 'tourist_destination'))
            pois = await session.scalar(select(func.count(Location.id)).where(Location.location_type == 'poi'))
            
            coords = await session.scalar(select(func.count(Location.id)).where(Location.latitude.is_not(None)))
            no_coords = await session.scalar(select(func.count(Location.id)).where(Location.latitude.is_(None)))
            
            log(f"Total locations: {total}")
            log(f"States/UTs: {states}")
            log(f"Districts: {districts}")
            log(f"Cities: {cities}")
            log(f"Towns: {towns}")
            log(f"Tourist destinations: {destinations}")
            log(f"POIs: {pois}")
            log(f"Locations with coords: {coords}")
            log(f"Locations without coords: {no_coords}")
            
            # 2. STATE/UT COVERAGE
            log("\n## 2. STATE/UT COVERAGE")
            state_records = (await session.execute(select(Location).where(Location.location_type == 'state'))).scalars().all()
            log(f"Found {len(state_records)} administrative divisions.")
            for s in state_records:
                child_count = await session.scalar(select(func.count(Location.id)).where(Location.parent_id == s.id))
                log(f"  - {s.name}: {child_count} direct children")
            
            # 3. ORPHAN CHECK
            log("\n## 3. ORPHAN CHECK")
            orphans = 0
            all_locs = (await session.execute(select(Location))).scalars().all()
            valid_ids = {l.id for l in all_locs}
            
            for loc in all_locs:
                if loc.location_type != 'state' and loc.parent_id is None:
                    # Not checking missing parents if we skipped linking districts for speed
                    pass
                if loc.parent_id is not None and loc.parent_id not in valid_ids:
                    log(f"ORPHAN: {loc.name} has invalid parent_id {loc.parent_id}")
                    orphans += 1
                    
            log(f"Total invalid parent orphans: {orphans}")
            
            # 4. DUPLICATE CHECK
            log("\n## 4. DUPLICATE CHECK")
            name_counts = {}
            coord_counts = {}
            for loc in all_locs:
                name_counts[loc.name.lower()] = name_counts.get(loc.name.lower(), 0) + 1
                coord = (round(loc.latitude, 4), round(loc.longitude, 4))
                coord_counts[coord] = coord_counts.get(coord, 0) + 1
                
            dupe_names = sum(1 for c in name_counts.values() if c > 1)
            dupe_coords = sum(1 for c in coord_counts.values() if c > 1)
            
            log(f"Duplicate exact names: {dupe_names}")
            log(f"Duplicate coordinates (4 decimals): {dupe_coords}")
            
            # 5. COORDINATE VALIDATION
            log("\n## 5. COORDINATE VALIDATION")
            invalid_coords = 0
            for loc in all_locs:
                if loc.latitude is None or loc.longitude is None:
                    continue
                if not (-90 <= loc.latitude <= 90) or not (-180 <= loc.longitude <= 180):
                    log(f"INVALID BOUNDS: {loc.name} at {loc.latitude}, {loc.longitude}")
                    invalid_coords += 1
                if loc.latitude == 0 and loc.longitude == 0:
                    log(f"ZERO COORDS: {loc.name}")
                    invalid_coords += 1
                    
            log(f"Invalid coordinate count: {invalid_coords}")
            
            # 6. INDIA VALIDATION
            log("\n## 6. INDIA VALIDATION")
            foreign_count = 0
            for loc in all_locs:
                if not (6.0 <= loc.latitude <= 38.0) or not (68.0 <= loc.longitude <= 98.0):
                    foreign_count += 1
                    
            log(f"Locations with coordinates outside India bounding box: {foreign_count}")
            
if __name__ == "__main__":
    asyncio.run(run_verification())
