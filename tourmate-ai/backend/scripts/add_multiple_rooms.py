import asyncio
import sys
import os
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import select

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.db import AsyncSessionLocal
from app.models.sql.hotel import Hotel, RoomType, RoomInventory, RoomRate

async def add_multiple_rooms():
    async with AsyncSessionLocal() as session:
        stmt = select(Hotel)
        result = await session.execute(stmt)
        hotels = result.scalars().all()
        
        for hotel in hotels:
            # Check existing rooms
            stmt_rt = select(RoomType).where(RoomType.hotel_id == hotel.id)
            res_rt = await session.execute(stmt_rt)
            existing_rooms = res_rt.scalars().all()
            
            room_names = [r.name for r in existing_rooms]
            
            new_rooms = []
            
            if "Deluxe Room" not in room_names:
                rt_deluxe = RoomType(
                    id=uuid.uuid4(),
                    hotel_id=hotel.id,
                    name="Deluxe Room",
                    description="Spacious room with modern amenities and a great view.",
                    bed_type="King",
                    max_adults=3,
                    total_rooms=8,
                    is_active=True
                )
                new_rooms.append(rt_deluxe)
                
            if "Executive Suite" not in room_names:
                rt_suite = RoomType(
                    id=uuid.uuid4(),
                    hotel_id=hotel.id,
                    name="Executive Suite",
                    description="Luxurious suite with a separate living area and premium services.",
                    bed_type="King",
                    max_adults=4,
                    total_rooms=3,
                    is_active=True
                )
                new_rooms.append(rt_suite)
                
            if new_rooms:
                session.add_all(new_rooms)
                await session.flush()
                
                today = datetime.now(timezone.utc).date()
                for rt in new_rooms:
                    base_price = 3000.0 if rt.name == "Deluxe Room" else 6000.0
                    for i in range(30):
                        d = today + timedelta(days=i)
                        inv = RoomInventory(room_type_id=rt.id, inventory_date=d, total_rooms=rt.total_rooms, reserved_rooms=0)
                        rate = RoomRate(room_type_id=rt.id, rate_date=d, price_per_night=base_price)
                        session.add_all([inv, rate])
                        
        await session.commit()
        print("Added multiple room types to all existing hotels!")

if __name__ == "__main__":
    asyncio.run(add_multiple_rooms())
