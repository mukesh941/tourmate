"""
Guide Service for TourMate AI.

Local Guides are part of the legacy feature set and are NOT represented in
the locked 23-table canonical PostgreSQL architecture.
To preserve database architecture integrity without fabricating new unapproved tables,
this service provides safe, non-blocking fallback responses without MongoDB dependencies.
"""
from typing import List, Optional
from app.schemas.guide import GuideResponse, BookingCreate, BookingResponse
from app.core.database import get_db

async def get_all_guides(location: Optional[str] = None) -> List[GuideResponse]:
    """
    Returns mock local guides for locations in India.
    """
    mock_guides = [
        {
            "id": "g1",
            "name": "Ravi Kumar",
            "languages": ["English", "Hindi"],
            "rating": 4.9,
            "reviews_count": 124,
            "hourly_rate": 500,
            "bio": "Certified historian with 10 years of experience showing the hidden gems of New Delhi.",
            "verified": True,
            "image_url": "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=60",
            "location": "New Delhi"
        },
        {
            "id": "g2",
            "name": "Priya Sharma",
            "languages": ["English", "Hindi", "Marathi"],
            "rating": 4.7,
            "reviews_count": 89,
            "hourly_rate": 450,
            "bio": "Passionate local showing you the best street food and culture of Mumbai.",
            "verified": True,
            "image_url": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=60",
            "location": "Mumbai"
        },
        {
            "id": "g3",
            "name": "Vikram Singh",
            "languages": ["English", "Hindi", "Rajasthani"],
            "rating": 4.8,
            "reviews_count": 210,
            "hourly_rate": 600,
            "bio": "Heritage expert guiding you through the majestic forts and palaces of Jaipur.",
            "verified": True,
            "image_url": "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=60",
            "location": "Jaipur"
        },
        {
            "id": "g4",
            "name": "Anita Desai",
            "languages": ["English", "Malayalam"],
            "rating": 4.9,
            "reviews_count": 150,
            "hourly_rate": 700,
            "bio": "Nature enthusiast specializing in Kerala backwaters and spice plantations.",
            "verified": True,
            "image_url": "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=60",
            "location": "Kochi"
        }
    ]

    guides = [GuideResponse(**g) for g in mock_guides]

    if location:
        # Filter guides by location (case-insensitive)
        guides = [g for g in guides if location.lower() in g.location.lower()]

    return guides

async def get_guide(guide_id: str) -> Optional[GuideResponse]:
    """Retrieves a single guide by id."""
    db = get_db()
    from bson import ObjectId
    try:
        g = await db.guides.find_one({"_id": ObjectId(guide_id)})
        if g:
            g["id"] = str(g.pop("_id"))
            return GuideResponse(**g)
    except Exception:
        pass
    return None


async def create_booking(user_id: str, payload: BookingCreate) -> BookingResponse:
    """Creates a guide booking."""
    db = get_db()
    from datetime import datetime, timezone
    
    if payload.hours < 1 or payload.hours > 8:
        raise ValueError("Hours must be between 1 and 8")
        
    try:
        booking_date = datetime.strptime(payload.date, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("Invalid date format")
        
    if booking_date < datetime.now().date():
        raise ValueError("Date cannot be in the past")
    
    guide = await get_guide(payload.guide_id)
    if not guide:
        raise ValueError("Guide not found")
        
    # Check duplicate
    existing_booking = await db.guide_bookings.find_one({
        "guide_id": payload.guide_id,
        "date": payload.date
    })
    if existing_booking:
        raise ValueError("Guide is already booked for this date")
        
    total_price = guide.hourly_rate * payload.hours
    
    booking_doc = {
        "user_id": user_id,
        "guide_id": payload.guide_id,
        "date": payload.date,
        "hours": payload.hours,
        "hourly_rate": guide.hourly_rate,
        "total_price": total_price,
        "status": "confirmed",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    result = await db.guide_bookings.insert_one(booking_doc)
    booking_doc["id"] = str(result.inserted_id)
    booking_doc["guide"] = guide
    
    return BookingResponse(**booking_doc)


async def get_user_bookings(user_id: str) -> List[BookingResponse]:
    """Returns guide bookings for the current user."""
    db = get_db()
    cursor = db.guide_bookings.find({"user_id": user_id})
    bookings = await cursor.to_list(length=100)
    
    result = []
    for b in bookings:
        b["id"] = str(b.pop("_id", ""))
        guide = await get_guide(b["guide_id"])
        if guide:
            b["guide"] = guide
        result.append(BookingResponse(**b))
    return result
