import uuid
import re
from typing import List, Optional
from bson import ObjectId
from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import AsyncSessionLocal
from app.core.database import get_db
from app.models.sql.poi import POI
from app.models.sql.location import Location
from app.models.sql.category import Category
from app.models.sql.media import POIImage, Image
from app.models.place import TouristPlaceInDB
from app.schemas.place import TouristPlaceCreate, TouristPlaceUpdate, TouristPlaceResponse
from app.services.user_service import get_user_preferences
from app.services import poi_service


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
        matched_category = await db.categories.find_one({"name": {"$regex": re.compile(f"^{q}$", re.IGNORECASE)}})
        if matched_category:
            query["category_id"] = str(matched_category["_id"])
        else:
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


async def get_place(place_id: str, db: Optional[AsyncSession] = None) -> TouristPlaceResponse | None:
    # 1. Query PostgreSQL canonical POIs first
    try:
        pg_place = await poi_service.get_poi_by_id(place_id, db=db)
        if pg_place:
            return pg_place
    except Exception as e:
        pass

    # 2. Check if valid MongoDB ObjectId before querying legacy MongoDB
    try:
        obj_id = ObjectId(place_id)
        mongo_db = get_db()
        doc = await mongo_db.tourist_places.find_one({"_id": obj_id})
        if doc:
            doc["id"] = str(doc["_id"])
            return TouristPlaceResponse(**doc)
    except Exception:
        pass
    return None


async def create_place(payload: TouristPlaceCreate, db: Optional[AsyncSession] = None) -> TouristPlaceResponse:
    """
    Creates a new POI in PostgreSQL linked to Location and Category.
    """
    async def _execute(session: AsyncSession) -> TouristPlaceResponse:
        # 1. Resolve Category
        category = None
        if payload.category_id:
            try:
                cat_uuid = uuid.UUID(str(payload.category_id).strip())
                cat_res = await session.execute(select(Category).where(Category.id == cat_uuid))
                category = cat_res.scalar_one_or_none()
            except (ValueError, TypeError):
                pass
            if not category:
                clean_cat = str(payload.category_id).strip().lower()
                clean_cat_norm = clean_cat.replace("-", " ").replace("_", " ").strip()
                cat_res = await session.execute(
                    select(Category).where(
                        or_(
                            func.lower(Category.name) == clean_cat,
                            func.lower(Category.slug) == clean_cat,
                            func.lower(Category.name) == clean_cat_norm,
                            func.lower(Category.slug) == clean_cat_norm,
                        )
                    )
                )
                category = cat_res.scalar_one_or_none()

        if not category:
            first_cat_res = await session.execute(select(Category).order_by(Category.name.asc()).limit(1))
            category = first_cat_res.scalar_one_or_none()
            if not category:
                category = Category(name="Sightseeing", slug="sightseeing", icon="MapPin")
                session.add(category)
                await session.flush()

        # 2. Resolve Location
        location = None
        dest_str = str(payload.destination_id).strip()
        try:
            loc_uuid = uuid.UUID(dest_str)
            loc_res = await session.execute(select(Location).where(Location.id == loc_uuid))
            location = loc_res.scalar_one_or_none()
        except (ValueError, TypeError):
            pass

        if not location:
            clean_dest = dest_str.lower()
            clean_dest_norm = clean_dest.replace("-", " ").replace("_", " ").strip()
            loc_res = await session.execute(
                select(Location).where(
                    or_(
                        func.lower(Location.city) == clean_dest,
                        func.lower(Location.city) == clean_dest_norm,
                        func.lower(Location.name) == clean_dest,
                        func.lower(Location.name) == clean_dest_norm,
                        func.lower(Location.canonical_name) == clean_dest,
                    )
                )
            )
            location = loc_res.scalars().first()

        lat = payload.location.coordinates[1] if payload.location and len(payload.location.coordinates) >= 2 else 20.5937
        lng = payload.location.coordinates[0] if payload.location and len(payload.location.coordinates) >= 2 else 78.9629

        if not location:
            location = Location(
                name=payload.name.strip(),
                city=dest_str or "India",
                canonical_name=dest_str or "India",
                state="",
                country="India",
                latitude=lat,
                longitude=lng,
                location_type="poi",
                is_active=True,
            )
            session.add(location)
            await session.flush()

        # 3. Create POI
        poi = POI(
            name=payload.name.strip(),
            description=payload.description or payload.history or "",
            location_id=location.id,
            category_id=category.id,
            rating=float(payload.rating) if payload.rating is not None else 4.5,
            price_tier=max(1, min(4, int(payload.price_level))) if payload.price_level else 1,
            typical_visit_duration_minutes=int(payload.visit_duration_minutes) if payload.visit_duration_minutes else 90,
            is_active=True,
        )
        session.add(poi)
        await session.flush()

        # 4. Attach Images
        if payload.images:
            for idx, img_url in enumerate(payload.images):
                if img_url and img_url.strip():
                    img = Image(url=img_url.strip(), is_fallback=False)
                    session.add(img)
                    await session.flush()
                    poi_img = POIImage(
                        poi_id=poi.id,
                        image_id=img.id,
                        is_primary=(idx == 0),
                        display_order=idx,
                    )
                    session.add(poi_img)

        await session.commit()
        return await poi_service.get_poi_by_id(str(poi.id), db=session)

    if db is not None:
        return await _execute(db)
    async with AsyncSessionLocal() as session:
        return await _execute(session)


async def update_place(place_id: str, payload: TouristPlaceUpdate, db: Optional[AsyncSession] = None) -> Optional[TouristPlaceResponse]:
    """
    Updates an existing POI in PostgreSQL.
    """
    async def _execute(session: AsyncSession) -> Optional[TouristPlaceResponse]:
        try:
            poi_uuid = uuid.UUID(str(place_id).strip())
        except (ValueError, TypeError):
            return None

        stmt = (
            select(POI)
            .where(POI.id == poi_uuid)
            .options(
                selectinload(POI.location),
                selectinload(POI.category),
                selectinload(POI.poi_images).selectinload(POIImage.image),
            )
        )
        res = await session.execute(stmt)
        poi = res.scalar_one_or_none()
        if not poi:
            return None

        if payload.name is not None:
            poi.name = payload.name.strip()
        if payload.description is not None:
            poi.description = payload.description.strip()
        elif payload.history is not None:
            poi.description = payload.history.strip()
        if payload.rating is not None:
            poi.rating = float(payload.rating)
        if payload.price_level is not None:
            poi.price_tier = max(1, min(4, int(payload.price_level)))
        if payload.visit_duration_minutes is not None:
            poi.typical_visit_duration_minutes = int(payload.visit_duration_minutes)

        if payload.category_id is not None:
            try:
                cat_uuid = uuid.UUID(str(payload.category_id).strip())
                cat_res = await session.execute(select(Category).where(Category.id == cat_uuid))
                cat = cat_res.scalar_one_or_none()
                if cat:
                    poi.category_id = cat.id
            except (ValueError, TypeError):
                clean_cat = str(payload.category_id).strip().lower()
                cat_res = await session.execute(
                    select(Category).where(
                        or_(
                            func.lower(Category.name) == clean_cat,
                            func.lower(Category.slug) == clean_cat,
                        )
                    )
                )
                cat = cat_res.scalar_one_or_none()
                if cat:
                    poi.category_id = cat.id

        if payload.destination_id is not None:
            dest_str = str(payload.destination_id).strip()
            try:
                loc_uuid = uuid.UUID(dest_str)
                loc_res = await session.execute(select(Location).where(Location.id == loc_uuid))
                loc = loc_res.scalar_one_or_none()
                if loc:
                    poi.location_id = loc.id
            except (ValueError, TypeError):
                clean_dest = dest_str.lower()
                loc_res = await session.execute(
                    select(Location).where(
                        or_(
                            func.lower(Location.city) == clean_dest,
                            func.lower(Location.name) == clean_dest,
                        )
                    )
                )
                loc = loc_res.scalars().first()
                if loc:
                    poi.location_id = loc.id

        if payload.location and len(payload.location.coordinates) >= 2 and poi.location:
            poi.location.longitude = payload.location.coordinates[0]
            poi.location.latitude = payload.location.coordinates[1]

        if payload.images is not None:
            for idx, img_url in enumerate(payload.images):
                if img_url and img_url.strip():
                    img = Image(url=img_url.strip(), is_fallback=False)
                    session.add(img)
                    await session.flush()
                    poi_img = POIImage(
                        poi_id=poi.id,
                        image_id=img.id,
                        is_primary=(idx == 0 and not poi.poi_images),
                        display_order=len(poi.poi_images) + idx,
                    )
                    session.add(poi_img)

        await session.commit()
        return await poi_service.get_poi_by_id(str(poi.id), db=session)

    if db is not None:
        return await _execute(db)
    async with AsyncSessionLocal() as session:
        return await _execute(session)


async def delete_place(place_id: str, db: Optional[AsyncSession] = None) -> bool:
    """
    Soft-deactivates a POI in PostgreSQL.
    """
    async def _execute(session: AsyncSession) -> bool:
        try:
            poi_uuid = uuid.UUID(str(place_id).strip())
        except (ValueError, TypeError):
            return False

        stmt = select(POI).where(POI.id == poi_uuid)
        res = await session.execute(stmt)
        poi = res.scalar_one_or_none()
        if not poi:
            return False

        poi.is_active = False
        await session.commit()
        return True

    if db is not None:
        return await _execute(db)
    async with AsyncSessionLocal() as session:
        return await _execute(session)


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

