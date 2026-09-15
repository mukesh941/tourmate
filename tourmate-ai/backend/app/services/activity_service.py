from bson import ObjectId
from typing import List, Optional
from app.core.database import get_db
from app.schemas.activity import ActivityResponse

async def get_all_activities(
    city: Optional[str] = None,
    query: Optional[str] = None,
    min_rating: Optional[float] = None,
    activity_type: Optional[str] = None,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    radius_km: Optional[float] = 10.0
) -> List[ActivityResponse]:
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

    if activity_type:
        filters["activity_type"] = {"$regex": activity_type, "$options": "i"}

    if lat is not None and lng is not None:
        radius_radians = radius_km / 6378.1
        filters["location"] = {
            "$geoWithin": {
                "$centerSphere": [[lng, lat], radius_radians]
            }
        }

    cursor = db.activities.find(filters).sort("rating", -1)
    activities = []
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        activities.append(ActivityResponse(**doc))
    return activities

async def get_activity_by_id(activity_id: str) -> Optional[ActivityResponse]:
    db = get_db()
    try:
        doc = await db.activities.find_one({"_id": ObjectId(activity_id)})
    except Exception:
        return None

    if doc:
        doc["id"] = str(doc["_id"])
        return ActivityResponse(**doc)
    return None
