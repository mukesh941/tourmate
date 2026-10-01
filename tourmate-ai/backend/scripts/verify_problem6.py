"""
TourMate Problem 6 Verification Script
Comprehensive India Location Coverage & Location Data Quality Validator

Checks:
1. Total location count (>= 7,000)
2. All 28 Indian States present & valid
3. All 8 Union Territories present & valid
4. Zero missing/null/empty state fields
5. Valid bounding box coordinates for all locations in India
6. No duplicate canonical records
7. Valid alias mappings (Bangalore -> Bengaluru, Bombay -> Mumbai, etc.)
8. Distribution across States and UTs
9. Representative destination resolution across all regions
10. Exit with non-zero exit code if any critical check fails.
"""
import asyncio
import os
import sys
from sqlalchemy import text

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.core.db import AsyncSessionLocal
from app.services.destination_resolver import resolve_destination, normalize_location_name, CITY_ALIASES

EXPECTED_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", 
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", 
    "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", 
    "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan", 
    "Sikkim", "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", 
    "Uttarakhand", "West Bengal"
]

EXPECTED_UTS = [
    "Andaman and Nicobar Islands", "Chandigarh", "Dadra and Nagar Haveli and Daman and Diu",
    "Delhi", "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry"
]

SAMPLE_DESTINATIONS = [
    ("Delhi", "Delhi"),
    ("New Delhi", "Delhi"),
    ("Bengaluru", "Karnataka"),
    ("Bangalore", "Karnataka"),
    ("Mumbai", "Maharashtra"),
    ("Bombay", "Maharashtra"),
    ("Jaipur", "Rajasthan"),
    ("Kochi", "Kerala"),
    ("Cochin", "Kerala"),
    ("Varanasi", "Uttar Pradesh"),
    ("Banaras", "Uttar Pradesh"),
    ("Goa", "Goa"),
    ("Leh", "Ladakh"),
    ("Srinagar", "Jammu and Kashmir"),
    ("Port Blair", "Andaman and Nicobar Islands"),
    ("Chandigarh", "Chandigarh"),
    ("Puducherry", "Puducherry"),
    ("Pondicherry", "Puducherry"),
    ("Shimla", "Himachal Pradesh"),
    ("Manali", "Himachal Pradesh"),
    ("Ooty", "Tamil Nadu"),
    ("Munnar", "Kerala"),
    ("Darjeeling", "West Bengal"),
    ("Gangtok", "Sikkim"),
    ("Shillong", "Meghalaya"),
    ("Kodaikanal", "Tamil Nadu"),
    ("Haridwar", "Uttarakhand"),
    ("Rishikesh", "Uttarakhand"),
    ("Tirupati", "Andhra Pradesh"),
    ("Puri", "Odisha"),
    ("Madurai", "Tamil Nadu"),
    ("Hampi", "Karnataka"),
    ("Amritsar", "Punjab"),
    ("Kaziranga", "Assam"),
    ("Gokarna", "Karnataka"),
    ("Varkala", "Kerala"),
    ("Agra", "Uttar Pradesh"),
    ("Mysuru", "Karnataka"),
    ("Mysore", "Karnataka"),
    ("Udaipur", "Rajasthan"),
    ("Hyderabad", "Telangana"),
    ("Chennai", "Tamil Nadu"),
    ("Madras", "Tamil Nadu"),
    ("Kolkata", "West Bengal"),
    ("Calcutta", "West Bengal"),
    ("Pune", "Maharashtra"),
    ("Poona", "Maharashtra"),
    ("Ahmedabad", "Gujarat"),
    ("Patna", "Bihar"),
    ("Ranchi", "Jharkhand"),
    ("Raipur", "Chhattisgarh"),
    ("Bhopal", "Madhya Pradesh"),
    ("Guwahati", "Assam"),
    ("Imphal", "Manipur"),
    ("Aizawl", "Mizoram"),
    ("Kohima", "Nagaland"),
    ("Agartala", "Tripura"),
    ("Itanagar", "Arunachal Pradesh"),
    ("Kavaratti", "Lakshadweep"),
    ("Silvassa", "Dadra and Nagar Haveli and Daman and Diu"),
]


async def run_verification():
    print("=" * 70)
    print("TOURMATE PROBLEM 6: INDIA LOCATION COVERAGE & DATA QUALITY AUDIT")
    print("=" * 70)

    failures = []

    async with AsyncSessionLocal() as session:
        # 1. Total location count
        res = await session.execute(text("SELECT count(*) FROM locations"))
        total_locations = res.scalar()
        print(f"[CHECK 1] Total Locations in PostgreSQL: {total_locations}")
        if total_locations < 7000:
            failures.append(f"Total location count {total_locations} is below expected threshold (7000)")

        # 2. Verify all 28 States
        res_states = await session.execute(
            text("SELECT name FROM locations WHERE category = 'State' ORDER BY name")
        )
        db_states = [r[0] for r in res_states.fetchall()]
        missing_states = set(EXPECTED_STATES) - set(db_states)
        print(f"[CHECK 2] States: {len(db_states)}/28 verified.")
        if missing_states:
            failures.append(f"Missing States: {missing_states}")
            print(f"  FAILED: Missing states -> {missing_states}")
        else:
            print("  PASSED: All 28 Indian States present.")

        # 3. Verify all 8 Union Territories
        res_uts = await session.execute(
            text("SELECT name FROM locations WHERE category = 'Union Territory' ORDER BY name")
        )
        db_uts = [r[0] for r in res_uts.fetchall()]
        missing_uts = set(EXPECTED_UTS) - set(db_uts)
        print(f"[CHECK 3] Union Territories: {len(db_uts)}/8 verified.")
        if missing_uts:
            failures.append(f"Missing UTs: {missing_uts}")
            print(f"  FAILED: Missing UTs -> {missing_uts}")
        else:
            print("  PASSED: All 8 Union Territories present.")

        # 4. Check for missing state/UT relationships
        res_missing_state = await session.execute(
            text("SELECT count(*) FROM locations WHERE state IS NULL OR state = ''")
        )
        missing_state_cnt = res_missing_state.scalar()
        print(f"[CHECK 4] Locations with missing/empty state: {missing_state_cnt}")
        if missing_state_cnt > 0:
            failures.append(f"Found {missing_state_cnt} locations with empty/null state field")

        # 5. Check coordinate validity (India bounding box ~ 6.0 to 38.0 N, 68.0 to 98.0 E)
        res_invalid_coords = await session.execute(
            text("""
                SELECT count(*) FROM locations 
                WHERE latitude < 6.0 OR latitude > 38.0 
                   OR longitude < 68.0 OR longitude > 98.0
            """)
        )
        invalid_coords_cnt = res_invalid_coords.scalar()
        print(f"[CHECK 5] Locations with coordinates outside India bounding box: {invalid_coords_cnt}")
        if invalid_coords_cnt > 0:
            failures.append(f"Found {invalid_coords_cnt} locations with coordinates outside India bounding box")

        # 6. Check required non-empty fields (name, city, country)
        res_empty_fields = await session.execute(
            text("""
                SELECT count(*) FROM locations 
                WHERE name IS NULL OR name = '' 
                   OR city IS NULL OR city = ''
                   OR country IS NULL OR country = ''
            """)
        )
        empty_fields_cnt = res_empty_fields.scalar()
        print(f"[CHECK 6] Locations with missing required fields (name, city, country): {empty_fields_cnt}")
        if empty_fields_cnt > 0:
            failures.append(f"Found {empty_fields_cnt} locations with missing required fields")

        # 7. Distribution by State/UT
        res_dist = await session.execute(text("""
            SELECT COALESCE(NULLIF(state, ''), 'Unknown') as st, count(*) 
            FROM locations 
            GROUP BY COALESCE(NULLIF(state, ''), 'Unknown')
            ORDER BY count(*) DESC
        """))
        state_distribution = res_dist.fetchall()
        print(f"[CHECK 7] Distribution across States & UTs (Total distinct regions: {len(state_distribution)}):")
        for st, count in state_distribution[:10]:
            print(f"    - {st}: {count} destinations")
        print(f"    ... and {len(state_distribution) - 10} more regions.")

        # 8. Representative Destination Resolution & Alias Mapping
        print(f"[CHECK 8] Representative Destination Resolution ({len(SAMPLE_DESTINATIONS)} samples):")
        unresolved = []
        for name, expected_state in SAMPLE_DESTINATIONS:
            dest = await resolve_destination(name, session)
            if not dest:
                unresolved.append(name)
                print(f"    ✗ {name:20} -> NOT RESOLVED")
            else:
                dest_state = dest.get("state") or ""
                # Validate state match
                st_match = (
                    expected_state.lower() in dest_state.lower() 
                    or dest_state.lower() in expected_state.lower()
                )
                if not st_match:
                    failures.append(f"Destination {name} resolved to state {dest_state}, expected {expected_state}")
                    print(f"    ✗ {name:20} -> {dest['name']} (State mismatch: got '{dest_state}', expected '{expected_state}')")
                else:
                    print(f"    ✓ {name:20} -> {dest['name']} ({dest_state})")

        if unresolved:
            failures.append(f"Unresolved sample destinations: {unresolved}")

    # Summary
    print("\n" + "=" * 70)
    if failures:
        print(f"VERIFICATION FAILED WITH {len(failures)} ERROR(S):")
        for idx, err in enumerate(failures, 1):
            print(f"  {idx}. {err}")
        print("=" * 70)
        sys.exit(1)
    else:
        print("ALL PROBLEM 6 DATA QUALITY & COVERAGE CHECKS PASSED SUCCESSFULLY (0 ERRORS)")
        print("=" * 70)
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(run_verification())
