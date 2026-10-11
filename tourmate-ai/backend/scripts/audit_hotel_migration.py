import asyncio
import sys
import os
from sqlalchemy import select, func
from datetime import datetime, timedelta, date

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.db import AsyncSessionLocal
from app.models.sql.accommodation import Accommodation
from app.models.sql.hotel import Hotel, RoomType, RoomInventory, RoomRate, HotelBooking

async def run_audit():
    async with AsyncSessionLocal() as session:
        # 1. Count accommodations
        stmt = select(func.count(Accommodation.id))
        acc_count = (await session.execute(stmt)).scalar()
        
        # 2. Count hotels
        stmt = select(func.count(Hotel.id))
        hotel_count = (await session.execute(stmt)).scalar()
        
        # 3. Check duplication prevention
        stmt = select(Hotel.name).group_by(Hotel.name, Hotel.location_id).having(func.count(Hotel.id) > 1)
        duplicates = (await session.execute(stmt)).scalars().all()
        
        # 4. Check generated inventory and rates
        stmt = select(func.count(RoomInventory.id))
        inv_count = (await session.execute(stmt)).scalar()
        
        stmt = select(func.count(RoomRate.id))
        rate_count = (await session.execute(stmt)).scalar()
        
        print("--- AUDIT RESULTS ---")
        print(f"Legacy Accommodations: {acc_count}")
        print(f"Migrated Hotels: {hotel_count}")
        print(f"Duplicate Hotels Found: {len(duplicates)} {duplicates if duplicates else ''}")
        print(f"Generated Inventory Records: {inv_count}")
        print(f"Generated Rate Records: {rate_count}")
        
        if acc_count > 0:
            print("Legacy records were NOT deleted.")
            
        print("Is generated inventory and rates DEMO data? YES. Sourced from a python script.")

if __name__ == "__main__":
    asyncio.run(run_audit())
