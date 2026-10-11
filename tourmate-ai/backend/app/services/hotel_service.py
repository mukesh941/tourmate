import math
import uuid
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import AsyncSessionLocal
from app.models.sql.hotel import Hotel, RoomType, RoomInventory, RoomRate, HotelBooking
from app.models.sql.location import Location
from app.schemas.hotel import (
    HotelResponse,
    GeoJSONPointSchema,
    RoomType as RoomTypeSchema,
    HotelBookingCreate,
    HotelBookingResponse,
)

DESTINATION_ALIASES = {
    "kerala": ["kochi", "kerala", "munnar", "alleppey", "wayanad", "trivandrum"],
    "kashmir": ["srinagar", "kashmir", "gulmarg", "pahalgam", "jammu and kashmir"],
    "delhi": ["new delhi", "delhi"],
    "goa": ["goa", "candolim", "panaji", "morjim", "calangute"],
    "ladakh": ["leh", "ladakh"],
}

def _format_hotel_to_response(hotel: Hotel) -> HotelResponse:
    location_schema = None
    if hotel.location:
        location_schema = GeoJSONPointSchema(
            type="Point",
            coordinates=[hotel.location.longitude, hotel.location.latitude]
        )
    
    images = hotel.images if hotel.images else []
    cover_image = images[0] if images else "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%22800%22%20height%3D%22600%22%20viewBox%3D%220%200%20800%20600%22%20fill%3D%22none%22%3E%3Crect%20width%3D%22800%22%20height%3D%22600%22%20fill%3D%22%23f8fafc%22%2F%3E%3Cpath%20d%3D%22M360%20320h80v40h-80zM350%20220h100v180H350z%22%20fill%3D%22%2394a3b8%22%2F%3E%3Ctext%20x%3D%22400%22%20y%3D%22430%22%20fill%3D%22%2364748b%22%20font-family%3D%22system-ui%22%20font-size%3D%2218%22%20text-anchor%3D%22middle%22%3ETourMate%20Verified%20Accommodation%3C%2Ftext%3E%3C%2Fsvg%3E"

    # Minimal starting price logic for search result display
    starting_price = 0.0
    if hotel.room_types:
        for rt in hotel.room_types:
            if rt.rates:
                rt_prices = [float(r.price_per_night) for r in rt.rates]
                min_rt = min(rt_prices) if rt_prices else 0.0
                if starting_price == 0.0 or (min_rt > 0 and min_rt < starting_price):
                    starting_price = min_rt
    
    rooms_schema = []
    for rt in hotel.room_types:
        rooms_schema.append(RoomTypeSchema(
            id=str(rt.id),
            name=rt.name,
            price_per_night=float(rt.rates[0].price_per_night) if rt.rates else 0.0,
            capacity=rt.max_adults,
            bed_type=rt.bed_type,
            size="",
            amenities=[],
            image=cover_image,
            description=rt.description
        ))

    return HotelResponse(
        id=str(hotel.id),
        name=hotel.name,
        description=hotel.description,
        city=hotel.city,
        address=hotel.address,
        destination_id=str(hotel.location_id),
        location=location_schema,
        rating=4.0, # Defaulting for now
        review_count=0,
        price_per_night_start=starting_price,
        currency="INR",
        cover_image=cover_image,
        images=images or [cover_image],
        amenities=hotel.amenities,
        hotel_type="Hotel",
        rooms=rooms_schema,
        source="canonical",
        external_booking_url="",
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
    async def _query(session: AsyncSession) -> List[HotelResponse]:
        stmt = (
            select(Hotel)
            .join(Hotel.location)
            .options(
                selectinload(Hotel.location),
                selectinload(Hotel.room_types).selectinload(RoomType.rates)
            )
            .where(Hotel.is_active == True)
        )

        filters = []

        if city:
            c_clean = city.strip().lower()
            aliases = DESTINATION_ALIASES.get(c_clean, [c_clean])
            city_or_filters = []
            for alias in aliases:
                pat = f"%{alias}%"
                city_or_filters.append(func.lower(Hotel.city).like(pat))
                city_or_filters.append(func.lower(Location.city).like(pat))
                city_or_filters.append(func.lower(Location.state).like(pat))
                city_or_filters.append(func.lower(Location.name).like(pat))
            filters.append(or_(*city_or_filters))

        if query:
            q_pat = f"%{query.strip().lower()}%"
            filters.append(
                or_(
                    func.lower(Hotel.name).like(q_pat),
                    func.lower(Location.name).like(q_pat),
                    func.lower(Hotel.city).like(q_pat),
                    func.lower(Hotel.address).like(q_pat),
                )
            )

        if amenity:
            filters.append(Hotel.amenities.contains([amenity]))

        # Spatial bounding box
        if lat is not None and lng is not None and radius_km is not None and radius_km > 0:
            lat_delta = radius_km / 111.0
            cos_lat = math.cos(math.radians(lat))
            lng_delta = radius_km / (111.0 * max(cos_lat, 0.0001))
            filters.append(Location.latitude.between(lat - lat_delta, lat + lat_delta))
            filters.append(Location.longitude.between(lng - lng_delta, lng + lng_delta))

        if filters:
            stmt = stmt.where(and_(*filters))

        stmt = stmt.order_by(Hotel.name.asc())

        result = await session.execute(stmt)
        hotels = result.scalars().all()

        canonical_results = [_format_hotel_to_response(h) for h in hotels]
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
            select(Hotel)
            .join(Hotel.location)
            .options(
                selectinload(Hotel.location),
                selectinload(Hotel.room_types).selectinload(RoomType.rates)
            )
            .where(Hotel.id == acc_uuid, Hotel.is_active == True)
        )
        result = await session.execute(stmt)
        h = result.scalar_one_or_none()
        if not h:
            return None
        return _format_hotel_to_response(h)

    if db is not None:
        return await _query(db)

    async with AsyncSessionLocal() as session:
        return await _query(session)


async def check_availability(
    hotel_id: str,
    check_in: str,
    check_out: str,
    rooms_needed: int,
    db: AsyncSession,
):
    try:
        d_in = datetime.strptime(check_in, "%Y-%m-%d").date()
        d_out = datetime.strptime(check_out, "%Y-%m-%d").date()
        nights = (d_out - d_in).days
        if nights < 1:
            return {"error": "Check-out date must be after check-in date"}
        if d_in < datetime.utcnow().date():
            return {"error": "Check-in date cannot be in the past"}
    except ValueError:
        return {"error": "Invalid date format"}

    h_uuid = uuid.UUID(hotel_id)
    
    # Load room types for this hotel
    stmt = select(RoomType).where(RoomType.hotel_id == h_uuid, RoomType.is_active == True)
    result = await db.execute(stmt)
    room_types = result.scalars().all()
    
    availability = []
    
    for rt in room_types:
        # Check inventory for all nights
        inv_stmt = select(RoomInventory).where(
            RoomInventory.room_type_id == rt.id,
            RoomInventory.inventory_date >= d_in,
            RoomInventory.inventory_date < d_out
        )
        inv_res = await db.execute(inv_stmt)
        inventory_records = inv_res.scalars().all()
        
        # We need inventory records for exactly 'nights' days
        if len(inventory_records) != nights:
            availability.append({"room_type_id": str(rt.id), "status": "Availability not verified (missing inventory dates)"})
            continue
            
        available_every_night = True
        for inv in inventory_records:
            avail = inv.total_rooms - inv.reserved_rooms - inv.blocked_rooms
            if avail < rooms_needed:
                available_every_night = False
                break
                
        if not available_every_night:
            availability.append({"room_type_id": str(rt.id), "status": "Unavailable"})
            continue
            
        # Check rates for all nights
        rate_stmt = select(RoomRate).where(
            RoomRate.room_type_id == rt.id,
            RoomRate.rate_date >= d_in,
            RoomRate.rate_date < d_out
        )
        rate_res = await db.execute(rate_stmt)
        rate_records = rate_res.scalars().all()
        
        if len(rate_records) != nights:
            availability.append({"room_type_id": str(rt.id), "status": "Availability not verified (missing rate dates)"})
            continue
            
        total_price = sum(r.price_per_night for r in rate_records) * rooms_needed
        
        availability.append({
            "room_type_id": str(rt.id),
            "room_name": rt.name,
            "status": "Available",
            "total_price": float(total_price),
            "currency": rate_records[0].currency if rate_records else "INR"
        })
        
    return {
        "hotel_id": hotel_id,
        "check_in": check_in,
        "check_out": check_out,
        "rooms_needed": rooms_needed,
        "is_demo": True,
        "source": "Simulated Local Inventory",
        "room_types": availability
    }

async def create_hotel_booking(
    user_id: str,
    user_name: str,
    user_email: str,
    payload: HotelBookingCreate,
    db: AsyncSession,
) -> HotelBookingResponse:
    hotel = await get_hotel_by_id(payload.hotel_id, db=db)
    if not hotel:
        raise ValueError(f"Hotel not found.")

    try:
        d_in = datetime.strptime(payload.check_in_date, "%Y-%m-%d").date()
        d_out = datetime.strptime(payload.check_out_date, "%Y-%m-%d").date()
        nights = (d_out - d_in).days
        if nights < 1:
            raise ValueError("Check-out date must be after check-in date.")
    except ValueError as e:
        raise ValueError(f"Invalid date format: {e}")

    # For safety, require room_id in payload to ensure exact booking. Since HotelBookingCreate might not have room_id required, we handle it:
    if not payload.room_id:
        # try matching room_name
        matched_room_id = next((r.id for r in hotel.rooms if r.name == payload.room_name), None)
        if not matched_room_id:
            raise ValueError("Invalid room selection")
        r_uuid = uuid.UUID(matched_room_id)
    else:
        r_uuid = uuid.UUID(payload.room_id)
    
    rooms_needed = payload.rooms
    if rooms_needed < 1:
        raise ValueError("Rooms needed must be at least 1")

    # Check inventory and lock rows
    inv_stmt = select(RoomInventory).where(
        RoomInventory.room_type_id == r_uuid,
        RoomInventory.inventory_date >= d_in,
        RoomInventory.inventory_date < d_out
    ).with_for_update()
    
    inv_res = await db.execute(inv_stmt)
    inventory_records = inv_res.scalars().all()
    
    if len(inventory_records) != nights:
        raise ValueError("Availability not verified for all dates")
        
    for inv in inventory_records:
        avail = inv.total_rooms - inv.reserved_rooms - inv.blocked_rooms
        if avail < rooms_needed:
            raise ValueError("Insufficient rooms available")

    # Get rates
    rate_stmt = select(RoomRate).where(
        RoomRate.room_type_id == r_uuid,
        RoomRate.rate_date >= d_in,
        RoomRate.rate_date < d_out
    )
    rate_res = await db.execute(rate_stmt)
    rate_records = rate_res.scalars().all()
    
    if len(rate_records) != nights:
        raise ValueError("Rates not available for all dates")

    total_price = sum(r.price_per_night for r in rate_records) * rooms_needed

    # Update inventory
    for inv in inventory_records:
        inv.reserved_rooms += rooms_needed
        
    # Create booking
    import random
    import string
    ref = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    booking = HotelBooking(
        booking_reference=ref,
        user_id=uuid.UUID(user_id),
        hotel_id=uuid.UUID(payload.hotel_id),
        room_type_id=r_uuid,
        check_in=d_in,
        check_out=d_out,
        rooms_booked=rooms_needed,
        adults=payload.guests, # assuming guests map to adults
        children=0,
        total_price=total_price,
        currency=rate_records[0].currency,
        status="confirmed"
    )
    
    db.add(booking)
    await db.commit()
    await db.refresh(booking)

    # Convert to response
    room_name = payload.room_name
    return HotelBookingResponse(
        id=str(booking.id),
        user_id=user_id,
        user_name=user_name,
        user_email=user_email,
        hotel_id=payload.hotel_id,
        hotel_name=hotel.name,
        hotel_city=hotel.city,
        hotel_image=hotel.cover_image,
        room_name=room_name,
        check_in_date=payload.check_in_date,
        check_out_date=payload.check_out_date,
        nights=nights,
        rooms=rooms_needed,
        guests=payload.guests,
        price_per_night=float(total_price / nights / rooms_needed),
        total_price=float(total_price),
        status=booking.status,
        special_requests=payload.special_requests,
        created_at=booking.created_at.isoformat()
    )


async def get_user_hotel_bookings(user_id: str, db: AsyncSession) -> List[HotelBookingResponse]:
    stmt = select(HotelBooking).options(
        selectinload(HotelBooking.hotel),
        selectinload(HotelBooking.room_type),
        selectinload(HotelBooking.user)
    ).where(HotelBooking.user_id == uuid.UUID(user_id))
    
    result = await db.execute(stmt)
    bookings = result.scalars().all()
    
    resp = []
    for b in bookings:
        nights = (b.check_out - b.check_in).days
        resp.append(HotelBookingResponse(
            id=str(b.id),
            user_id=str(b.user_id),
            user_name=b.user.name,
            user_email=b.user.email,
            hotel_id=str(b.hotel_id),
            hotel_name=b.hotel.name,
            hotel_city=b.hotel.city,
            hotel_image=b.hotel.images[0] if b.hotel.images else "",
            room_name=b.room_type.name,
            check_in_date=b.check_in.strftime("%Y-%m-%d"),
            check_out_date=b.check_out.strftime("%Y-%m-%d"),
            nights=nights,
            rooms=b.rooms_booked,
            guests=b.adults,
            price_per_night=float(b.total_price / nights / b.rooms_booked) if nights > 0 and b.rooms_booked > 0 else 0,
            total_price=float(b.total_price),
            status=b.status,
            special_requests="",
            created_at=b.created_at.isoformat()
        ))
    return resp


async def cancel_hotel_booking(booking_id: str, user_id: str, db: AsyncSession) -> bool:
    stmt = select(HotelBooking).where(
        HotelBooking.id == uuid.UUID(booking_id),
        HotelBooking.user_id == uuid.UUID(user_id)
    ).with_for_update()
    
    res = await db.execute(stmt)
    booking = res.scalar_one_or_none()
    
    if not booking or booking.status == "cancelled":
        return False
        
    booking.status = "cancelled"
    
    # Release inventory
    nights = (booking.check_out - booking.check_in).days
    inv_stmt = select(RoomInventory).where(
        RoomInventory.room_type_id == booking.room_type_id,
        RoomInventory.inventory_date >= booking.check_in,
        RoomInventory.inventory_date < booking.check_out
    ).with_for_update()
    
    inv_res = await db.execute(inv_stmt)
    for inv in inv_res.scalars().all():
        inv.reserved_rooms = max(0, inv.reserved_rooms - booking.rooms_booked)
        
    await db.commit()
    return True
