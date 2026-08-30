from bson import ObjectId
from app.core.database import get_db
from app.models.itinerary import ItineraryInDB
from app.schemas.itinerary import ItineraryCreate, ItineraryUpdate, ItineraryResponse

async def get_user_itineraries(user_id: str) -> list[ItineraryResponse]:
    db = get_db()
    cursor = db.itineraries.find({"user_id": user_id}).sort("created_at", -1)
    itineraries = []
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        itineraries.append(ItineraryResponse(**doc))
    return itineraries

async def get_itinerary(itinerary_id: str, user_id: str) -> ItineraryResponse | None:
    db = get_db()
    doc = await db.itineraries.find_one({"_id": ObjectId(itinerary_id), "user_id": user_id})
    if doc:
        doc["id"] = str(doc["_id"])
        return ItineraryResponse(**doc)
    return None

async def create_itinerary(user_id: str, payload: ItineraryCreate) -> ItineraryResponse:
    db = get_db()
    new_itinerary = ItineraryInDB(user_id=user_id, **payload.dict())
    result = await db.itineraries.insert_one(new_itinerary.dict())
    
    doc = await db.itineraries.find_one({"_id": result.inserted_id})
    doc["id"] = str(doc["_id"])
    return ItineraryResponse(**doc)

async def update_itinerary(itinerary_id: str, user_id: str, payload: ItineraryUpdate) -> ItineraryResponse | None:
    db = get_db()
    update_data = {k: v for k, v in payload.dict(exclude_unset=True).items() if v is not None}
    if update_data:
        await db.itineraries.update_one(
            {"_id": ObjectId(itinerary_id), "user_id": user_id}, 
            {"$set": update_data}
        )
    return await get_itinerary(itinerary_id, user_id)

async def delete_itinerary(itinerary_id: str, user_id: str) -> bool:
    db = get_db()
    result = await db.itineraries.delete_one({"_id": ObjectId(itinerary_id), "user_id": user_id})
    return result.deleted_count > 0
