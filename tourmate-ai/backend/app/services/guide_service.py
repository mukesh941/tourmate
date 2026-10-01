"""
Guide Service for TourMate AI.

Manages Local Expert profiles and bookings stored in MongoDB ('guides' and 'guide_bookings' collections).
Provides MongoDB ObjectId lookups, case-insensitive location filtering, server-side pricing,
and booking duplicate & boundary validations.
"""
import re
import logging
from datetime import datetime, timezone
from typing import List, Optional
from bson import ObjectId

from app.schemas.guide import GuideResponse, BookingCreate, BookingResponse
from app.core.database import get_db

logger = logging.getLogger(__name__)


def _doc_to_guide_response(doc: dict) -> GuideResponse:
    """
    Serializes a raw MongoDB guide document into a GuideResponse schema.
    Converts '_id' to string 'id'.
    """
    d = dict(doc)
    d["id"] = str(d.pop("_id"))
    return GuideResponse(**d)


async def get_all_guides(location: Optional[str] = None) -> List[GuideResponse]:
    """
    Retrieves all guide profiles from the MongoDB 'guides' collection.
    Supports case-insensitive substring search on the 'location' field.
    """
    db = get_db()
    query = {}
    if location and location.strip():
        escaped_loc = re.escape(location.strip())
        query["location"] = {"$regex": escaped_loc, "$options": "i"}

    cursor = db.guides.find(query)
    docs = await cursor.to_list(length=500)
    return [_doc_to_guide_response(doc) for doc in docs]


async def get_guide(guide_id: str) -> Optional[GuideResponse]:
    """
    Retrieves a single guide profile by MongoDB ObjectId string.
    Safely handles invalid ObjectId strings (e.g. 'g1') by returning None.
    """
    if not guide_id or not ObjectId.is_valid(guide_id):
        return None

    db = get_db()
    try:
        doc = await db.guides.find_one({"_id": ObjectId(guide_id)})
        if doc:
            return _doc_to_guide_response(doc)
    except Exception as e:
        logger.warning(f"Error retrieving guide '{guide_id}': {e}")
    return None


async def create_booking(user_id: str, payload: BookingCreate) -> BookingResponse:
    """
    Creates a guide booking for the authenticated user in 'guide_bookings'.
    Validates:
      - 1 <= hours <= 8
      - date is valid YYYY-MM-DD and not in the past
      - guide exists in MongoDB
      - guide is not already booked on that date
    Calculates total_price server-side from the authoritative guide.hourly_rate.
    """
    if payload.hours < 1 or payload.hours > 8:
        raise ValueError("Hours must be between 1 and 8")

    try:
        booking_date = datetime.strptime(payload.date, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("Invalid date format. Expected YYYY-MM-DD")

    today = datetime.now(timezone.utc).date()
    if booking_date < today:
        raise ValueError("Date cannot be in the past")

    guide = await get_guide(payload.guide_id)
    if not guide:
        raise ValueError("Guide not found")

    db = get_db()

    # Check duplicate booking
    existing_booking = await db.guide_bookings.find_one({
        "guide_id": payload.guide_id,
        "date": payload.date
    })
    if existing_booking:
        raise ValueError("Guide is already booked for this date")

    total_price = round(guide.hourly_rate * payload.hours, 2)
    created_at = datetime.now(timezone.utc).isoformat()

    booking_doc = {
        "user_id": user_id,
        "guide_id": payload.guide_id,
        "date": payload.date,
        "hours": payload.hours,
        "hourly_rate": guide.hourly_rate,
        "total_price": total_price,
        "status": "confirmed",
        "created_at": created_at
    }

    result = await db.guide_bookings.insert_one(booking_doc)
    booking_doc["id"] = str(result.inserted_id)
    booking_doc["guide"] = guide

    return BookingResponse(**booking_doc)


async def get_user_bookings(user_id: str) -> List[BookingResponse]:
    """
    Retrieves all guide bookings for a specific user with attached guide profiles.
    """
    db = get_db()
    cursor = db.guide_bookings.find({"user_id": user_id}).sort("created_at", -1)
    bookings = await cursor.to_list(length=100)

    result = []
    for b in bookings:
        b["id"] = str(b.pop("_id", ""))
        guide = await get_guide(b.get("guide_id", ""))
        if guide:
            b["guide"] = guide
        result.append(BookingResponse(**b))
    return result
