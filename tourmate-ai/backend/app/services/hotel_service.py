import math
import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import AsyncSessionLocal
from app.models.sql.accommodation import Accommodation
from app.models.sql.location import Location
from app.models.sql.media import AccommodationImage, Image
from app.schemas.hotel import (
    HotelResponse,
    GeoJSONPointSchema,
    RoomType,
    HotelBookingCreate,
    HotelBookingResponse,
)

# In-memory bookings store fallback for user hotel bookings
_in_memory_bookings: List[dict] = []


DESTINATION_ALIASES = {
    "kerala": ["kochi", "kerala", "munnar", "alleppey", "wayanad", "trivandrum"],
    "kashmir": ["srinagar", "kashmir", "gulmarg", "pahalgam", "jammu and kashmir"],
    "delhi": ["new delhi", "delhi"],
    "goa": ["goa", "candolim", "panaji", "morjim", "calangute"],
    "ladakh": ["leh", "ladakh"],
}


ACC_IMAGE_MAP = {
    # Agra
    "The Oberoi Amarvilas": "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=1200&q=80",
    "Tajview - IHCL SeleQtions": "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=1200&q=80",
    "Zostel Agra": "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?auto=format&fit=crop&w=1200&q=80",
    # New Delhi
    "The Imperial New Delhi": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1200&q=80",
    "Bloomrooms @ Janpath": "https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?auto=format&fit=crop&w=1200&q=80",
    "The Claridges New Delhi": "https://images.unsplash.com/photo-1566665797739-1674de7a421a?auto=format&fit=crop&w=1200&q=80",
    # Jaipur
    "Rambagh Palace": "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=1200&q=80",
    "Alsisar Haveli": "https://images.unsplash.com/photo-1566665797739-1674de7a421a?auto=format&fit=crop&w=1200&q=80",
    "Zostel Jaipur": "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?auto=format&fit=crop&w=1200&q=80",
    # Mumbai
    "The Taj Mahal Palace": "https://images.unsplash.com/photo-1582719508461-905c673771fd?auto=format&fit=crop&w=1200&q=80",
    "Residency Hotel Fort": "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=1200&q=80",
    "Zostel Mumbai": "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?auto=format&fit=crop&w=1200&q=80",
    # Bengaluru
    "The Leela Palace Bengaluru": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1200&q=80",
    "Bloomrooms @ Indiranagar": "https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?auto=format&fit=crop&w=1200&q=80",
    # Goa
    "Taj Fort Aguada Resort & Spa": "https://images.unsplash.com/photo-1582719508461-905c673771fd?auto=format&fit=crop&w=1200&q=80",
    "Santana Beach Resort": "https://images.unsplash.com/photo-1571896349842-33c89424de2d?auto=format&fit=crop&w=1200&q=80",
    "Zostel Goa (Morjim)": "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?auto=format&fit=crop&w=1200&q=80",
    # Varanasi
    "BrijRama Palace": "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=1200&q=80",
    "Stops Hostel Varanasi": "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?auto=format&fit=crop&w=1200&q=80",
    # Kochi / Kerala
    "Brunton Boatyard": "https://images.unsplash.com/photo-1571896349842-33c89424de2d?auto=format&fit=crop&w=1200&q=80",
    "Zostel Kochi": "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?auto=format&fit=crop&w=1200&q=80",
    # Udaipur
    "Taj Lake Palace": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1200&q=80",
    "Zostel Udaipur": "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?auto=format&fit=crop&w=1200&q=80",
    # Amritsar
    "Taj Swarna Amritsar": "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=1200&q=80",
    "Jugaadus Hostel": "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?auto=format&fit=crop&w=1200&q=80",
    # Hyderabad
    "Taj Falaknuma Palace": "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=1200&q=80",
    # Chennai
    "Taj Coromandel": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1200&q=80",
    # Mysuru
    "Lalitha Mahal Palace Hotel": "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=1200&q=80",
    # Manali
    "Johnson Lodge & Spa": "https://images.unsplash.com/photo-1512918728675-ed5a9ecdebfd?auto=format&fit=crop&w=1200&q=80",
    "Zostel Manali": "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?auto=format&fit=crop&w=1200&q=80",
    # Srinagar / Kashmir
    "The Lalit Grand Palace Srinagar": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1200&q=80",
    "Zostel Srinagar": "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?auto=format&fit=crop&w=1200&q=80",
}


def _format_acc_to_hotel_response(acc: Accommodation) -> HotelResponse:
    # Build coordinates
    location_schema = None
    if acc.location:
        location_schema = GeoJSONPointSchema(
            type="Point",
            coordinates=[acc.location.longitude, acc.location.latitude]
        )

    # Images
    images: List[str] = []
    if acc.accommodation_images:
        sorted_imgs = sorted(acc.accommodation_images, key=lambda x: (not x.is_primary, x.display_order))
        for ai in sorted_imgs:
            if ai.image and ai.image.url:
                url = ai.image.url
                if "wikimedia.org" in url and acc.name in ACC_IMAGE_MAP:
                    url = ACC_IMAGE_MAP[acc.name]
                images.append(url)

    if not images and acc.name in ACC_IMAGE_MAP:
        images.append(ACC_IMAGE_MAP[acc.name])

    cover_image = images[0] if images else "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%22800%22%20height%3D%22600%22%20viewBox%3D%220%200%20800%20600%22%20fill%3D%22none%22%3E%3Crect%20width%3D%22800%22%20height%3D%22600%22%20fill%3D%22%23f8fafc%22%2F%3E%3Cpath%20d%3D%22M360%20320h80v40h-80zM350%20220h100v180H350z%22%20fill%3D%22%2394a3b8%22%2F%3E%3Ctext%20x%3D%22400%22%20y%3D%22430%22%20fill%3D%22%2364748b%22%20font-family%3D%22system-ui%22%20font-size%3D%2218%22%20text-anchor%3D%22middle%22%3ETourMate%20Verified%20Accommodation%3C%2Ftext%3E%3C%2Fsvg%3E"

    price = float(acc.price_per_night) if acc.price_per_night else 3500.0

    rooms = [
        RoomType(
            id=f"{acc.id}-r1",
            name="Deluxe Room",
            price_per_night=price,
            capacity=2,
            bed_type="1 King Bed",
            size="450 sq ft",
            amenities=["Free WiFi", "City View", "Breakfast Included"],
            image=cover_image,
            description="Spacious and elegant room with modern amenities."
        ),
        RoomType(
            id=f"{acc.id}-r2",
            name="Executive Suite",
            price_per_night=round(price * 1.4, 2),
            capacity=3,
            bed_type="1 King Bed + 1 Sofa Bed",
            size="650 sq ft",
            amenities=["Free WiFi", "Balcony", "Lounge Access", "Breakfast Included"],
            image=cover_image,
            description="Luxury suite offering panoramic views and exclusive lounge access."
        )
    ]

    city_name = acc.location.city if acc.location else ""
    address_name = acc.location.address if acc.location else ""

    return HotelResponse(
        id=str(acc.id),
        name=acc.name,
        description=f"Experience exceptional comfort at {acc.name}, a premier {acc.budget_tier} {acc.type} in {city_name or 'India'}.",
        city=city_name,
        address=address_name,
        destination_id=city_name,
        location=location_schema,
        rating=float(acc.rating) if acc.rating else 4.5,
        review_count=128,
        price_per_night_start=price,
        currency="₹",
        cover_image=cover_image,
        images=images or [cover_image],
        amenities=["Free WiFi", "Pool", "Restaurant", "Air Conditioning", "Spa", "Breakfast"],
        hotel_type=acc.type.capitalize() if acc.type else "Hotel",
        rooms=rooms,
        source="canonical",
        external_booking_url=acc.external_booking_url,
    )


async def get_all_hotels(
    city: Optional[str] = None,
    query: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    amenity: Optional[str] = None,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    radius_km: Optional[float] = 10.0,
    db: Optional[AsyncSession] = None,
) -> List[HotelResponse]:
    from app.core.config import settings
    from app.services.google_places_service import search_lodging
    import logging

    async def _query(session: AsyncSession) -> List[HotelResponse]:
        stmt = (
            select(Accommodation)
            .join(Accommodation.location)
            .options(
                selectinload(Accommodation.location),
                selectinload(Accommodation.accommodation_images).selectinload(AccommodationImage.image),
            )
            .where(Accommodation.is_active == True)
        )

        filters = []

        if city:
            c_clean = city.strip().lower()
            aliases = DESTINATION_ALIASES.get(c_clean, [c_clean])
            city_or_filters = []
            for alias in aliases:
                pat = f"%{alias}%"
                city_or_filters.append(func.lower(Location.city).like(pat))
                city_or_filters.append(func.lower(Location.state).like(pat))
                city_or_filters.append(func.lower(Location.name).like(pat))
            filters.append(or_(*city_or_filters))

        if query:
            q_pat = f"%{query.strip().lower()}%"
            filters.append(
                or_(
                    func.lower(Accommodation.name).like(q_pat),
                    func.lower(Location.name).like(q_pat),
                    func.lower(Location.city).like(q_pat),
                    func.lower(Location.address).like(q_pat),
                )
            )

        if min_price is not None:
            filters.append(Accommodation.price_per_night >= Decimal(str(min_price)))

        if max_price is not None:
            filters.append(Accommodation.price_per_night <= Decimal(str(max_price)))

        if min_rating is not None:
            filters.append(Accommodation.rating >= float(min_rating))

        # Spatial bounding box
        if lat is not None and lng is not None and radius_km is not None and radius_km > 0:
            lat_delta = radius_km / 111.0
            cos_lat = math.cos(math.radians(lat))
            lng_delta = radius_km / (111.0 * max(cos_lat, 0.0001))
            filters.append(Location.latitude.between(lat - lat_delta, lat + lat_delta))
            filters.append(Location.longitude.between(lng - lng_delta, lng + lng_delta))

        if filters:
            stmt = stmt.where(and_(*filters))

        stmt = stmt.order_by(Accommodation.rating.desc(), Accommodation.name.asc())

        result = await session.execute(stmt)
        accs = result.scalars().all()

        # Haversine post-filter
        if lat is not None and lng is not None and radius_km is not None and radius_km > 0:
            filtered = []
            for a in accs:
                if a.location:
                    dlat = math.radians(a.location.latitude - lat)
                    dlng = math.radians(a.location.longitude - lng)
                    a_term = (
                        math.sin(dlat / 2) ** 2
                        + math.cos(math.radians(lat))
                        * math.cos(math.radians(a.location.latitude))
                        * math.sin(dlng / 2) ** 2
                    )
                    c = 2 * math.atan2(math.sqrt(a_term), math.sqrt(1 - a_term))
                    if 6371.0 * c <= radius_km:
                        filtered.append(a)
            accs = filtered

        canonical_results = [_format_acc_to_hotel_response(a) for a in accs]

        # Layered Discovery: If insufficient canonical results and Google Places configured, query external provider
        if len(canonical_results) < 2 and (city or (lat and lng)) and settings.google_maps_api_key:
            try:
                dest_target = city or "India"
                ext_places = await search_lodging(destination=dest_target, lat=lat, lng=lng, max_results=10)
                
                # Deduplicate against canonical results by name
                canonical_names = {c.name.strip().lower() for c in canonical_results}
                for ep in ext_places:
                    ep_name = ep.get("name", "").strip().lower()
                    if ep_name and ep_name not in canonical_names:
                        if min_rating is not None and (ep.get("rating") is None or ep.get("rating") < min_rating):
                            continue
                        canonical_results.append(HotelResponse(**ep))
                        canonical_names.add(ep_name)
            except Exception as e:
                logging.warning("External lodging discovery failed gracefully: %s", e)

        return canonical_results

    if db is not None:
        return await _query(db)

    async with AsyncSessionLocal() as session:
        return await _query(session)


async def get_hotel_by_id(hotel_id: str, db: Optional[AsyncSession] = None) -> Optional[HotelResponse]:
    try:
        acc_uuid = uuid.UUID(hotel_id)
    except (ValueError, TypeError):
        return None

    async def _query(session: AsyncSession) -> Optional[HotelResponse]:
        stmt = (
            select(Accommodation)
            .join(Accommodation.location)
            .options(
                selectinload(Accommodation.location),
                selectinload(Accommodation.accommodation_images).selectinload(AccommodationImage.image),
            )
            .where(Accommodation.id == acc_uuid, Accommodation.is_active == True)
        )
        result = await session.execute(stmt)
        acc = result.scalar_one_or_none()
        if not acc:
            return None
        return _format_acc_to_hotel_response(acc)

    if db is not None:
        return await _query(db)

    async with AsyncSessionLocal() as session:
        return await _query(session)


async def create_hotel_booking(
    user_id: str,
    user_name: str,
    user_email: str,
    payload: HotelBookingCreate,
    db: Optional[AsyncSession] = None,
) -> HotelBookingResponse:
    hotel = await get_hotel_by_id(payload.hotel_id, db=db)
    if not hotel:
        raise ValueError(f"Hotel with ID '{payload.hotel_id}' not found.")

    try:
        d_in = datetime.strptime(payload.check_in_date, "%Y-%m-%d")
        d_out = datetime.strptime(payload.check_out_date, "%Y-%m-%d")
        nights = (d_out - d_in).days
        if nights < 1:
            raise ValueError("Check-out date must be at least one day after check-in date.")
    except ValueError as e:
        if "Check-out" in str(e):
            raise
        raise ValueError(f"Invalid date format for booking: {e}")

    # Determine price per night from selected room or hotel starting price
    price_per_night = float(hotel.price_per_night_start)
    matched_room_name = payload.room_name
    if hotel.rooms:
        for room in hotel.rooms:
            if (payload.room_name and room.name.lower() == payload.room_name.strip().lower()) or (payload.room_id and room.id == payload.room_id):
                price_per_night = float(room.price_per_night)
                matched_room_name = room.name
                break

    total_price = round(price_per_night * nights, 2)

    booking_id = str(uuid.uuid4())
    booking = {
        "id": booking_id,
        "user_id": user_id,
        "user_name": user_name,
        "user_email": user_email,
        "hotel_id": str(hotel.id),
        "hotel_name": hotel.name,
        "hotel_city": hotel.city,
        "hotel_image": hotel.cover_image,
        "room_name": matched_room_name,
        "check_in_date": payload.check_in_date,
        "check_out_date": payload.check_out_date,
        "nights": nights,
        "guests": payload.guests,
        "price_per_night": price_per_night,
        "total_price": total_price,
        "status": "confirmed",
        "special_requests": payload.special_requests,
        "created_at": datetime.utcnow().isoformat()
    }
    _in_memory_bookings.append(booking)
    return HotelBookingResponse(**booking)


async def get_user_hotel_bookings(user_id: str, db: Optional[AsyncSession] = None) -> List[HotelBookingResponse]:
    user_bookings = [b for b in _in_memory_bookings if b.get("user_id") == user_id]
    return [HotelBookingResponse(**b) for b in user_bookings]


async def cancel_hotel_booking(booking_id: str, user_id: str, db: Optional[AsyncSession] = None) -> bool:
    for b in _in_memory_bookings:
        if b.get("id") == booking_id and b.get("user_id") == user_id:
            b["status"] = "cancelled"
            return True
    return False
