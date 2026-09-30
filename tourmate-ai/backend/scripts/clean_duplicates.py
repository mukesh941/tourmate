import asyncio
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from sqlalchemy import select, update, delete, text
from app.core.db import AsyncSessionLocal
from app.models.sql.location import Location
from app.models.sql.poi import POI
from app.models.sql.accommodation import Accommodation
from app.models.sql.transport import TransportOption
from app.models.sql.trip import Trip

async def clean_duplicates():
    print("Starting Duplicate Resolution...")
    async with AsyncSessionLocal() as session:
        # Group by name and parent_id
        res = await session.execute(text(
            "SELECT name, parent_id, array_agg(id) FROM locations "
            "GROUP BY name, parent_id HAVING count(*) > 1;"
        ))
        duplicate_groups = res.fetchall()
        
        print(f"Found {len(duplicate_groups)} duplicate groups")
        
        for name, parent_id, ids in duplicate_groups:
            # ids is a list of location IDs that are duplicates
            # We treat the first one as canonical, but prefer the one with data
            canonical_id = ids[0]
            
            print(f"Consolidating group: {name} with IDs {ids}")
            
            # Merge all others into the canonical_id
            for dup_id in ids[1:]:
                # Update POIs
                await session.execute(
                    update(POI).where(POI.location_id == dup_id).values(location_id=canonical_id)
                )
                # Update Accommodations
                await session.execute(
                    update(Accommodation).where(Accommodation.location_id == dup_id).values(location_id=canonical_id)
                )
                # Update Transport origin
                await session.execute(
                    update(TransportOption).where(TransportOption.origin_location_id == dup_id).values(origin_location_id=canonical_id)
                )
                # Update Transport destination
                await session.execute(
                    update(TransportOption).where(TransportOption.destination_location_id == dup_id).values(destination_location_id=canonical_id)
                )
                # Update Trips
                await session.execute(
                    update(Trip).where(Trip.location_id == dup_id).values(location_id=canonical_id)
                )
                
                # Delete duplicate
                await session.execute(delete(Location).where(Location.id == dup_id))
                
        await session.commit()
        print("Duplicate Resolution complete.")

if __name__ == "__main__":
    asyncio.run(clean_duplicates())
