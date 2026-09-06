from bson import ObjectId

from app.core.database import get_db
from app.core.security import hash_password, verify_password
from app.schemas.auth import UserPublic
from app.schemas.user import ChangePasswordRequest, UserPreferencesUpdate, UserProfileUpdate


async def update_user_profile(user_id: str, payload: UserProfileUpdate) -> UserPublic:
    update_data = {k: v for k, v in payload.dict(exclude_unset=True).items() if v is not None}
    
    db = get_db()
    if update_data:
        await db.users.update_one({"_id": ObjectId(user_id)}, {"$set": update_data})
    
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise ValueError("User not found")
        
    return UserPublic(
        id=str(user["_id"]),
        name=user["name"],
        email=user["email"],
        role=user.get("role", "user"),
        preferred_language=user.get("preferred_language", "en")
    )


async def change_password(user_id: str, payload: ChangePasswordRequest) -> None:
    db = get_db()
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise ValueError("User not found")
    if not verify_password(payload.current_password, user.get("password_hash", "")):
        raise ValueError("Current password is incorrect")
    new_hash = hash_password(payload.new_password)
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"password_hash": new_hash}}
    )


async def update_user_preferences(user_id: str, payload: UserPreferencesUpdate) -> dict:
    prefs_data = payload.dict(exclude_unset=True)
    
    db = get_db()
    await db.user_preferences.update_one(
        {"user_id": ObjectId(user_id)},
        {"$set": prefs_data},
        upsert=True
    )
    
    prefs = await db.user_preferences.find_one({"user_id": ObjectId(user_id)})
    if not prefs:
        raise ValueError("Preferences not saved")
        
    return {
        "id": str(prefs["_id"]),
        "user_id": str(prefs["user_id"]),
        "interests": prefs.get("interests", []),
        "budget_range": prefs.get("budget_range"),
        "travel_style": prefs.get("travel_style"),
        "available_time": prefs.get("available_time"),
        "preferred_activities": prefs.get("preferred_activities", [])
    }


async def get_user_preferences(user_id: str) -> dict | None:
    db = get_db()
    prefs = await db.user_preferences.find_one({"user_id": ObjectId(user_id)})
    if not prefs:
        return None
    return {
        "id": str(prefs["_id"]),
        "user_id": str(prefs["user_id"]),
        "interests": prefs.get("interests", []),
        "budget_range": prefs.get("budget_range"),
        "travel_style": prefs.get("travel_style"),
        "available_time": prefs.get("available_time"),
        "preferred_activities": prefs.get("preferred_activities", [])
    }
