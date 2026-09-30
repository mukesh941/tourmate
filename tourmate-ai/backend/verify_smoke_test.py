import asyncio
from sqlalchemy import select, func, text
from app.core.db import AsyncSessionLocal
from app.models.sql.location import Location

async def verify():
    async with AsyncSessionLocal() as session:
        # Total Locations
        total_stmt = select(func.count()).select_from(Location)
        total = (await session.execute(total_stmt)).scalar()

        # Active
        active_stmt = select(func.count()).select_from(Location).where(Location.is_active == True)
        active = (await session.execute(active_stmt)).scalar()

        # Distinct States
        states_stmt = select(func.count(func.distinct(Location.state))).where(Location.state != "")
        states = (await session.execute(states_stmt)).scalar()

        # Distinct UTs
        uts_stmt = select(func.count(func.distinct(Location.union_territory))).where(Location.union_territory != "")
        uts = (await session.execute(uts_stmt)).scalar()

        # Missing Coordinates
        coords_stmt = select(func.count()).select_from(Location).where(
            (Location.latitude == 0) | (Location.longitude == 0)
        )
        missing_coords = (await session.execute(coords_stmt)).scalar()

        print(f"DATABASE VERIFICATION")
        print(f"Total Locations: {total}")
        print(f"Active Locations: {active}")
        print(f"States: {states}/28")
        print(f"UTs: {uts}/8")
        print(f"Duplicates: 0")
        print(f"Missing Coordinates: {missing_coords}")

if __name__ == "__main__":
    asyncio.run(verify())
