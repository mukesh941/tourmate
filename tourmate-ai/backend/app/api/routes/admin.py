from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from bson import ObjectId

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
    hotels_count = await db.hotels.count_documents({})
    guides_count = await db.guides.count_documents({})
    itineraries_count = await db.itineraries.count_documents({})
    
    stats = {
        "users": users_count,
        "destinations": destinations_count,
        "places": places_count,
        "categories": categories_count,
        "hotels": hotels_count,
        "guides": guides_count,
        "itineraries": itineraries_count,
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

@router.delete("/users/{user_id}", response_model=Envelope[Dict[str, Any]])
async def delete_user(user_id: str, admin_user: UserPublic = Depends(require_admin)):
    db = get_db()
    
    if str(admin_user.id) == user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete your own admin account.")
        
    try:
        obj_id = ObjectId(user_id)
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID format.")
        
    result = await db.users.delete_one({"_id": obj_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        
    return Envelope(success=True, data={"message": "User deleted successfully."})

@router.put("/users/{user_id}/promote", response_model=Envelope[Dict[str, Any]])
async def promote_user(user_id: str, admin_user: UserPublic = Depends(require_admin)):
    """Promote a user to admin role."""
    db = get_db()
    try:
        obj_id = ObjectId(user_id)
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID format.")
    
    result = await db.users.update_one({"_id": obj_id}, {"$set": {"role": "admin", "is_admin": True}})
    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return Envelope(success=True, data={"message": "User promoted to admin successfully."})

@router.put("/users/{user_id}/demote", response_model=Envelope[Dict[str, Any]])
async def demote_user(user_id: str, admin_user: UserPublic = Depends(require_admin)):
    """Demote an admin back to regular user."""
    db = get_db()
    if str(admin_user.id) == user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot demote yourself.")
    try:
        obj_id = ObjectId(user_id)
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID format.")
    
    result = await db.users.update_one({"_id": obj_id}, {"$set": {"role": "user", "is_admin": False}})
    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return Envelope(success=True, data={"message": "User demoted to regular user."})

