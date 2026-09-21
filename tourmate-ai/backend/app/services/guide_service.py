"""
Guide Service for TourMate AI.

Local Guides are part of the legacy feature set and are NOT represented in
the locked 23-table canonical PostgreSQL architecture.
To preserve database architecture integrity without fabricating new unapproved tables,
this service provides safe, non-blocking fallback responses without MongoDB dependencies.
"""
from typing import List, Optional
from app.schemas.guide import GuideResponse, BookingCreate, BookingResponse


async def get_all_guides(location: Optional[str] = None) -> List[GuideResponse]:
    """
    Returns available local guides.
    Currently empty as the locked 23-table schema does not include a guides table.
    """
    return []


async def get_guide(guide_id: str) -> Optional[GuideResponse]:
    """Retrieves a single guide by id."""
    return None


async def create_booking(user_id: str, payload: BookingCreate) -> BookingResponse:
    """Creates a guide booking."""
    raise ValueError("Local Expert booking is currently not available in this release.")


async def get_user_bookings(user_id: str) -> List[BookingResponse]:
    """Returns guide bookings for the current user."""
    return []
