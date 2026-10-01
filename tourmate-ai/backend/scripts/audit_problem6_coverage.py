import asyncio
import os
import sys
from sqlalchemy import text

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.core.db import AsyncSessionLocal
from app.services.destination_resolver import resolve_destination

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

async def audit():
    print("==================================================")
    print("AUDITING PROBLEM 6 LOCATION COVERAGE & QUALITY")
    print("==================================================")
    
    async with AsyncSessionLocal() as session:
        # 1. Total counts
        res = await session.execute(text("SELECT count(*) FROM locations"))
        total = res.scalar()
        print(f"Total location records: {total}")

        # 2. Check 28 states + 8 UTs
        res_states = await session.execute(text("SELECT name, category FROM locations WHERE category = 'State' ORDER BY name"))
        db_states = [r[0] for r in res_states.fetchall()]
        print(f"\nStates in DB ({len(db_states)}/28):", db_states)
        missing_states = set(EXPECTED_STATES) - set(db_states)
        assert len(missing_states) == 0, f"Missing states: {missing_states}"

        res_uts = await session.execute(text("SELECT name, category FROM locations WHERE category = 'Union Territory' ORDER BY name"))
        db_uts = [r[0] for r in res_uts.fetchall()]
        print(f"\nUnion Territories in DB ({len(db_uts)}/8):", db_uts)
        missing_uts = set(EXPECTED_UTS) - set(db_uts)
        assert len(missing_uts) == 0, f"Missing UTs: {missing_uts}"

        # 3. Check distribution across States and UTs
        res_dist = await session.execute(text("""
            SELECT COALESCE(NULLIF(state, ''), 'Unknown') as st, count(*) 
            FROM locations 
            GROUP BY COALESCE(NULLIF(state, ''), 'Unknown')
            ORDER BY count(*) DESC
        """))
        print("\nLocations per State/UT (top 15):")
        for r in res_dist.fetchall()[:15]:
            print(f"  - {r[0]}: {r[1]} locations")

        # 4. Check for any missing state fields
        res_missing_state = await session.execute(text("SELECT count(*) FROM locations WHERE state IS NULL OR state = ''"))
        missing_state_cnt = res_missing_state.scalar()
        print(f"\nLocations with empty state: {missing_state_cnt}")
        assert missing_state_cnt == 0, f"Found {missing_state_cnt} locations with empty state!"

        # 5. Check sample destinations resolution
        print("\nTesting sample destinations resolution:")
        resolved_count = 0
        unresolved = []
        for name, expected_state in SAMPLE_DESTINATIONS:
            dest = await resolve_destination(name, session)
            if dest:
                resolved_count += 1
                state_match = expected_state.lower() in (dest.get("state") or "").lower() or (dest.get("state") or "").lower() in expected_state.lower()
                print(f"  ✓ {name:15} -> {dest['name']} ({dest.get('state')}) [State Match: {state_match}]")
            else:
                unresolved.append(name)
                print(f"  ✗ {name:15} -> NOT RESOLVED")

        print(f"\nResolved {resolved_count}/{len(SAMPLE_DESTINATIONS)} sample destinations.")
        if unresolved:
            print("Unresolved destinations:", unresolved)

if __name__ == "__main__":
    asyncio.run(audit())
