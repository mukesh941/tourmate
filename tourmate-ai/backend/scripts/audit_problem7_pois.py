"""
Phase 2: Real PostgreSQL POI Database Audit Script for Problem 7.
"""
import asyncio
import os
import sys
from sqlalchemy import text

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.core.db import AsyncSessionLocal

MAJOR_DESTINATIONS = [
    "Agra", "New Delhi", "Delhi", "Jaipur", "Mumbai", "Bengaluru", "Bangalore",
    "Goa", "Varanasi", "Kochi", "Udaipur", "Amritsar", "Hyderabad", "Chennai",
    "Mysuru", "Manali", "Srinagar", "Shimla", "Darjeeling", "Gangtok", "Shillong",
    "Ooty", "Munnar", "Kodaikanal", "Hampi", "Kaziranga", "Gokarna", "Varkala",
    "Haridwar", "Rishikesh", "Puri", "Tirupati", "Madurai", "Kolkata", "Pune",
    "Ahmedabad", "Patna", "Ranchi", "Raipur", "Bhopal", "Guwahati", "Leh", "Port Blair"
]

async def audit_pois():
    print("=" * 70)
    print("PHASE 2: REAL POSTGRESQL POI DATABASE AUDIT")
    print("=" * 70)
    
    async with AsyncSessionLocal() as session:
        # 1. Total POIs
        res = await session.execute(text("SELECT count(*) FROM pois"))
        total_pois = res.scalar()
        print(f"1. Total POIs: {total_pois}")

        # 2. Locations with at least one POI
        res = await session.execute(text("SELECT count(DISTINCT location_id) FROM pois WHERE location_id IS NOT NULL"))
        locs_with_poi = res.scalar()
        print(f"2. Number of locations with at least one POI: {locs_with_poi}")

        # 3. Locations with zero POIs
        res_total_locs = await session.execute(text("SELECT count(*) FROM locations"))
        total_locs = res_total_locs.scalar()
        locs_zero_poi = total_locs - locs_with_poi
        print(f"3. Number of locations with zero POIs: {locs_zero_poi} (out of {total_locs} total locations)")

        # 4. POIs grouped by state
        res_by_state = await session.execute(text("""
            SELECT COALESCE(NULLIF(l.state, ''), 'Unknown') as state, count(p.id) as poi_count
            FROM pois p
            JOIN locations l ON p.location_id = l.id
            GROUP BY COALESCE(NULLIF(l.state, ''), 'Unknown')
            ORDER BY poi_count DESC
        """))
        pois_by_state = res_by_state.fetchall()
        print("\n4. POIs grouped by state:")
        for st, cnt in pois_by_state:
            print(f"   - {st}: {cnt} POIs")

        # 5. POIs grouped by city
        res_by_city = await session.execute(text("""
            SELECT COALESCE(NULLIF(l.city, ''), 'Unknown') as city, count(p.id) as poi_count
            FROM pois p
            JOIN locations l ON p.location_id = l.id
            GROUP BY COALESCE(NULLIF(l.city, ''), 'Unknown')
            ORDER BY poi_count DESC
        """))
        pois_by_city = res_by_city.fetchall()
        print(f"\n5. POIs grouped by city (Total cities with POIs: {len(pois_by_city)}):")
        for ct, cnt in pois_by_city:
            print(f"   - {ct}: {cnt} POIs")

        # 6. POIs grouped by category
        res_by_cat = await session.execute(text("""
            SELECT COALESCE(c.name, 'Uncategorized') as category, count(p.id) as poi_count
            FROM pois p
            LEFT JOIN categories c ON p.category_id = c.id
            GROUP BY c.name
            ORDER BY poi_count DESC
        """))
        pois_by_cat = res_by_cat.fetchall()
        print("\n6. POIs grouped by category:")
        for cat, cnt in pois_by_cat:
            print(f"   - {cat}: {cnt} POIs")

        # 7. POIs with missing names
        res = await session.execute(text("SELECT count(*) FROM pois WHERE name IS NULL OR name = ''"))
        missing_names = res.scalar()
        print(f"\n7. POIs with missing names: {missing_names}")

        # 8. POIs with missing descriptions
        res = await session.execute(text("SELECT count(*) FROM pois WHERE description IS NULL OR description = ''"))
        missing_descriptions = res.scalar()
        print(f"8. POIs with missing descriptions: {missing_descriptions}")

        # 9. POIs with missing latitude/longitude in location
        res = await session.execute(text("""
            SELECT count(p.id) FROM pois p
            JOIN locations l ON p.location_id = l.id
            WHERE l.latitude IS NULL OR l.longitude IS NULL OR (l.latitude = 0.0 AND l.longitude = 0.0)
        """))
        missing_coords = res.scalar()
        print(f"9. POIs with missing/zero coordinates: {missing_coords}")

        # 10. Coordinates outside India (6.0 - 38.0 N, 68.0 - 98.0 E)
        res = await session.execute(text("""
            SELECT count(p.id) FROM pois p
            JOIN locations l ON p.location_id = l.id
            WHERE l.latitude < 6.0 OR l.latitude > 38.0 OR l.longitude < 68.0 OR l.longitude > 98.0
        """))
        outside_india = res.scalar()
        print(f"10. POIs with coordinates outside India: {outside_india}")

        # 11. POIs referencing invalid/nonexistent locations
        res = await session.execute(text("""
            SELECT count(p.id) FROM pois p
            LEFT JOIN locations l ON p.location_id = l.id
            WHERE l.id IS NULL
        """))
        invalid_loc_refs = res.scalar()
        print(f"11. POIs referencing invalid/nonexistent locations: {invalid_loc_refs}")

        # 12. Duplicate POI names within the same location
        res = await session.execute(text("""
            SELECT p.location_id, lower(trim(p.name)), count(*) 
            FROM pois p 
            GROUP BY p.location_id, lower(trim(p.name)) 
            HAVING count(*) > 1
        """))
        dups = res.fetchall()
        print(f"12. Duplicate POI names within same location: {len(dups)}")

        # 13. POIs with suspicious placeholder/mock names
        res = await session.execute(text("""
            SELECT p.id, p.name FROM pois p 
            WHERE lower(p.name) LIKE '%test%' 
               OR lower(p.name) LIKE '%mock%' 
               OR lower(p.name) LIKE '%placeholder%'
               OR lower(p.name) LIKE '%dummy%'
               OR lower(p.name) = 'string'
        """))
        mock_pois = res.fetchall()
        print(f"13. Suspicious placeholder/mock POIs: {len(mock_pois)}")
        for mp in mock_pois:
            print(f"    - {mp[1]} (id: {mp[0]})")

        # 14. Major tourist destinations with zero POIs
        print(f"\n14. POI presence across {len(MAJOR_DESTINATIONS)} major tourist destinations:")
        zero_poi_major = []
        for dest in MAJOR_DESTINATIONS:
            res_dest_pois = await session.execute(text("""
                SELECT count(p.id) 
                FROM pois p 
                JOIN locations l ON p.location_id = l.id 
                WHERE lower(l.city) = :city OR lower(l.name) = :city OR lower(l.canonical_name) = :city
            """), {"city": dest.lower()})
            cnt = res_dest_pois.scalar()
            if cnt == 0:
                zero_poi_major.append(dest)
                print(f"    ✗ {dest:15}: 0 POIs")
            else:
                print(f"    ✓ {dest:15}: {cnt} POIs")
        
        print(f"\nSummary of Major Destinations with 0 POIs ({len(zero_poi_major)}/{len(MAJOR_DESTINATIONS)}):")
        print(zero_poi_major)

if __name__ == "__main__":
    asyncio.run(audit_pois())
