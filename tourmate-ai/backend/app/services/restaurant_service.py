"""
PostgreSQL Restaurant Service.
Queries food/restaurant POIs from canonical PostgreSQL tables.
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
from app.schemas.restaurant import RestaurantResponse, GeoJSONPointSchema


def _format_poi_to_restaurant(poi: POI) -> RestaurantResponse:
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
    cover_image = images[0] if images else "https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=800&q=80"

    return RestaurantResponse(
        id=str(poi.id),
        name=poi.name,
        description=poi.description or "",
        cuisine_type=["Local Speciality", "Traditional"],
        city=city,
        address=address,
        destination_id=city,
        location=location_schema,
        rating=float(poi.rating) if poi.rating else 4.5,
        review_count=120,
        price_level=int(poi.price_tier) if poi.price_tier else 2,
        popular_dishes=["Chef's Special"],
        opening_hours="09:00 AM - 10:00 PM",
        cover_image=cover_image,
        images=images
    )


async def get_all_restaurants(
    city: Optional[str] = None,
    query: Optional[str] = None,
    min_rating: Optional[float] = None,
    cuisine: Optional[str] = None,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    radius_km: Optional[float] = 10.0
) -> List[RestaurantResponse]:
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
        # Filter for food/dining category
        filters.append(
            or_(
                func.lower(Category.name).like("%food%"),
                func.lower(Category.slug).like("%food%"),
                func.lower(Category.name).like("%restaurant%"),
                func.lower(POI.name).like("%restaurant%"),
                func.lower(POI.name).like("%cafe%"),
                func.lower(POI.description).like("%food%"),
                func.lower(POI.description).like("%cuisine%")
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
        return [_format_poi_to_restaurant(p) for p in pois]


async def get_restaurant_by_id(restaurant_id: str) -> Optional[RestaurantResponse]:
    try:
        p_uuid = uuid.UUID(restaurant_id)
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
            return _format_poi_to_restaurant(poi)
    return None
