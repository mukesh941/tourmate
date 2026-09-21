import uuid
from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import AsyncSessionLocal
from app.models.sql.location import Location
from app.models.sql.poi import POI
from app.models.sql.media import POIImage, Image
from app.schemas.destination import DestinationCreate, DestinationUpdate, DestinationResponse


async def get_all_destinations(db: Optional[AsyncSession] = None) -> List[DestinationResponse]:
    """
    Queries distinct canonical destinations (cities) from PostgreSQL locations.
    """
    async def _query(session: AsyncSession) -> List[DestinationResponse]:
        # Query distinct locations with their POIs to extract images
        stmt = (
            select(Location)
            .options(
                selectinload(Location.pois).selectinload(POI.poi_images).selectinload(POIImage.image)
            )
            .order_by(Location.city.asc())
        )
        result = await session.execute(stmt)
        locations = result.scalars().all()

        city_dict = {}
        for loc in locations:
            city = loc.city.strip()
            city_key = city.lower()
            if not city_key:
                continue
            if city_key not in city_dict:
                city_dict[city_key] = {
                    "city": city,
                    "state": loc.state or "",
                    "country": loc.country or "India",
                    "cover_image": ""
                }
            if not city_dict[city_key]["cover_image"]:
                for poi in loc.pois:
                    if poi.poi_images:
                        sorted_imgs = sorted(poi.poi_images, key=lambda x: (not x.is_primary, x.display_order))
                        for pi in sorted_imgs:
                            if pi.image and pi.image.url:
                                city_dict[city_key]["cover_image"] = pi.image.url
                                break
                    if city_dict[city_key]["cover_image"]:
                        break

        destinations = []
        for city_info in city_dict.values():
            city_name = city_info["city"]
            destinations.append(
                DestinationResponse(
                    id=city_name,
                    name=city_name,
                    state=city_info["state"],
                    country=city_info["country"],
                    description=f"Explore historic attractions, architecture, and cultural landmarks in {city_name}.",
                    cover_image=city_info["cover_image"],
                    popularity_score=4.9
                )
            )

        return destinations

    if db is not None:
        return await _query(db)

    async with AsyncSessionLocal() as session:
        return await _query(session)


async def get_destination(destination_id: str, db: Optional[AsyncSession] = None) -> Optional[DestinationResponse]:
    """
    Queries a destination by city name or location UUID.
    """
    async def _query(session: AsyncSession) -> Optional[DestinationResponse]:
        loc = None
        try:
            loc_uuid = uuid.UUID(destination_id)
            stmt = select(Location).where(Location.id == loc_uuid).options(
                selectinload(Location.pois).selectinload(POI.poi_images).selectinload(POIImage.image)
            )
            res = await session.execute(stmt)
            loc = res.scalar_one_or_none()
        except (ValueError, TypeError):
            pass

        if loc is None:
            stmt = select(Location).where(func.lower(Location.city) == destination_id.strip().lower()).options(
                selectinload(Location.pois).selectinload(POI.poi_images).selectinload(POIImage.image)
            )
            res = await session.execute(stmt)
            loc = res.scalars().first()

        if loc is None:
            return None

        cover_image = ""
        for poi in loc.pois:
            if poi.poi_images:
                for pi in poi.poi_images:
                    if pi.image and pi.image.url:
                        cover_image = pi.image.url
                        break
            if cover_image:
                break

        return DestinationResponse(
            id=loc.city,
            name=loc.city,
            state=loc.state or "",
            country=loc.country or "India",
            description=f"Explore historic attractions, architecture, and cultural landmarks in {loc.city}.",
            cover_image=cover_image,
            popularity_score=4.9
        )

    if db is not None:
        return await _query(db)

    async with AsyncSessionLocal() as session:
        return await _query(session)


async def create_destination(payload: DestinationCreate, db: Optional[AsyncSession] = None) -> DestinationResponse:
    # Convenience create - maps to response
    return DestinationResponse(
        id=payload.name,
        name=payload.name,
        state=payload.state,
        country=payload.country,
        description=payload.description,
        cover_image=payload.cover_image,
        popularity_score=payload.popularity_score
    )


async def update_destination(destination_id: str, payload: DestinationUpdate, db: Optional[AsyncSession] = None) -> Optional[DestinationResponse]:
    dest = await get_destination(destination_id, db=db)
    if not dest:
        return None
    return dest


async def delete_destination(destination_id: str, db: Optional[AsyncSession] = None) -> bool:
    return True
