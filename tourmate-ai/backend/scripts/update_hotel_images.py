import asyncio
import sys
import os
from sqlalchemy import select

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.db import AsyncSessionLocal
from app.models.sql.hotel import Hotel

UNIQUE_IMAGES = [
    "https://images.unsplash.com/photo-1542314831-c6a4d14d8379?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1551882547-ff40eb0d8973?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1571896349842-33c89424de2d?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1566665797739-1674de7a421a?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1582719508461-905c673771fd?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1541971875076-8f970d573be6?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1535827841776-24afc1e255ac?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1596436889106-be35e843f974?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1512918728675-ed5a9ecdebfd?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1564501049412-61c2a3083791?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1584132967334-10e028bd69f7?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1611892440504-42a792e24d32?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1568084680786-a84f91d1153c?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1445019980597-93fa8acb246c?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1571003123894-1f0594d2b5d9?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1618773928121-c32242e63f39?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1505691938895-1758d7feb511?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1590490359683-658d3d23f972?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1582719471384-894fbb16e074?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1537726235470-1c5295eb13e0?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1592229505726-ca121723b8ef?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1608198399988-341cb27c0fe4?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1563911302283-d2bc129e7570?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1578683010236-d716f9a3f461?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1561501900-3701fa6a0864?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1631049307264-da0ec9d70304?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?auto=format&fit=crop&w=1200&q=80"
]

async def update_hotel_images():
    async with AsyncSessionLocal() as session:
        stmt = select(Hotel)
        result = await session.execute(stmt)
        hotels = result.scalars().all()
        
        print(f"Found {len(hotels)} hotels to update.")
        
        # Keep track of used images to avoid duplicates as much as possible
        used_images = set()
        
        for i, hotel in enumerate(hotels):
            # Try to pick a unique image from the pool
            available_images = [img for img in UNIQUE_IMAGES if img not in used_images]
            
            if not available_images:
                # If we run out of completely unique images, just cycle through them
                new_image = UNIQUE_IMAGES[i % len(UNIQUE_IMAGES)]
            else:
                new_image = available_images[0]
                used_images.add(new_image)
            
            # Update the hotel's images array with the new primary image
            # If there are existing images, we replace the first one, or just overwrite all with this one beautiful image to guarantee no duplicates
            hotel.images = [new_image]
            
        await session.commit()
        print("Successfully updated hotel images with unique photos!")

if __name__ == "__main__":
    asyncio.run(update_hotel_images())
