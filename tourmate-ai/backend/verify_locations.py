import asyncio
from collections import defaultdict
from sqlalchemy import select, create_engine
from app.core.config import settings
from app.models.sql.location import Location
from app.core.database import get_db

async def verify():
    # PostgreSQL Connection
    engine = create_engine(settings.sync_database_url)
    with engine.begin() as conn:
        res = conn.execute(select(Location))
        sql_locations = res.mappings().fetchall()

    # MongoDB Connection
    mongo_db = get_db()
    mongo_destinations = await mongo_db.destinations.find({}).to_list(length=None)

    sql_count = len(sql_locations)
    mongo_count = len(mongo_destinations)

    # States & UTs (from the lists)
    indian_states = {
        "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
        "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
        "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
        "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
        "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal"
    }
    indian_uts = {
        "Andaman and Nicobar Islands", "Chandigarh", "Dadra and Nagar Haveli and Daman and Diu",
        "Delhi", "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry"
    }

    found_states = set()
    found_uts = set()

    for loc in sql_locations:
        state = loc["state"]
        if state in indian_states:
            found_states.add(state)
        elif state in indian_uts:
            found_uts.add(state)

    for dest in mongo_destinations:
        state = dest.get("state")
        if state in indian_states:
            found_states.add(state)
        elif state in indian_uts:
            found_uts.add(state)

    # Check Duplicates (name + state)
    seen_sql = set()
    duplicates = 0
    for loc in sql_locations:
        key = f"{loc['name']}|{loc['state']}".lower()
        if key in seen_sql:
            duplicates += 1
        seen_sql.add(key)

    seen_mongo = set()
    for dest in mongo_destinations:
        name = dest.get("name", "")
        state = dest.get("state", "")
        key = f"{name}|{state}".lower()
        if key in seen_mongo:
            duplicates += 1
        seen_mongo.add(key)

    # Verify Categories
    cat_counts = defaultdict(int)
    for dest in mongo_destinations:
        categories = dest.get("categories", [])
        for c in categories:
            cat_counts[c] += 1

    print(f"PostgreSQL locations: {sql_count}")
    print(f"MongoDB destinations: {mongo_count}")
    print(f"States: {len(found_states)}/28")
    print(f"Union Territories: {len(found_uts)}/8")
    print(f"Duplicate locations: {duplicates}")
    print("")
    print(f"City: {cat_counts.get('city', 0)}")
    print(f"Town: {cat_counts.get('town', 0)}")
    print(f"Hill station: {cat_counts.get('hill_station', 0)}")
    print(f"Beach: {cat_counts.get('beach', 0)}")
    print(f"Heritage: {cat_counts.get('heritage', 0)}")
    print(f"Pilgrimage: {cat_counts.get('pilgrimage', 0)}")
    print(f"Wildlife: {cat_counts.get('wildlife', 0)}")
    print(f"Nature: {cat_counts.get('nature', 0)}")
    print("")

if __name__ == "__main__":
    asyncio.run(verify())
