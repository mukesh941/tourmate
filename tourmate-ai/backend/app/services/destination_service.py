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


CANONICAL_DESTINATION_METADATA = {
    "agra": {
        "description": "Home of the world-renowned Taj Mahal, Agra Fort, and Mughal architectural marvels on the banks of the Yamuna River.",
        "cover_image": "https://images.unsplash.com/photo-1564507592333-c60657eea523?auto=format&fit=crop&w=1200&q=80",
        "state": "Uttar Pradesh"
    },
    "new delhi": {
        "description": "India's vibrant capital, blending centuries of Mughal and colonial heritage with bustling modern boulevards.",
        "cover_image": "https://images.unsplash.com/photo-1587474260584-136574528ed5?auto=format&fit=crop&w=1200&q=80",
        "state": "Delhi"
    },
    "jaipur": {
        "description": "The Pink City of Rajasthan, famed for majestic hill forts, the astronomical Jantar Mantar observatory, and vibrant bazaars.",
        "cover_image": "https://images.unsplash.com/photo-1477587458883-47145ed94245?auto=format&fit=crop&w=1200&q=80",
        "state": "Rajasthan"
    },
    "mumbai": {
        "description": "India's bustling financial and cinematic capital on the Arabian Sea, featuring Victorian Gothic landmarks and coastal promenades.",
        "cover_image": "https://images.unsplash.com/photo-1570168007204-dfb528c6958f?auto=format&fit=crop&w=1200&q=80",
        "state": "Maharashtra"
    },
    "bengaluru": {
        "description": "India's Silicon Valley and Garden City, celebrated for Bangalore Palace, Lalbagh botanical gardens, and vibrant tech culture.",
        "cover_image": "https://images.unsplash.com/photo-1596176530529-78163a4f7af2?auto=format&fit=crop&w=1200&q=80",
        "state": "Karnataka"
    },
    "goa": {
        "description": "Coastal paradise known for UNESCO World Heritage Portuguese architecture, sun-drenched beaches, spice plantations, and vibrant culture.",
        "cover_image": "https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?auto=format&fit=crop&w=1200&q=80",
        "state": "Goa"
    },
    "varanasi": {
        "description": "One of the world's oldest living cities and spiritual heart of India along the sacred Ganges, famous for ancient ghats and evening aartis.",
        "cover_image": "https://images.unsplash.com/photo-1561361513-2d000a50f0dc?auto=format&fit=crop&w=1200&q=80",
        "state": "Uttar Pradesh"
    },
    "kochi": {
        "description": "The Queen of the Arabian Sea, renowned for historic Fort Kochi, 14th-century Chinese fishing nets, spice trade heritage, and backwaters.",
        "cover_image": "https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?auto=format&fit=crop&w=1200&q=80",
        "state": "Kerala"
    },
    "udaipur": {
        "description": "The City of Lakes and Venice of the East, surrounded by the Aravali Hills with marble palaces reflected on Lake Pichola.",
        "cover_image": "https://images.unsplash.com/photo-1599661046289-e31897846e41?auto=format&fit=crop&w=1200&q=80",
        "state": "Rajasthan"
    },
    "amritsar": {
        "description": "Spiritual center of the Sikh religion, home to the magnificent gilded Harmandir Sahib (Golden Temple) and deep cultural heritage.",
        "cover_image": "https://images.unsplash.com/photo-1514222134-b57cbb8ce073?auto=format&fit=crop&w=1200&q=80",
        "state": "Punjab"
    },
    "hyderabad": {
        "description": "The City of Pearls, where Nizami grandeur at the Charminar and Golconda Fort converges with modern technology hubs and royal culinary traditions.",
        "cover_image": "https://images.unsplash.com/photo-1604999333679-b86d54738315?auto=format&fit=crop&w=1200&q=80",
        "state": "Telangana"
    },
    "chennai": {
        "description": "Cultural capital of South India, celebrated for Dravidian Kapaleeshwarar temple architecture, classical Carnatic music, and Marina Beach.",
        "cover_image": "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&w=1200&q=80",
        "state": "Tamil Nadu"
    },
    "mysuru": {
        "description": "The Heritage City of Karnataka, famed for the glittering Mysore Palace, Chamundi Hills, silk weaving, and royal Dasara festivities.",
        "cover_image": "https://images.unsplash.com/photo-1580837119756-563d608dd119?auto=format&fit=crop&w=1200&q=80",
        "state": "Karnataka"
    },
    "manali": {
        "description": "Himalayan resort town nestled in the Beas River valley, gateway to Solang Valley adventures, Rohtang Pass, and deodar forests.",
        "cover_image": "https://images.unsplash.com/photo-1626621341517-bbf3d9990a23?auto=format&fit=crop&w=1200&q=80",
        "state": "Himachal Pradesh"
    },
    "srinagar": {
        "description": "Paradise on Earth in the Kashmir Valley, famous for serene Dal Lake houseboats, Mughal gardens, and snow-capped Himalayan peaks.",
        "cover_image": "https://images.unsplash.com/photo-1598091383021-15ddea10925d?auto=format&fit=crop&w=1200&q=80",
        "state": "Jammu and Kashmir"
    },
}

NEUTRAL_PLACEHOLDER_COVER = "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%22800%22%20height%3D%22600%22%20viewBox%3D%220%200%20800%20600%22%20fill%3D%22none%22%3E%3Crect%20width%3D%22800%22%20height%3D%22600%22%20fill%3D%22%23f1f5f9%22%2F%3E%3Ccircle%20cx%3D%22400%22%20cy%3D%22260%22%20r%3D%2248%22%20fill%3D%22%23cbd5e1%22%2F%3E%3Cpath%20d%3D%22M400%20228c-17.7%200-32%2014.3-32%2032%200%2028%2032%2056%2032%2056s32-28%2032-56c0-17.7-14.3-32-32-32zm0%2044c-6.6%200-12-5.4-12-12s5.4-12%2012-12%2012%205.4%2012%2012-5.4%2012-12%2012z%22%20fill%3D%22%2364748b%22%2F%3E%3Ctext%20x%3D%22400%22%20y%3D%22360%22%20fill%3D%22%23475569%22%20font-family%3D%22system-ui%2C%20sans-serif%22%20font-size%3D%2220%22%20font-weight%3D%22600%22%20text-anchor%3D%22middle%22%3ETourMate%20Verified%20Destination%3C%2Ftext%3E%3Ctext%20x%3D%22400%22%20y%3D%22390%22%20fill%3D%22%2394a3b8%22%20font-family%3D%22system-ui%2C%20sans-serif%22%20font-size%3D%2214%22%20font-weight%3D%22400%22%20text-anchor%3D%22middle%22%3EAuthentic%20Travel%20%26%20Heritage%3C%2Ftext%3E%3C%2Fsvg%3E"


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
            meta = CANONICAL_DESTINATION_METADATA.get(city_key, {})
            if city_key not in city_dict:
                city_dict[city_key] = {
                    "city": city,
                    "state": loc.state or meta.get("state", ""),
                    "country": loc.country or "India",
                    "cover_image": meta.get("cover_image", "")
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
        for city_key, city_info in city_dict.items():
            city_name = city_info["city"]
            meta = CANONICAL_DESTINATION_METADATA.get(city_key, {})
            cover_img = city_info["cover_image"] or meta.get("cover_image") or NEUTRAL_PLACEHOLDER_COVER
            description = meta.get("description", f"Explore historic attractions, architecture, and cultural landmarks in {city_name}.")
            destinations.append(
                DestinationResponse(
                    id=city_name,
                    name=city_name,
                    state=city_info["state"],
                    country=city_info["country"],
                    description=description,
                    cover_image=cover_img,
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
            clean_name = destination_id.strip().lower()
            clean_norm = clean_name.replace("-", " ").replace("_", " ").strip()
            stmt = select(Location).where(
                or_(
                    func.lower(Location.city) == clean_name,
                    func.lower(Location.city) == clean_norm,
                    func.lower(Location.state) == clean_name,
                    func.lower(Location.state) == clean_norm,
                    func.replace(func.lower(Location.city), " ", "-") == clean_name,
                    func.replace(func.lower(Location.city), " ", "_") == clean_name,
                )
            ).options(
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

        city_key = loc.city.strip().lower()
        meta = CANONICAL_DESTINATION_METADATA.get(city_key, {})
        final_cover = cover_image or meta.get("cover_image") or NEUTRAL_PLACEHOLDER_COVER
        description = meta.get("description", f"Explore historic attractions, architecture, and cultural landmarks in {loc.city}.")
        state_val = loc.state or meta.get("state", "")

        return DestinationResponse(
            id=loc.city,
            name=loc.city,
            state=state_val,
            country=loc.country or "India",
            description=description,
            cover_image=final_cover,
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
