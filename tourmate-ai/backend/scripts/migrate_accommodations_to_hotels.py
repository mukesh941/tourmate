import asyncio
import sys
import os
import uuid
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.orm import selectinload

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.db import AsyncSessionLocal
from app.models.sql.accommodation import Accommodation
from app.models.sql.hotel import Hotel, RoomType, RoomInventory, RoomRate

ACC_IMAGE_MAP = {
    # Agra
    "The Oberoi Amarvilas": "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=1200&q=80",
    "Tajview - IHCL SeleQtions": "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=1200&q=80",
    "Zostel Agra": "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?auto=format&fit=crop&w=1200&q=80",
    # New Delhi
    "The Imperial New Delhi": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1200&q=80",
    "Bloomrooms @ Janpath": "https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?auto=format&fit=crop&w=1200&q=80",
    "The Claridges New Delhi": "https://images.unsplash.com/photo-1566665797739-1674de7a421a?auto=format&fit=crop&w=1200&q=80",
    # Jaipur
    "Rambagh Palace": "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=1200&q=80",
    "Alsisar Haveli": "https://images.unsplash.com/photo-1566665797739-1674de7a421a?auto=format&fit=crop&w=1200&q=80",
    "Zostel Jaipur": "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?auto=format&fit=crop&w=1200&q=80",
    # Mumbai
    "The Taj Mahal Palace": "https://images.unsplash.com/photo-1582719508461-905c673771fd?auto=format&fit=crop&w=1200&q=80",
    "Residency Hotel Fort": "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=1200&q=80",
    "Zostel Mumbai": "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?auto=format&fit=crop&w=1200&q=80",
    # Bengaluru
    "The Leela Palace Bengaluru": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1200&q=80",
    "Bloomrooms @ Indiranagar": "https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?auto=format&fit=crop&w=1200&q=80",
    # Goa
    "Taj Fort Aguada Resort & Spa": "https://images.unsplash.com/photo-1582719508461-905c673771fd?auto=format&fit=crop&w=1200&q=80",
    "Santana Beach Resort": "https://images.unsplash.com/photo-1571896349842-33c89424de2d?auto=format&fit=crop&w=1200&q=80",
    "Zostel Goa (Morjim)": "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?auto=format&fit=crop&w=1200&q=80",
    # Varanasi
    "BrijRama Palace": "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=1200&q=80",
    "Stops Hostel Varanasi": "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?auto=format&fit=crop&w=1200&q=80",
    # Kochi / Kerala
    "Brunton Boatyard": "https://images.unsplash.com/photo-1571896349842-33c89424de2d?auto=format&fit=crop&w=1200&q=80",
    "Zostel Kochi": "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?auto=format&fit=crop&w=1200&q=80",
    # Udaipur
    "Taj Lake Palace": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1200&q=80",
    "Zostel Udaipur": "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?auto=format&fit=crop&w=1200&q=80",
    # Amritsar
    "Taj Swarna Amritsar": "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=1200&q=80",
    "Jugaadus Hostel": "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?auto=format&fit=crop&w=1200&q=80",
    # Hyderabad
    "Taj Falaknuma Palace": "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=1200&q=80",
    # Chennai
    "Taj Coromandel": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1200&q=80",
    # Mysuru
    "Lalitha Mahal Palace Hotel": "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=1200&q=80",
    # Manali
    "Johnson Lodge & Spa": "https://images.unsplash.com/photo-1512918728675-ed5a9ecdebfd?auto=format&fit=crop&w=1200&q=80",
    "Zostel Manali": "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?auto=format&fit=crop&w=1200&q=80",
    # Srinagar / Kashmir
    "The Lalit Grand Palace Srinagar": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1200&q=80",
    "Zostel Srinagar": "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?auto=format&fit=crop&w=1200&q=80",
}

async def migrate_accommodations():
    async with AsyncSessionLocal() as session:
        # Get all old accommodations
        from app.models.sql.media import AccommodationImage
        stmt = select(Accommodation).options(
            selectinload(Accommodation.location), 
            selectinload(Accommodation.accommodation_images).selectinload(AccommodationImage.image)
        )
        result = await session.execute(stmt)
        accommodations = result.scalars().all()
        
        if not accommodations:
            print("No old accommodations found.")
            return

        print(f"Found {len(accommodations)} accommodations. Migrating...")
        
        for acc in accommodations:
            # Check if this hotel already exists
            exist_stmt = select(Hotel).where(Hotel.name == acc.name, Hotel.location_id == acc.location_id)
            exist_res = await session.execute(exist_stmt)
            if exist_res.scalar_one_or_none():
                print(f"Hotel '{acc.name}' already migrated. Skipping.")
                continue

            # Build images list
            images = []
            if acc.name in ACC_IMAGE_MAP:
                images.append(ACC_IMAGE_MAP[acc.name])
            if acc.accommodation_images:
                sorted_imgs = sorted(acc.accommodation_images, key=lambda x: (not x.is_primary, x.display_order))
                for ai in sorted_imgs:
                    if ai.image and ai.image.url:
                        url = ai.image.url
                        if "wikimedia.org" not in url and url != "photo-1542314831-c6a4d14ce8a1" and url not in images:
                            images.append(url)
            
            if not images and acc.name in ACC_IMAGE_MAP:
                images.append(ACC_IMAGE_MAP[acc.name])

            # Provide default if still empty
            if not images:
                 images.append("data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%22800%22%20height%3D%22600%22%20viewBox%3D%220%200%20800%20600%22%20fill%3D%22none%22%3E%3Crect%20width%3D%22800%22%20height%3D%22600%22%20fill%3D%22%23f8fafc%22%2F%3E%3Cpath%20d%3D%22M360%20320h80v40h-80zM350%20220h100v180H350z%22%20fill%3D%22%2394a3b8%22%2F%3E%3Ctext%20x%3D%22400%22%20y%3D%22430%22%20fill%3D%22%2364748b%22%20font-family%3D%22system-ui%22%20font-size%3D%2218%22%20text-anchor%3D%22middle%22%3ETourMate%20Verified%20Accommodation%3C%2Ftext%3E%3C%2Fsvg%3E")

            city_name = acc.location.city if acc.location and acc.location.city else (acc.location.name if acc.location else "Unknown City")
            
            hotel = Hotel(
                id=uuid.uuid4(),
                name=acc.name,
                description=f"A beautiful {acc.budget_tier} {acc.type} in {city_name}.",
                address="City Center",
                city=city_name,
                location_id=acc.location_id,
                contact_phone="+91-0000000000",
                amenities=["Wi-Fi", "Breakfast"] if acc.budget_tier in ["budget", "moderate"] else ["Wi-Fi", "Breakfast", "Pool", "Spa", "Room Service"],
                images=images,
                is_active=True
            )
            session.add(hotel)
            await session.flush() # get hotel.id

            # Create Room Types
            rt = RoomType(
                id=uuid.uuid4(),
                hotel_id=hotel.id,
                name="Standard Room",
                description="Comfortable standard accommodation.",
                bed_type="Double",
                max_adults=2,
                total_rooms=10,
                is_active=True
            )
            session.add(rt)
            
            if acc.budget_tier == "luxury":
                rt_lux = RoomType(
                    id=uuid.uuid4(),
                    hotel_id=hotel.id,
                    name="Luxury Suite",
                    description="Luxurious suite with premium amenities.",
                    bed_type="King",
                    max_adults=3,
                    total_rooms=5,
                    is_active=True
                )
                session.add(rt_lux)

            await session.flush()
            
            # Create Inventory & Rates for 30 days
            from datetime import datetime, timezone, timedelta
            today = datetime.now(timezone.utc).date()
            
            price = float(acc.price_per_night) if float(acc.price_per_night) > 0 else (5000.0 if acc.budget_tier == "luxury" else 2000.0)
            
            for i in range(30):
                d = today + timedelta(days=i)
                inv = RoomInventory(room_type_id=rt.id, inventory_date=d, total_rooms=10, reserved_rooms=0)
                rate = RoomRate(room_type_id=rt.id, rate_date=d, price_per_night=price)
                session.add_all([inv, rate])
                
                if acc.budget_tier == "luxury":
                    inv_lux = RoomInventory(room_type_id=rt_lux.id, inventory_date=d, total_rooms=5, reserved_rooms=0)
                    rate_lux = RoomRate(room_type_id=rt_lux.id, rate_date=d, price_per_night=price * 1.5)
                    session.add_all([inv_lux, rate_lux])

        await session.commit()
        print("Successfully migrated all old accommodations to the new Hotel models.")

if __name__ == "__main__":
    asyncio.run(migrate_accommodations())
