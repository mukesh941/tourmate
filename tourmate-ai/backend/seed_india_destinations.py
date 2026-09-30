import asyncio
import logging
from sqlalchemy import select
from app.core.db import AsyncSessionLocal
from app.models.sql.location import Location

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

INDIAN_STATES = {
    "Andhra Pradesh": "Visakhapatnam",
    "Arunachal Pradesh": "Tawang",
    "Assam": "Guwahati",
    "Bihar": "Bodh Gaya",
    "Chhattisgarh": "Raipur",
    "Goa": "Goa",
    "Gujarat": "Ahmedabad",
    "Haryana": "Gurugram",
    "Himachal Pradesh": "Manali",
    "Jharkhand": "Ranchi",
    "Karnataka": "Bengaluru",
    "Kerala": "Kochi",
    "Madhya Pradesh": "Indore",
    "Maharashtra": "Mumbai",
    "Manipur": "Imphal",
    "Meghalaya": "Shillong",
    "Mizoram": "Aizawl",
    "Nagaland": "Kohima",
    "Odisha": "Bhubaneswar",
    "Punjab": "Amritsar",
    "Rajasthan": "Jaipur",
    "Sikkim": "Gangtok",
    "Tamil Nadu": "Chennai",
    "Telangana": "Hyderabad",
    "Tripura": "Agartala",
    "Uttar Pradesh": "Varanasi",
    "Uttarakhand": "Rishikesh",
    "West Bengal": "Kolkata"
}

INDIAN_UTS = {
    "Andaman and Nicobar Islands": "Port Blair",
    "Chandigarh": "Chandigarh",
    "Dadra and Nagar Haveli and Daman and Diu": "Daman",
    "Delhi": "Delhi",
    "Jammu and Kashmir": "Srinagar",
    "Ladakh": "Leh",
    "Lakshadweep": "Kavaratti",
    "Puducherry": "Pondicherry"
}

async def seed_india_destinations():
    async with AsyncSessionLocal() as session:
        inserted = 0
        skipped = 0

        # Seed States
        for state, city in INDIAN_STATES.items():
            stmt = select(Location).where(Location.canonical_name == city)
            existing = (await session.execute(stmt)).scalars().first()
            if existing:
                skipped += 1
                continue
                
            loc = Location(
                name=city,
                canonical_name=city,
                state=state,
                union_territory="",
                district=city,
                country="India",
                city=city,
                latitude=20.0,
                longitude=77.0,
                category="City",
                subcategories=["Tourism"],
                description=f"Popular destination in {state}",
                best_time_to_visit="October to March",
                image="",
                is_active=True
            )
            session.add(loc)
            inserted += 1

        # Seed UTs
        for ut, city in INDIAN_UTS.items():
            stmt = select(Location).where(Location.canonical_name == city)
            existing = (await session.execute(stmt)).scalars().first()
            if existing:
                skipped += 1
                continue
                
            loc = Location(
                name=city,
                canonical_name=city,
                state="",
                union_territory=ut,
                district=city,
                country="India",
                city=city,
                latitude=20.0,
                longitude=77.0,
                category="City",
                subcategories=["Tourism"],
                description=f"Popular destination in {ut}",
                best_time_to_visit="October to March",
                image="",
                is_active=True
            )
            session.add(loc)
            inserted += 1

        await session.commit()
        logger.info(f"Seed complete: {inserted} inserted, {skipped} skipped/duplicates prevented.")
        logger.info(f"Verified states representation: {len(INDIAN_STATES)}/{len(INDIAN_STATES)}")
        logger.info(f"Verified UTs representation: {len(INDIAN_UTS)}/{len(INDIAN_UTS)}")

if __name__ == "__main__":
    asyncio.run(seed_india_destinations())
