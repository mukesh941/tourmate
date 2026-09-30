"""
Fix empty state fields for cities using indian_cities.json reference data.

The 6,643 cities with empty state fields need their state populated.
This script uses indian_cities.json (1,221 records with name+state) to
fill in state fields and then links cities to state records via parent_id.

Strategy:
1. Load indian_cities.json: {name -> state} lookup
2. For each city with empty state field: look up state from JSON
3. Update the state field in the DB
4. Link cities to state records via parent_id

Does NOT modify coordinates, names, or any other fields.
"""
import asyncio
import json
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select, text, update, func
from app.core.db import AsyncSessionLocal
from app.models.sql.location import Location

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Known Indian state for capital/major cities with empty state
# These are major Indian cities that may not be in the JSON
MANUAL_STATE_MAP = {
    "Delhi": "Delhi",
    "New Delhi": "Delhi",
    "Port Blair": "Andaman and Nicobar Islands",
    "Leh": "Ladakh",
    "Kavaratti": "Lakshadweep",
    "Srinagar": "Jammu and Kashmir",
    "Jammu": "Jammu and Kashmir",
    "Chandigarh": "Chandigarh",
    "Silvassa": "Dadra and Nagar Haveli",
    "Daman": "Daman and Diu",
    "Diu": "Daman and Diu",
    "Panaji": "Goa",
    "Puducherry": "Puducherry",
    "Pondicherry": "Puducherry",
    "Mumbai": "Maharashtra",
    "Pune": "Maharashtra",
    "Nashik": "Maharashtra",
    "Nagpur": "Maharashtra",
    "Aurangabad": "Maharashtra",
    "Thane": "Maharashtra",
    "Kolhapur": "Maharashtra",
    "Solapur": "Maharashtra",
    "Satara": "Maharashtra",
    "Jalgaon": "Maharashtra",
    "Bengaluru": "Karnataka",
    "Bangalore": "Karnataka",
    "Mysuru": "Karnataka",
    "Mangaluru": "Karnataka",
    "Hubballi": "Karnataka",
    "Dharwad": "Karnataka",
    "Belagavi": "Karnataka",
    "Tumakuru": "Karnataka",
    "Shivamogga": "Karnataka",
    "Davangere": "Karnataka",
    "Ballari": "Karnataka",
    "Kalaburagi": "Karnataka",
    "Udupi": "Karnataka",
    "Hassan": "Karnataka",
    "Chikmagalur": "Karnataka",
    "Hampi": "Karnataka",
    "Badami": "Karnataka",
    "Chennai": "Tamil Nadu",
    "Coimbatore": "Tamil Nadu",
    "Madurai": "Tamil Nadu",
    "Tiruchirappalli": "Tamil Nadu",
    "Salem": "Tamil Nadu",
    "Tirunelveli": "Tamil Nadu",
    "Kanchipuram": "Tamil Nadu",
    "Thanjavur": "Tamil Nadu",
    "Ooty": "Tamil Nadu",
    "Kodaikanal": "Tamil Nadu",
    "Rameswaram": "Tamil Nadu",
    "Kanyakumari": "Tamil Nadu",
    "Mahabalipuram": "Tamil Nadu",
    "Hyderabad": "Telangana",
    "Warangal": "Telangana",
    "Nizamabad": "Telangana",
    "Karimnagar": "Telangana",
    "Visakhapatnam": "Andhra Pradesh",
    "Vijayawada": "Andhra Pradesh",
    "Tirupati": "Andhra Pradesh",
    "Kochi": "Kerala",
    "Thiruvananthapuram": "Kerala",
    "Kozhikode": "Kerala",
    "Thrissur": "Kerala",
    "Kannur": "Kerala",
    "Kollam": "Kerala",
    "Alappuzha": "Kerala",
    "Munnar": "Kerala",
    "Varkala": "Kerala",
    "Kovalam": "Kerala",
    "Ahmedabad": "Gujarat",
    "Surat": "Gujarat",
    "Vadodara": "Gujarat",
    "Rajkot": "Gujarat",
    "Gandhinagar": "Gujarat",
    "Bhavnagar": "Gujarat",
    "Junagadh": "Gujarat",
    "Jamnagar": "Gujarat",
    "Anand": "Gujarat",
    "Dwarka": "Gujarat",
    "Somnath": "Gujarat",
    "Jaipur": "Rajasthan",
    "Jodhpur": "Rajasthan",
    "Udaipur": "Rajasthan",
    "Ajmer": "Rajasthan",
    "Bikaner": "Rajasthan",
    "Kota": "Rajasthan",
    "Pushkar": "Rajasthan",
    "Jaisalmer": "Rajasthan",
    "Alwar": "Rajasthan",
    "Bharatpur": "Rajasthan",
    "Mount Abu": "Rajasthan",
    "Kolkata": "West Bengal",
    "Darjeeling": "West Bengal",
    "Siliguri": "West Bengal",
    "Durgapur": "West Bengal",
    "Asansol": "West Bengal",
    "Howrah": "West Bengal",
    "Lucknow": "Uttar Pradesh",
    "Agra": "Uttar Pradesh",
    "Varanasi": "Uttar Pradesh",
    "Kanpur": "Uttar Pradesh",
    "Allahabad": "Uttar Pradesh",
    "Prayagraj": "Uttar Pradesh",
    "Mathura": "Uttar Pradesh",
    "Vrindavan": "Uttar Pradesh",
    "Gorakhpur": "Uttar Pradesh",
    "Meerut": "Uttar Pradesh",
    "Noida": "Uttar Pradesh",
    "Ghaziabad": "Uttar Pradesh",
    "Rishikesh": "Uttarakhand",
    "Haridwar": "Uttarakhand",
    "Dehradun": "Uttarakhand",
    "Nainital": "Uttarakhand",
    "Mussoorie": "Uttarakhand",
    "Auli": "Uttarakhand",
    "Jim Corbett": "Uttarakhand",
    "Patna": "Bihar",
    "Bodh Gaya": "Bihar",
    "Nalanda": "Bihar",
    "Gaya": "Bihar",
    "Ranchi": "Jharkhand",
    "Jamshedpur": "Jharkhand",
    "Dhanbad": "Jharkhand",
    "Raipur": "Chhattisgarh",
    "Bhopal": "Madhya Pradesh",
    "Indore": "Madhya Pradesh",
    "Jabalpur": "Madhya Pradesh",
    "Gwalior": "Madhya Pradesh",
    "Ujjain": "Madhya Pradesh",
    "Pachmarhi": "Madhya Pradesh",
    "Khajuraho": "Madhya Pradesh",
    "Kanha": "Madhya Pradesh",
    "Bandhavgarh": "Madhya Pradesh",
    "Amritsar": "Punjab",
    "Ludhiana": "Punjab",
    "Chandigarh": "Punjab",
    "Jalandhar": "Punjab",
    "Gurugram": "Haryana",
    "Faridabad": "Haryana",
    "Shimla": "Himachal Pradesh",
    "Manali": "Himachal Pradesh",
    "Dharamshala": "Himachal Pradesh",
    "Kullu": "Himachal Pradesh",
    "Guwahati": "Assam",
    "Jorhat": "Assam",
    "Kaziranga": "Assam",
    "Majuli": "Assam",
    "Shillong": "Meghalaya",
    "Cherrapunjee": "Meghalaya",
    "Cherrapunji": "Meghalaya",
    "Aizawl": "Mizoram",
    "Imphal": "Manipur",
    "Kohima": "Nagaland",
    "Agartala": "Tripura",
    "Bhubaneswar": "Odisha",
    "Puri": "Odisha",
    "Chilika": "Odisha",
    "Konark": "Odisha",
    "Tawang": "Arunachal Pradesh",
    "Ziro": "Arunachal Pradesh",
    "Itanagar": "Arunachal Pradesh",
    "Gangtok": "Sikkim",
    "Lachen": "Sikkim",
    "Pelling": "Sikkim",
    "Gir": "Gujarat",
    "Bekal": "Kerala",
}


async def fix_city_states():
    # Load indian_cities.json
    try:
        with open("indian_cities.json", "r", encoding="utf-8") as f:
            cities_json = json.load(f)
        json_map = {c["name"].lower().strip(): c["state"] for c in cities_json if c.get("name") and c.get("state")}
        logger.info("Loaded %d city->state mappings from indian_cities.json", len(json_map))
    except Exception as e:
        logger.warning("Could not load indian_cities.json: %s", e)
        json_map = {}

    # Merge with manual map
    manual_lower = {k.lower(): v for k, v in MANUAL_STATE_MAP.items()}
    combined_map = {**json_map, **manual_lower}
    logger.info("Combined map has %d entries", len(combined_map))

    updated_state = 0
    linked = 0
    not_found = 0

    async with AsyncSessionLocal() as session:
        # Build state UUID map
        state_result = await session.execute(
            select(Location.id, Location.name)
            .where(Location.location_type == "state")
        )
        state_rows = state_result.fetchall()
        state_uuid_map = {}
        for row in state_rows:
            key = row.name.lower().strip()
            state_uuid_map[key] = row.id
            # Also add common variants
            # Handle "(UT)" suffix
            if " (ut)" in key:
                state_uuid_map[key.replace(" (ut)", "")] = row.id
            if " (nct)" in key:
                state_uuid_map[key.replace(" (nct)", "")] = row.id

        logger.info("Built state UUID map with %d entries", len(state_uuid_map))

        # Get all cities with empty state
        unlinked_result = await session.execute(
            select(Location.id, Location.name, Location.location_type)
            .where(
                Location.parent_id.is_(None),
                Location.location_type.in_(["city", "town"])
            )
        )
        unlinked = unlinked_result.fetchall()
        logger.info("Found %d cities without parent_id to fix", len(unlinked))

        batch_updates = []
        for row in unlinked:
            city_key = row.name.lower().strip()
            state_name = combined_map.get(city_key)

            if not state_name:
                not_found += 1
                continue

            state_id = state_uuid_map.get(state_name.lower().strip())
            if not state_id:
                not_found += 1
                continue

            batch_updates.append({
                "loc_id": row.id,
                "state_name": state_name,
                "parent_id": state_id,
            })

        logger.info("Will update %d records", len(batch_updates))

        # Execute updates in batches
        BATCH_SIZE = 500
        for i in range(0, len(batch_updates), BATCH_SIZE):
            batch = batch_updates[i:i + BATCH_SIZE]
            for item in batch:
                await session.execute(
                    update(Location)
                    .where(Location.id == item["loc_id"])
                    .values(
                        parent_id=item["parent_id"],
                        state=item["state_name"],
                    )
                )
            await session.commit()
            linked += len(batch)
            logger.info("Updated batch %d-%d (%d total)", i, i + len(batch), linked)

    logger.info("=" * 60)
    logger.info("City state fix complete:")
    logger.info("  Updated (state + parent_id): %d", linked)
    logger.info("  Not found in map: %d", not_found)
    logger.info("=" * 60)

    return linked, not_found


if __name__ == "__main__":
    asyncio.run(fix_city_states())
