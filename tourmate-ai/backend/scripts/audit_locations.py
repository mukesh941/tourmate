import asyncio
import os
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Adjust sys.path to be able to import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.db import AsyncSessionLocal

async def audit():
    print("==================================================")
    print("PHASE 1 - FULL DATABASE AUDIT")
    print("==================================================")
    
    async with AsyncSessionLocal() as session:
        # 1. Total Location records
        res = await session.execute(text("SELECT count(*) FROM locations;"))
        total_locations = res.scalar()
        print(f"Total Location records: {total_locations}")
        
        # 2. Breakdown by category
        res = await session.execute(text("SELECT category, count(*) FROM locations GROUP BY category;"))
        categories = dict(res.fetchall())
        print("\nBreakdown by category:")
        for cat, count in categories.items():
            print(f"  - {cat}: {count}")
            
        # POIs
        res = await session.execute(text("SELECT count(*) FROM pois;"))
        total_pois = res.scalar()
        print(f"  - POIs: {total_pois}")
        
        # 3. Coordinates
        res = await session.execute(text("SELECT count(*) FROM locations WHERE latitude IS NOT NULL AND longitude IS NOT NULL;"))
        valid_coords = res.scalar()
        res = await session.execute(text("SELECT count(*) FROM locations WHERE latitude IS NULL OR longitude IS NULL;"))
        missing_coords = res.scalar()
        
        # Bounding box of India: lat ~8.4 to 37.6, lon ~68.7 to 97.25
        res = await session.execute(text(
            "SELECT count(*) FROM locations WHERE latitude IS NOT NULL AND "
            "(latitude < 8.4 OR latitude > 37.6 OR longitude < 68.7 OR longitude > 97.25);"
        ))
        suspicious_coords = res.scalar()
        
        print("\nCoordinates:")
        print(f"  - Valid coordinates: {valid_coords}")
        print(f"  - Missing coordinates: {missing_coords}")
        print(f"  - Suspicious coordinates (outside India): {suspicious_coords}")
        
        # 4. Duplicate names
        res = await session.execute(text(
            "SELECT name, count(*) FROM locations GROUP BY name HAVING count(*) > 1;"
        ))
        duplicate_names = res.fetchall()
        print(f"\nDuplicate names: {len(duplicate_names)} locations have duplicate names")
        
        # 5. Duplicate coordinates
        res = await session.execute(text(
            "SELECT latitude, longitude, count(*) FROM locations WHERE latitude IS NOT NULL "
            "GROUP BY latitude, longitude HAVING count(*) > 1;"
        ))
        duplicate_coords = res.fetchall()
        print(f"Duplicate coordinates: {len(duplicate_coords)} coordinate pairs are duplicated")
        
        # 6. Orphan records (e.g. parent_id is missing when category is not State/UT)
        res = await session.execute(text(
            "SELECT count(*) FROM locations WHERE parent_id IS NULL AND category NOT IN ('state', 'union_territory');"
        ))
        orphans = res.scalar()
        print(f"Orphan records (missing parent_id but not state/UT): {orphans}")
        
        # 7. Invalid parent_id relationships
        res = await session.execute(text(
            "SELECT count(*) FROM locations l1 LEFT JOIN locations l2 ON l1.parent_id = l2.id "
            "WHERE l1.parent_id IS NOT NULL AND l2.id IS NULL;"
        ))
        invalid_parents = res.scalar()
        print(f"Invalid parent_id relationships: {invalid_parents}")
        
        # 8. Incorrect hierarchy (e.g. city pointing to another city instead of district/state)
        res = await session.execute(text(
            "SELECT l1.category, l2.category as parent_cat, count(*) "
            "FROM locations l1 JOIN locations l2 ON l1.parent_id = l2.id "
            "GROUP BY l1.category, l2.category;"
        ))
        print("\nHierarchy relationships:")
        for child_cat, parent_cat, count in res.fetchall():
            print(f"  - {child_cat} -> {parent_cat}: {count}")
            
        # 9. Foreign locations
        res = await session.execute(text(
            "SELECT count(*) FROM locations WHERE country != 'India';"
        ))
        foreign_locs = res.scalar()
        print(f"Foreign/non-Indian locations: {foreign_locs}")
        
        # 10. Incorrect state/UT assignment (this requires complex logic, we just check how many have missing state/city/district fields)
        res = await session.execute(text(
            "SELECT count(*) FROM locations WHERE category = 'city' AND (state IS NULL OR state = '');"
        ))
        missing_state_for_city = res.scalar()
        print(f"\nMissing state for cities: {missing_state_for_city}")
        
        # 12. Missing aliases
        # (Column doesn't exist yet, so we have 0 aliases in DB)
        print("Locations with missing aliases: All (aliases column does not exist yet)")

if __name__ == "__main__":
    asyncio.run(audit())
