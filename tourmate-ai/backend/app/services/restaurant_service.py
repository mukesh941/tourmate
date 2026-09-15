from bson import ObjectId
from typing import List, Optional
from app.core.database import get_db
from app.schemas.restaurant import RestaurantResponse

async def get_all_restaurants(
    city: Optional[str] = None,
    query: Optional[str] = None,
    min_rating: Optional[float] = None,
    cuisine: Optional[str] = None,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    radius_km: Optional[float] = 10.0
) -> List[RestaurantResponse]:
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

    if min_rating is not None:
        filters["rating"] = {"$gte": min_rating}

    if cuisine:
        filters["cuisine_type"] = {"$regex": cuisine, "$options": "i"}

    if lat is not None and lng is not None:
        radius_radians = radius_km / 6378.1
        filters["location"] = {
            "$geoWithin": {
                "$centerSphere": [[lng, lat], radius_radians]
            }
        }

    cursor = db.restaurants.find(filters).sort("rating", -1)
    restaurants = []
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        restaurants.append(RestaurantResponse(**doc))
    return restaurants

async def get_restaurant_by_id(restaurant_id: str) -> Optional[RestaurantResponse]:
    db = get_db()
    try:
        doc = await db.restaurants.find_one({"_id": ObjectId(restaurant_id)})
    except Exception:
        return None

    if doc:
        doc["id"] = str(doc["_id"])
        return RestaurantResponse(**doc)
    return None
