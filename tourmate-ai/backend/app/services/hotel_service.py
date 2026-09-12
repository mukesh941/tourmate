from datetime import datetime
from bson import ObjectId
from typing import List, Optional
from app.core.database import get_db
from app.schemas.hotel import HotelResponse, HotelBookingCreate, HotelBookingResponse

async def get_all_hotels(
    city: Optional[str] = None,
    query: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    amenity: Optional[str] = None
) -> List[HotelResponse]:
    db = get_db()
    filters = {}

    if city:
        filters["city"] = {"$regex": city, "$options": "i"}

    if query:
        filters["$or"] = [
            {"name": {"$regex": query, "$options": "i"}},
            {"description": {"$regex": query, "$options": "i"}},
            {"city": {"$regex": query, "$options": "i"}},
            {"address": {"$regex": query, "$options": "i"}}
        ]

    if min_price is not None or max_price is not None:
        price_cond = {}
        if min_price is not None:
            price_cond["$gte"] = min_price
        if max_price is not None:
            price_cond["$lte"] = max_price
        filters["price_per_night_start"] = price_cond

    if min_rating is not None:
        filters["rating"] = {"$gte": min_rating}

    if amenity:
        filters["amenities"] = {"$regex": amenity, "$options": "i"}

    cursor = db.hotels.find(filters).sort("rating", -1)
    hotels = []
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        hotels.append(HotelResponse(**doc))
    return hotels

async def get_hotel_by_id(hotel_id: str) -> Optional[HotelResponse]:
    db = get_db()
    try:
        doc = await db.hotels.find_one({"_id": ObjectId(hotel_id)})
    except Exception:
        return None

    if doc:
        doc["id"] = str(doc["_id"])
        return HotelResponse(**doc)
    return None

async def create_hotel_booking(
    user_id: str,
    user_name: str,
    user_email: str,
    payload: HotelBookingCreate
) -> HotelBookingResponse:
    db = get_db()
    
    # 1. Verify Hotel
    try:
        hotel = await db.hotels.find_one({"_id": ObjectId(payload.hotel_id)})
    except Exception:
        raise ValueError("Invalid hotel ID")

    if not hotel:
        raise ValueError("Hotel not found")

    # 2. Find Room in Hotel
    rooms = hotel.get("rooms", [])
    selected_room = None
    for r in rooms:
        if r.get("id") == payload.room_id or r.get("name").lower() == payload.room_name.lower():
            selected_room = r
            break

    price_per_night = selected_room.get("price_per_night", hotel.get("price_per_night_start", 100)) if selected_room else hotel.get("price_per_night_start", 100)

    # 3. Calculate Nights
    try:
        d_in = datetime.strptime(payload.check_in_date, "%Y-%m-%d")
        d_out = datetime.strptime(payload.check_out_date, "%Y-%m-%d")
        nights = (d_out - d_in).days
        if nights <= 0:
            nights = 1
    except Exception:
        nights = 1

    total_price = round(price_per_night * nights, 2)

    # 4. Create Booking Document
    booking_doc = {
        "user_id": user_id,
        "user_name": user_name,
        "user_email": user_email,
        "hotel_id": str(hotel["_id"]),
        "hotel_name": hotel.get("name", "Hotel Stay"),
        "hotel_city": hotel.get("city", ""),
        "hotel_image": hotel.get("cover_image", ""),
        "room_name": payload.room_name,
        "check_in_date": payload.check_in_date,
        "check_out_date": payload.check_out_date,
        "nights": nights,
        "guests": payload.guests,
        "price_per_night": price_per_night,
        "total_price": total_price,
        "status": "confirmed",
        "special_requests": payload.special_requests,
        "created_at": datetime.utcnow().isoformat()
    }

    res = await db.hotel_bookings.insert_one(booking_doc)
    booking_doc["id"] = str(res.inserted_id)

    return HotelBookingResponse(**booking_doc)

async def get_user_hotel_bookings(user_id: str) -> List[HotelBookingResponse]:
    db = get_db()
    cursor = db.hotel_bookings.find({"user_id": user_id}).sort("created_at", -1)
    bookings = []
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        bookings.append(HotelBookingResponse(**doc))
    return bookings

async def cancel_hotel_booking(booking_id: str, user_id: str) -> bool:
    db = get_db()
    res = await db.hotel_bookings.update_one(
        {"_id": ObjectId(booking_id), "user_id": user_id},
        {"$set": {"status": "cancelled"}}
    )
    return res.modified_count > 0
