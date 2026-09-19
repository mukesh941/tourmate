import uuid
from datetime import datetime, timezone
from bson import ObjectId
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.db import AsyncSessionLocal
from app.core.security import hash_password, verify_password
from app.models.sql.category import Category
from app.models.sql.user import Preference, UserInterest
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


async def _execute_update_user_preferences(
    user_id: str, payload: UserPreferencesUpdate, db: AsyncSession
) -> dict:
    try:
        uid = uuid.UUID(str(user_id))
    except (ValueError, TypeError) as exc:
        raise ValueError(f"Invalid user id: {user_id}") from exc

    # 1. Upsert Preference
    stmt = select(Preference).where(Preference.user_id == uid)
    res = await db.execute(stmt)
    pref = res.scalar_one_or_none()

    budget = payload.budget_range.strip().lower()[:32] if payload.budget_range else None
    style = payload.travel_style.strip()[:64] if payload.travel_style else None

    if pref:
        if budget:
            pref.budget_tier = budget
        if style:
            pref.travel_style = style
        pref.updated_at = datetime.now(timezone.utc)
    else:
        pref = Preference(
            user_id=uid,
            budget_tier=budget or "moderate",
            travel_style=style or "balanced",
        )
        db.add(pref)

    await db.flush()

    # 2. Match interests with existing categories
    matched_category_names = []
    if payload.interests:
        clean_interests = [i.strip() for i in payload.interests if i.strip()]
        if clean_interests:
            cat_stmt = select(Category).where(
                func.lower(Category.name).in_([ci.lower() for ci in clean_interests])
            )
            cat_res = await db.execute(cat_stmt)
            categories = cat_res.scalars().all()

            if categories:
                ui_stmt = select(UserInterest).where(UserInterest.user_id == uid)
                ui_res = await db.execute(ui_stmt)
                existing_ui = {ui.category_id: ui for ui in ui_res.scalars().all()}

                for cat in categories:
                    matched_category_names.append(cat.name)
                    if cat.id in existing_ui:
                        existing_ui[cat.id].weight = 1.0
                    else:
                        new_ui = UserInterest(user_id=uid, category_id=cat.id, weight=1.0)
                        db.add(new_ui)

    await db.commit()
    await db.refresh(pref)

    returned_interests = matched_category_names if matched_category_names else payload.interests

    return {
        "id": str(pref.id),
        "user_id": str(pref.user_id),
        "interests": returned_interests,
        "budget_range": pref.budget_tier.capitalize() if pref.budget_tier else "Moderate",
        "travel_style": pref.travel_style,
        "available_time": payload.available_time,
        "preferred_activities": payload.preferred_activities,
    }


async def update_user_preferences(
    user_id: str, payload: UserPreferencesUpdate, db: AsyncSession | None = None
) -> dict:
    if db is not None:
        return await _execute_update_user_preferences(user_id, payload, db)
    async with AsyncSessionLocal() as session:
        return await _execute_update_user_preferences(user_id, payload, session)


async def _execute_get_user_preferences(user_id: str, db: AsyncSession) -> dict | None:
    try:
        uid = uuid.UUID(str(user_id))
    except (ValueError, TypeError) as exc:
        raise ValueError(f"Invalid user id: {user_id}") from exc

    stmt = select(Preference).where(Preference.user_id == uid)
    res = await db.execute(stmt)
    pref = res.scalar_one_or_none()
    if not pref:
        return None

    ui_query = (
        select(Category.name)
        .join(UserInterest, UserInterest.category_id == Category.id)
        .where(UserInterest.user_id == uid)
    )
    interests = list((await db.execute(ui_query)).scalars().all())

    return {
        "id": str(pref.id),
        "user_id": str(pref.user_id),
        "interests": interests,
        "budget_range": pref.budget_tier.capitalize() if pref.budget_tier else "Moderate",
        "travel_style": pref.travel_style,
        "available_time": None,
        "preferred_activities": [],
    }


async def get_user_preferences(user_id: str, db: AsyncSession | None = None) -> dict | None:
    if db is not None:
        return await _execute_get_user_preferences(user_id, db)
    async with AsyncSessionLocal() as session:
        return await _execute_get_user_preferences(user_id, session)
