import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import AsyncSessionLocal
from app.models.sql.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse


async def get_all_categories(db: Optional[AsyncSession] = None) -> List[CategoryResponse]:
    """Queries all categories from PostgreSQL."""
    if db is not None:
        stmt = select(Category).order_by(Category.name.asc())
        result = await db.execute(stmt)
        categories = result.scalars().all()
        return [
            CategoryResponse(
                id=str(cat.id),
                name=cat.name,
                icon=cat.icon or "MapPin"
            )
            for cat in categories
        ]

    async with AsyncSessionLocal() as session:
        stmt = select(Category).order_by(Category.name.asc())
        result = await session.execute(stmt)
        categories = result.scalars().all()
        return [
            CategoryResponse(
                id=str(cat.id),
                name=cat.name,
                icon=cat.icon or "MapPin"
            )
            for cat in categories
        ]


async def get_category(category_id: str, db: Optional[AsyncSession] = None) -> Optional[CategoryResponse]:
    try:
        cat_uuid = uuid.UUID(category_id)
    except (ValueError, TypeError):
        return None

    if db is not None:
        stmt = select(Category).where(Category.id == cat_uuid)
        result = await db.execute(stmt)
        cat = result.scalar_one_or_none()
        if cat:
            return CategoryResponse(id=str(cat.id), name=cat.name, icon=cat.icon or "MapPin")
        return None

    async with AsyncSessionLocal() as session:
        stmt = select(Category).where(Category.id == cat_uuid)
        result = await session.execute(stmt)
        cat = result.scalar_one_or_none()
        if cat:
            return CategoryResponse(id=str(cat.id), name=cat.name, icon=cat.icon or "MapPin")
        return None


async def create_category(payload: CategoryCreate, db: Optional[AsyncSession] = None) -> CategoryResponse:
    slug = payload.name.strip().lower().replace(" ", "-")
    cat = Category(
        name=payload.name,
        slug=slug,
        icon=payload.icon or "MapPin"
    )
    if db is not None:
        db.add(cat)
        await db.commit()
        await db.refresh(cat)
        return CategoryResponse(id=str(cat.id), name=cat.name, icon=cat.icon or "MapPin")

    async with AsyncSessionLocal() as session:
        session.add(cat)
        await session.commit()
        await session.refresh(cat)
        return CategoryResponse(id=str(cat.id), name=cat.name, icon=cat.icon or "MapPin")


async def update_category(category_id: str, payload: CategoryUpdate, db: Optional[AsyncSession] = None) -> Optional[CategoryResponse]:
    try:
        cat_uuid = uuid.UUID(category_id)
    except (ValueError, TypeError):
        return None

    session_ctx = None
    if db is None:
        session_ctx = AsyncSessionLocal()
        session = await session_ctx.__aenter__()
    else:
        session = db

    try:
        stmt = select(Category).where(Category.id == cat_uuid)
        result = await session.execute(stmt)
        cat = result.scalar_one_or_none()
        if not cat:
            return None
        if payload.name is not None:
            cat.name = payload.name
            cat.slug = payload.name.strip().lower().replace(" ", "-")
        if payload.icon is not None:
            cat.icon = payload.icon
        await session.commit()
        await session.refresh(cat)
        return CategoryResponse(id=str(cat.id), name=cat.name, icon=cat.icon or "MapPin")
    finally:
        if session_ctx:
            await session_ctx.__aexit__(None, None, None)


async def delete_category(category_id: str, db: Optional[AsyncSession] = None) -> bool:
    try:
        cat_uuid = uuid.UUID(category_id)
    except (ValueError, TypeError):
        return False

    session_ctx = None
    if db is None:
        session_ctx = AsyncSessionLocal()
        session = await session_ctx.__aenter__()
    else:
        session = db

    try:
        stmt = select(Category).where(Category.id == cat_uuid)
        result = await session.execute(stmt)
        cat = result.scalar_one_or_none()
        if not cat:
            return False
        await session.delete(cat)
        await session.commit()
        return True
    finally:
        if session_ctx:
            await session_ctx.__aexit__(None, None, None)
