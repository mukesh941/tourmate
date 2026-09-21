import uuid
from datetime import datetime, timezone
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import AsyncSessionLocal
from app.core.security import hash_password, verify_password
from app.models.sql.category import Category
from app.models.sql.user import Preference, UserInterest, User
from app.schemas.auth import UserPublic
from app.schemas.user import ChangePasswordRequest, UserPreferencesUpdate, UserProfileUpdate


async def update_user_profile(user_id: str, payload: UserProfileUpdate) -> UserPublic:
    try:
        uid = uuid.UUID(str(user_id))
    except (ValueError, TypeError) as exc:
        raise ValueError(f"Invalid user id: {user_id}") from exc

    async with AsyncSessionLocal() as db:
        stmt = select(User).where(User.id == uid)
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()
        if not user:
            raise ValueError("User not found")

        if payload.name is not None:
            user.name = payload.name
        if payload.preferred_language is not None:
            user.preferred_language = payload.preferred_language

        await db.commit()
        await db.refresh(user)

        return UserPublic(
            id=str(user.id),
            name=user.name,
            email=user.email,
            role=user.role,
            preferred_language=user.preferred_language
        )


async def change_password(user_id: str, payload: ChangePasswordRequest) -> None:
    try:
        uid = uuid.UUID(str(user_id))
    except (ValueError, TypeError) as exc:
        raise ValueError(f"Invalid user id: {user_id}") from exc

    async with AsyncSessionLocal() as db:
        stmt = select(User).where(User.id == uid)
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()
        if not user:
            raise ValueError("User not found")

        if not verify_password(payload.current_password, user.password_hash or ""):
            raise ValueError("Current password is incorrect")

        user.password_hash = hash_password(payload.new_password)
        await db.commit()


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
