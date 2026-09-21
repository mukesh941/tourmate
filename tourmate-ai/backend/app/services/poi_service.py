"""
PostgreSQL POI Service.
Queries canonical POIs, locations, categories, and media from PostgreSQL.
Transforms relational entities into the existing TouristPlaceResponse contract.
"""
import math
import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sql.poi import POI
from app.models.sql.location import Location
from app.models.sql.category import Category
from app.models.sql.media import POIImage, Image
from app.schemas.place import TouristPlaceResponse, GeoJSONPointSchema, FeatureScoresSchema


def _format_poi_to_response(poi: POI) -> TouristPlaceResponse:
    """Transforms a PostgreSQL POI model into the frontend TouristPlaceResponse schema."""
    # Build coordinates [lng, lat]
    location_schema = None
    if poi.location is not None:
        location_schema = GeoJSONPointSchema(
            type="Point",
            coordinates=[poi.location.longitude, poi.location.latitude]
        )

    # Collect images
    image_urls: List[str] = []
    if poi.poi_images:
        sorted_images = sorted(poi.poi_images, key=lambda x: (not x.is_primary, x.display_order))
        for pi in sorted_images:
            if pi.image and pi.image.url:
                image_urls.append(pi.image.url)

    # Feature scores based on canonical category
    cat_slug = poi.category.slug.lower() if poi.category else ""
    cat_name = poi.category.name.lower() if poi.category else ""
    feature_scores = FeatureScoresSchema(
        history=10.0 if "history" in (cat_slug, cat_name) else 1.0,
        nature=10.0 if "nature" in (cat_slug, cat_name) else 1.0,
        culture=10.0 if "culture" in (cat_slug, cat_name) else 1.0,
        adventure=10.0 if "adventure" in (cat_slug, cat_name) else 1.0,
        food=10.0 if "food" in (cat_slug, cat_name) else 1.0,
        shopping=10.0 if "shopping" in (cat_slug, cat_name) else 1.0,
        architecture=10.0 if "architecture" in (cat_slug, cat_name) else 1.0,
    )

    return TouristPlaceResponse(
        id=str(poi.id),
        name=poi.name,
        description=poi.description or "",
        category_id=str(poi.category_id),
        location=location_schema,
        images=image_urls,
        rating=float(poi.rating),
        price_level=int(poi.price_tier),
        visit_duration_minutes=int(poi.typical_visit_duration_minutes),
        feature_scores=feature_scores,
        history=poi.description or "",
        cultural_significance="",
        destination_id=str(poi.location.city) if poi.location else "",
        nearby_place_ids=[],
    )


async def get_all_pois(
    destination_id: Optional[str] = None,
    category_id: Optional[str] = None,
    q: Optional[str] = None,
    min_rating: Optional[float] = None,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    radius_km: Optional[float] = 10.0,
    db: AsyncSession = None,
) -> List[TouristPlaceResponse]:
    """Queries canonical POIs from PostgreSQL with optional filtering."""
    stmt = (
        select(POI)
        .join(POI.location)
        .join(POI.category)
        .options(
            selectinload(POI.location),
            selectinload(POI.category),
            selectinload(POI.poi_images).selectinload(POIImage.image),
        )
        .where(POI.is_active == True)
    )

    filters = []

    if destination_id:
        try:
            dest_uuid = uuid.UUID(destination_id)
            filters.append(or_(POI.location_id == dest_uuid, Location.id == dest_uuid))
        except (ValueError, TypeError):
            filters.append(func.lower(Location.city) == destination_id.strip().lower())

    if category_id:
        try:
            cat_uuid = uuid.UUID(category_id)
            filters.append(POI.category_id == cat_uuid)
        except ValueError:
            # Maybe category_id is category slug or name
            filters.append(
                or_(
                    func.lower(Category.name) == category_id.lower(),
                    func.lower(Category.slug) == category_id.lower(),
                )
            )

    if q:
        search_pattern = f"%{q.strip().lower()}%"
        filters.append(
            or_(
                func.lower(POI.name).like(search_pattern),
                func.lower(POI.description).like(search_pattern),
                func.lower(Location.name).like(search_pattern),
                func.lower(Location.city).like(search_pattern),
                func.lower(Location.state).like(search_pattern),
                func.lower(Category.name).like(search_pattern),
            )
        )

    if min_rating is not None and min_rating > 0:
        filters.append(POI.rating >= float(min_rating))

    # Spatial bounding box pre-filter
    if lat is not None and lng is not None and radius_km is not None and radius_km > 0:
        lat_delta = radius_km / 111.0
        cos_lat = math.cos(math.radians(lat))
        lng_delta = radius_km / (111.0 * max(cos_lat, 0.0001))
        filters.append(Location.latitude.between(lat - lat_delta, lat + lat_delta))
        filters.append(Location.longitude.between(lng - lng_delta, lng + lng_delta))

    if filters:
        stmt = stmt.where(and_(*filters))

    stmt = stmt.order_by(POI.rating.desc(), POI.name.asc())

    result = await db.execute(stmt)
    pois = result.scalars().all()

    # If spatial search was requested, compute exact Haversine distance
    if lat is not None and lng is not None and radius_km is not None and radius_km > 0:
        filtered = []
        for p in pois:
            if p.location:
                # Haversine distance
                dlat = math.radians(p.location.latitude - lat)
                dlng = math.radians(p.location.longitude - lng)
                a = (
                    math.sin(dlat / 2) ** 2
                    + math.cos(math.radians(lat))
                    * math.cos(math.radians(p.location.latitude))
                    * math.sin(dlng / 2) ** 2
                )
                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
                distance_km = 6371.0 * c
                if distance_km <= radius_km:
                    filtered.append(p)
        pois = filtered

    return [_format_poi_to_response(p) for p in pois]


async def get_poi_by_id(poi_id: str, db: AsyncSession) -> Optional[TouristPlaceResponse]:
    """Retrieves a single POI by UUID from PostgreSQL."""
    try:
        poi_uuid = uuid.UUID(poi_id)
    except (ValueError, TypeError):
        return None

    stmt = (
        select(POI)
        .join(POI.location)
        .join(POI.category)
        .options(
            selectinload(POI.location),
            selectinload(POI.category),
            selectinload(POI.poi_images).selectinload(POIImage.image),
        )
        .where(POI.id == poi_uuid, POI.is_active == True)
    )

    result = await db.execute(stmt)
    poi = result.scalar_one_or_none()
    if poi is None:
        return None

    return _format_poi_to_response(poi)
