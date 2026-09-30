import asyncio
from sqlalchemy import select, update, delete
from app.core.db import AsyncSessionLocal
from app.models.sql.location import Location
from app.models.sql.poi import POI
from app.models.sql.accommodation import Accommodation
from app.models.sql.transport import TransportOption
from app.models.sql.trip import Trip

async def clean_duplicates():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Location))
        locations = result.scalars().all()
        
        seen = {}
        duplicates = []
        for loc in locations:
            key = f"{loc.name.lower()}|{loc.state.lower()}"
            if key in seen:
                duplicates.append((seen[key], loc))
            else:
                seen[key] = loc
                
        print(f"Found {len(duplicates)} duplicate pairs in PostgreSQL")
        
        for orig, dup in duplicates:
            # Identify which is the true canonical record (the one with actual coordinates, not 20.0/77.0)
            if dup.latitude == 20.0 and dup.longitude == 77.0:
                canonical_loc = orig
                duplicate_loc = dup
            elif orig.latitude == 20.0 and orig.longitude == 77.0:
                canonical_loc = dup
                duplicate_loc = orig
            else:
                print(f"Skipping {orig.name}, no 20.0/77.0 placeholder found.")
                continue
                
            print(f"Consolidating {duplicate_loc.name} -> keeping canonical {canonical_loc.id}, removing {duplicate_loc.id}")
            
            # Update POIs
            await session.execute(
                update(POI).where(POI.location_id == duplicate_loc.id).values(location_id=canonical_loc.id)
            )
            # Update Accommodations
            await session.execute(
                update(Accommodation).where(Accommodation.location_id == duplicate_loc.id).values(location_id=canonical_loc.id)
            )
            # Update Transport origin
            await session.execute(
                update(TransportOption).where(TransportOption.origin_location_id == duplicate_loc.id).values(origin_location_id=canonical_loc.id)
            )
            # Update Transport destination
            await session.execute(
                update(TransportOption).where(TransportOption.destination_location_id == duplicate_loc.id).values(destination_location_id=canonical_loc.id)
            )
            # Update Trips
            await session.execute(
                update(Trip).where(Trip.location_id == duplicate_loc.id).values(location_id=canonical_loc.id)
            )
            
            # Delete the duplicate
            await session.execute(
                delete(Location).where(Location.id == duplicate_loc.id)
            )
            
        await session.commit()
        print("Cleanup complete.")

if __name__ == "__main__":
    asyncio.run(clean_duplicates())
