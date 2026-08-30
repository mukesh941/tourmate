from bson import ObjectId
from app.core.database import get_db
from app.models.place import TouristPlaceInDB
from app.schemas.place import TouristPlaceCreate, TouristPlaceUpdate, TouristPlaceResponse
import re
from app.services.user_service import get_user_preferences
async def get_all_places(
    destination_id: str = None, 
    category_id: str = None, 
    q: str = None, 
    min_rating: float = None,
    lat: float = None,
    lng: float = None,
    radius_km: float = 10.0
) -> list[TouristPlaceResponse]:
    db = get_db()
    query = {}
    if lat is not None and lng is not None:
        query["location"] = {
            "$near": {
                "$geometry": {
                    "type": "Point",
                    "coordinates": [lng, lat]
                },
                "$maxDistance": radius_km * 1000  # Convert km to meters
            }
        }
    
    if destination_id:
        query["destination_id"] = destination_id
    if category_id:
        query["category_id"] = category_id
    if q:
        query["name"] = {"$regex": re.compile(q, re.IGNORECASE)}
    if min_rating:
        query["rating"] = {"$gte": float(min_rating)}
        
    cursor = db.tourist_places.find(query)
    places = []
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        places.append(TouristPlaceResponse(**doc))
    return places

async def get_place(place_id: str) -> TouristPlaceResponse | None:
    db = get_db()
    doc = await db.tourist_places.find_one({"_id": ObjectId(place_id)})
    if doc:
        doc["id"] = str(doc["_id"])
        return TouristPlaceResponse(**doc)
    return None

async def create_place(payload: TouristPlaceCreate) -> TouristPlaceResponse:
    db = get_db()
    new_place = TouristPlaceInDB(**payload.dict())
    result = await db.tourist_places.insert_one(new_place.dict())
    doc = await db.tourist_places.find_one({"_id": result.inserted_id})
    doc["id"] = str(doc["_id"])
    return TouristPlaceResponse(**doc)

async def update_place(place_id: str, payload: TouristPlaceUpdate) -> TouristPlaceResponse | None:
    db = get_db()
    update_data = {k: v for k, v in payload.dict(exclude_unset=True).items() if v is not None}
    if update_data:
        await db.tourist_places.update_one({"_id": ObjectId(place_id)}, {"$set": update_data})
    return await get_place(place_id)

async def delete_place(place_id: str) -> bool:
    db = get_db()
    result = await db.tourist_places.delete_one({"_id": ObjectId(place_id)})
    return result.deleted_count > 0

async def get_recommended_places(user_id: str) -> list[TouristPlaceResponse]:
    db = get_db()
    prefs = await get_user_preferences(user_id)
    
    # Fetch all places (in a real app, you would pre-filter this or use vector search)
    cursor = db.tourist_places.find({})
    all_places = []
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        all_places.append(TouristPlaceResponse(**doc))
        
    if not prefs or not prefs.get("interests"):
        # Fallback: return top rated
        all_places.sort(key=lambda x: x.rating, reverse=True)
        return all_places[:10]
        
    user_interests = [i.lower() for i in prefs.get("interests", [])]
    
    from app.services.ml_service import get_knn_recommendations
    recommended_places = await get_knn_recommendations(all_places, user_interests, k=10)
    
    return recommended_places
