from bson import ObjectId
from app.core.database import get_db
from app.models.guide import GuideInDB, BookingInDB
from app.schemas.guide import GuideCreate, GuideResponse, BookingCreate, BookingResponse

async def get_all_guides(location: str = None) -> list[GuideResponse]:
    db = get_db()
    query = {}
    if location:
        query["location"] = {"$regex": location, "$options": "i"}
        
    cursor = db.guides.find(query)
    guides = []
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        guides.append(GuideResponse(**doc))
    return guides

async def get_guide(guide_id: str) -> GuideResponse | None:
    db = get_db()
    doc = await db.guides.find_one({"_id": ObjectId(guide_id)})
    if doc:
        doc["id"] = str(doc["_id"])
        return GuideResponse(**doc)
    return None

async def create_booking(user_id: str, payload: BookingCreate) -> BookingResponse:
    db = get_db()
    
    # Calculate price based on guide's hourly rate
    guide = await db.guides.find_one({"_id": ObjectId(payload.guide_id)})
    if not guide:
        raise ValueError("Guide not found")
        
    total_price = guide.get("hourly_rate", 0) * payload.hours
    
    new_booking = BookingInDB(
        user_id=user_id,
        guide_id=payload.guide_id,
        date=payload.date,
        hours=payload.hours,
        total_price=total_price,
        status="confirmed"
    )
    
    result = await db.bookings.insert_one(new_booking.dict())
    doc = await db.bookings.find_one({"_id": result.inserted_id})
    doc["id"] = str(doc["_id"])
    
    # Populate guide data for response
    guide["id"] = str(guide["_id"])
    doc["guide"] = GuideResponse(**guide).dict()
    
    return BookingResponse(**doc)

async def get_user_bookings(user_id: str) -> list[BookingResponse]:
    db = get_db()
    cursor = db.bookings.find({"user_id": user_id})
    bookings = []
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        
        # Populate guide
        guide = await db.guides.find_one({"_id": ObjectId(doc["guide_id"])})
        if guide:
            guide["id"] = str(guide["_id"])
            doc["guide"] = GuideResponse(**guide).dict()
            
        bookings.append(BookingResponse(**doc))
    return bookings
