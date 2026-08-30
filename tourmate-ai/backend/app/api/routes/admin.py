from fastapi import APIRouter, Depends
from typing import List, Dict, Any

from app.api.deps import require_admin
from app.schemas.auth import UserPublic
from app.schemas.common import Envelope
from app.core.database import get_db

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/stats", response_model=Envelope[Dict[str, Any]])
async def get_system_stats(admin_user: UserPublic = Depends(require_admin)):
    db = get_db()
    users_count = await db.users.count_documents({})
    destinations_count = await db.destinations.count_documents({})
    places_count = await db.tourist_places.count_documents({})
    categories_count = await db.categories.count_documents({})
    
    stats = {
        "users": users_count,
        "destinations": destinations_count,
        "places": places_count,
        "categories": categories_count
    }
    return Envelope(success=True, data=stats)

@router.get("/users", response_model=Envelope[List[UserPublic]])
async def get_all_users(admin_user: UserPublic = Depends(require_admin)):
    db = get_db()
    cursor = db.users.find({}).sort("created_at", -1)
    users = []
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        users.append(UserPublic(**doc))
    return Envelope(success=True, data=users)
