"""
PostgreSQL Activity Service.
Queries adventure/cultural/sightseeing POIs from canonical PostgreSQL tables.
Provides non-blocking, production-safe responses without MongoDB dependencies.
"""
import math
import uuid
from typing import List, Optional
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload

from app.core.db import AsyncSessionLocal
from app.models.sql.poi import POI
from app.models.sql.category import Category
from app.models.sql.location import Location
from app.models.sql.media import POIImage, Image
from app.schemas.activity import ActivityResponse, GeoJSONPointSchema


def _format_poi_to_activity(poi: POI) -> ActivityResponse:
    location_schema = None
    if poi.location:
        location_schema = GeoJSONPointSchema(
            type="Point",
            coordinates=[poi.location.longitude, poi.location.latitude]
        )

    images: List[str] = []
    if poi.poi_images:
        sorted_imgs = sorted(poi.poi_images, key=lambda x: (not x.is_primary, x.display_order))
        for pi in sorted_imgs:
            if pi.image and pi.image.url:
                images.append(pi.image.url)

    city = poi.location.city if poi.location and poi.location.city else "India"
    address = poi.location.address if poi.location and poi.location.address else city
    cover_image = images[0] if images else "https://images.unsplash.com/photo-1533692328991-08159ff19fca?auto=format&fit=crop&w=800&q=80"
    activity_type = poi.category.name if poi.category else "Sightseeing"
    duration_mins = int(poi.typical_visit_duration_minutes) if poi.typical_visit_duration_minutes else 120

    return ActivityResponse(
        id=str(poi.id),
        name=poi.name,
        description=poi.description or "",
        activity_type=activity_type,
        city=city,
        address=address,
        destination_id=city,
        location=location_schema,
        rating=float(poi.rating) if poi.rating else 4.7,
        review_count=180,
        price=float(poi.price_tier * 150) if poi.price_tier else 0.0,
        currency="₹",
        duration=f"{duration_mins // 60}h {duration_mins % 60}m" if duration_mins >= 60 else f"{duration_mins} mins",
        difficulty_level="Moderate" if poi.price_tier and poi.price_tier > 2 else "Easy",
        cover_image=cover_image,
        images=images
    )


async def get_all_activities(
    city: Optional[str] = None,
    query: Optional[str] = None,
    min_rating: Optional[float] = None,
    activity_type: Optional[str] = None,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    radius_km: Optional[float] = 10.0
) -> List[ActivityResponse]:
    async with AsyncSessionLocal() as db:
        stmt = (
            select(POI)
            .join(POI.location)
            .join(POI.category)
            .options(
                selectinload(POI.location),
                selectinload(POI.category),
                selectinload(POI.poi_images).selectinload(POIImage.image)
            )
            .where(POI.is_active == True)
        )

        filters = []
        # Filter for activity categories
        filters.append(
            or_(
                func.lower(Category.name).like("%adventure%"),
                func.lower(Category.slug).like("%adventure%"),
                func.lower(Category.name).like("%culture%"),
                func.lower(Category.slug).like("%culture%"),
                func.lower(Category.name).like("%nature%"),
                func.lower(Category.slug).like("%nature%"),
                func.lower(Category.name).like("%history%"),
                func.lower(Category.slug).like("%history%"),
                func.lower(Category.name).like("%architecture%"),
                func.lower(Category.slug).like("%architecture%")
            )
        )

        if city:
            filters.append(func.lower(Location.city).like(f"%{city.strip().lower()}%"))

        if query:
            q_pat = f"%{query.strip().lower()}%"
            filters.append(
                or_(
                    func.lower(POI.name).like(q_pat),
                    func.lower(POI.description).like(q_pat),
                    func.lower(Location.city).like(q_pat)
                )
            )

        if min_rating:
            filters.append(POI.rating >= min_rating)

        if activity_type:
            filters.append(func.lower(Category.name).like(f"%{activity_type.strip().lower()}%"))

        if lat is not None and lng is not None and radius_km:
            lat_delta = radius_km / 111.0
            cos_lat = math.cos(math.radians(lat))
            lng_delta = radius_km / (111.0 * max(cos_lat, 0.0001))
            filters.append(Location.latitude.between(lat - lat_delta, lat + lat_delta))
            filters.append(Location.longitude.between(lng - lng_delta, lng + lng_delta))

        if filters:
            stmt = stmt.where(and_(*filters))

        stmt = stmt.order_by(POI.rating.desc())
        result = await db.execute(stmt)
        pois = result.scalars().all()
        return [_format_poi_to_activity(p) for p in pois]


async def get_activity_by_id(activity_id: str) -> Optional[ActivityResponse]:
    try:
        p_uuid = uuid.UUID(activity_id)
    except (ValueError, TypeError):
        return None

    async with AsyncSessionLocal() as db:
        stmt = (
            select(POI)
            .join(POI.location)
            .join(POI.category)
            .options(
                selectinload(POI.location),
                selectinload(POI.category),
                selectinload(POI.poi_images).selectinload(POIImage.image)
            )
            .where(POI.id == p_uuid, POI.is_active == True)
        )
        result = await db.execute(stmt)
        poi = result.scalar_one_or_none()
        if poi:
            return _format_poi_to_activity(poi)
    return None
