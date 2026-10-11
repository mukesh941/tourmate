import asyncio
import uuid
import sys
import os
from datetime import datetime, date, timedelta
from decimal import Decimal

# Add the backend directory to sys.path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.core.db import AsyncSessionLocal
from app.models.sql.hotel import Hotel, RoomType, RoomInventory, RoomRate
from app.models.sql.location import Location

async def seed_hotels():
    async with AsyncSessionLocal() as session:
        # Get a location to attach the hotel to
        stmt = select(Location).limit(1)
        result = await session.execute(stmt)
        loc = result.scalar_one_or_none()
        
        if not loc:
            print("No locations found. Creating a default location.")
            loc = Location(name="Mumbai Central", city="Mumbai", country="India", latitude=18.96, longitude=72.82)
            session.add(loc)
            await session.commit()
            await session.refresh(loc)
            
        print(f"Using location: {loc.name} ({loc.id})")

        # 1. Create a Hotel
        hotel_id = uuid.uuid4()
        hotel = Hotel(
            id=hotel_id,
            name="The Grand Mumbai Resort",
            description="A luxurious 5-star resort in the heart of Mumbai featuring an infinity pool and world-class dining.",
            address="123 Marine Drive",
            city="Mumbai",
            location_id=loc.id,
            contact_phone="+91-9876543210",
            amenities=["Pool", "Breakfast", "Spa", "Wi-Fi"],
            images=[
                "https://images.unsplash.com/photo-1566073771259-6a8506099945?ixlib=rb-4.0.3&auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
            ],
            is_active=True
        )
        session.add(hotel)

        hotel2_id = uuid.uuid4()
        hotel2 = Hotel(
            id=hotel2_id,
            name="Delhi Heritage Inn",
            description="Experience authentic heritage living with modern amenities in New Delhi.",
            address="45 Connaught Place",
            city="Delhi",
            location_id=loc.id,
            contact_phone="+91-9876543211",
            amenities=["Wi-Fi", "Breakfast"],
            images=[
                "https://images.unsplash.com/photo-1542314831-c6a4d14d8379?ixlib=rb-4.0.3&auto=format&fit=crop&w=1200&q=80"
            ],
            is_active=True
        )
        session.add(hotel2)
        await session.commit()
        print("Created Hotels.")

        # 2. Create Room Types
        rt1_id = uuid.uuid4()
        rt1 = RoomType(
            id=rt1_id,
            hotel_id=hotel_id,
            name="Deluxe Ocean View",
            description="Spacious room with a beautiful view of the Arabian Sea.",
            bed_type="King",
            max_adults=2,
            max_children=1,
            total_rooms=10,
            is_active=True
        )
        session.add(rt1)

        rt2_id = uuid.uuid4()
        rt2 = RoomType(
            id=rt2_id,
            hotel_id=hotel_id,
            name="Presidential Suite",
            description="Ultra-luxury suite with private jacuzzi.",
            bed_type="King",
            max_adults=4,
            max_children=2,
            total_rooms=2,
            is_active=True
        )
        session.add(rt2)

        rt3_id = uuid.uuid4()
        rt3 = RoomType(
            id=rt3_id,
            hotel_id=hotel2_id,
            name="Standard Heritage Room",
            description="Comfortable room with antique furnishings.",
            bed_type="Queen",
            max_adults=2,
            max_children=0,
            total_rooms=15,
            is_active=True
        )
        session.add(rt3)

        await session.commit()
        print("Created Room Types.")

        # 3. Create Inventory & Rates for the next 30 days
        today = datetime.utcnow().date()
        for i in range(30):
            d = today + timedelta(days=i)
            
            # Deluxe Ocean View (rt1) - 10 rooms, 5000 INR
            inv1 = RoomInventory(room_type_id=rt1_id, inventory_date=d, total_rooms=10, reserved_rooms=0)
            rate1 = RoomRate(room_type_id=rt1_id, rate_date=d, price_per_night=5000)
            
            # Presidential Suite (rt2) - 2 rooms, 25000 INR
            inv2 = RoomInventory(room_type_id=rt2_id, inventory_date=d, total_rooms=2, reserved_rooms=0)
            rate2 = RoomRate(room_type_id=rt2_id, rate_date=d, price_per_night=25000)
            
            # Heritage Room (rt3) - 15 rooms, 2000 INR
            inv3 = RoomInventory(room_type_id=rt3_id, inventory_date=d, total_rooms=15, reserved_rooms=0)
            rate3 = RoomRate(room_type_id=rt3_id, rate_date=d, price_per_night=2000)
            
            session.add_all([inv1, rate1, inv2, rate2, inv3, rate3])

        await session.commit()
        print("Created Inventory and Rates for next 30 days.")
        print("Seeding successful!")

if __name__ == "__main__":
    asyncio.run(seed_hotels())
