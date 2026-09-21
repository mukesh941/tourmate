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
    
    # Restrict to India
    indian_dests = []
    async for dest in db.destinations.find({"country": {"$regex": re.compile("^India$", re.IGNORECASE)}}):
        indian_dests.append(str(dest["_id"]))
        
    if destination_id:
        if destination_id in indian_dests:
            query["destination_id"] = destination_id
        else:
            return []
    else:
        query["destination_id"] = {"$in": indian_dests}

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
    
    if category_id:
        query["category_id"] = category_id
    if q:
        # Check if q exactly matches a category name (e.g. from the Vibe buttons)
        matched_category = await db.categories.find_one({"name": {"$regex": re.compile(f"^{q}$", re.IGNORECASE)}})
        if matched_category:
            query["category_id"] = str(matched_category["_id"])
        else:
            # Find destinations that match the query
            matched_dests = []
            async for dest in db.destinations.find({"name": {"$regex": re.compile(q, re.IGNORECASE)}}):
                if str(dest["_id"]) in indian_dests:
                    matched_dests.append(str(dest["_id"]))
            
            or_conditions = [
                {"name": {"$regex": re.compile(q, re.IGNORECASE)}},
                {"description": {"$regex": re.compile(q, re.IGNORECASE)}}
            ]
            if matched_dests:
                or_conditions.append({"destination_id": {"$in": matched_dests}})
                
            query["$or"] = or_conditions
    if min_rating:
        query["rating"] = {"$gte": float(min_rating)}
        
    cursor = db.tourist_places.find(query)
    places = []
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        places.append(TouristPlaceResponse(**doc))
    return places

async def get_place(place_id: str) -> TouristPlaceResponse | None:
    # 1. Query PostgreSQL canonical POIs first
    try:
        from app.services.poi_service import get_poi_by_id
        pg_place = await get_poi_by_id(place_id)
        if pg_place:
            return pg_place
    except Exception as e:
        print(f"PostgreSQL POI lookup in get_place: {e}")

    # 2. Check if valid MongoDB ObjectId before querying legacy MongoDB
    try:
        from bson.errors import InvalidId
        obj_id = ObjectId(place_id)
        db = get_db()
        doc = await db.tourist_places.find_one({"_id": obj_id})
        if doc:
            doc["id"] = str(doc["_id"])
            return TouristPlaceResponse(**doc)
    except Exception:
        pass
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
    
    # Get all destination IDs for India
    indian_dests = []
    async for dest in db.destinations.find({"country": {"$regex": re.compile("^India$", re.IGNORECASE)}}):
        indian_dests.append(str(dest["_id"]))
        
    # Fetch all places located in India
    cursor = db.tourist_places.find({"destination_id": {"$in": indian_dests}})
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
