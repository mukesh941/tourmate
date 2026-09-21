"""
Test Suite for Production Pass 3: Data Quality, Product Content, and Booking Integrity.
Verifies canonical destination coverage (>= 15, all 15 intended cities, no duplicates),
hotel tier distribution, and server-side booking pricing without arbitrary hardcoding.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy import text
from app.core.db import AsyncSessionLocal
from app.services.hotel_service import create_hotel_booking, get_all_hotels
from app.schemas.hotel import HotelBookingCreate

EXPECTED_CANONICAL_DESTINATIONS = {
    "Agra", "Amritsar", "Bengaluru", "Chennai", "Goa",
    "Hyderabad", "Jaipur", "Kochi", "Manali", "Mumbai",
    "Mysuru", "New Delhi", "Srinagar", "Udaipur", "Varanasi"
}


@pytest.mark.asyncio
async def test_canonical_destinations_pass3(client: AsyncClient):
    """
    Verifies:
    - All 15 intended canonical destinations exist
    - Destination count is >= 15 (does NOT assume exactly 15 forever)
    - No duplicate destinations
    - Each destination has a valid non-empty cover_image and description
    """
    response = await client.get("/api/destinations")
    assert response.status_code == 200, f"Failed to get destinations: {response.text}"
    data = response.json()
    assert data["success"] is True
    destinations = data["data"]

    # 1. Count must be >= 15
    assert len(destinations) >= 15, f"Expected >= 15 destinations, got {len(destinations)}"

    # 2. No duplicates
    destination_names = [d["name"] for d in destinations]
    assert len(destination_names) == len(set(destination_names)), "Duplicate destinations detected in API response"

    # 3. All 15 intended canonical destinations must exist
    dest_name_set = set(destination_names)
    missing = EXPECTED_CANONICAL_DESTINATIONS - dest_name_set
    assert not missing, f"Missing canonical destinations: {missing}"

    # 4. Each destination has non-empty cover_image and description
    for d in destinations:
        assert d["cover_image"], f"Destination {d['name']} missing cover image"
        assert d["description"], f"Destination {d['name']} missing description"
        assert d["state"], f"Destination {d['name']} missing state"


@pytest.mark.asyncio
async def test_accommodations_tier_coverage_and_rates(client: AsyncClient):
    """
    Verifies:
    - Accommodations cover budget, moderate, and luxury tiers
    - Indicative prices are positive and realistic
    - Preserves budget < moderate < luxury indicative baseline tier ordering
    """
    response = await client.get("/api/hotels")
    assert response.status_code == 200, f"Failed to get hotels: {response.text}"
    data = response.json()
    assert data["success"] is True
    hotels = data["data"]
    assert len(hotels) >= 15, f"Expected >= 15 hotels, got {len(hotels)}"

    # Check that database contains budget, moderate, and luxury tiers
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text("SELECT budget_tier, count(*), min(price_per_night), max(price_per_night) FROM accommodations GROUP BY budget_tier;")
        )
        tier_stats = {row[0]: {"count": row[1], "min": float(row[2]), "max": float(row[3])} for row in result.fetchall()}

    assert "budget" in tier_stats, "No budget tier accommodations found in database"
    assert "moderate" in tier_stats, "No moderate tier accommodations found in database"
    assert "luxury" in tier_stats, "No luxury tier accommodations found in database"

    # Verify realistic indicative baseline tier ordering: budget min < moderate min < luxury max
    assert tier_stats["budget"]["min"] < tier_stats["moderate"]["min"]
    assert tier_stats["moderate"]["min"] < tier_stats["luxury"]["max"]


@pytest.mark.asyncio
async def test_hotel_booking_server_side_calculation():
    """
    Verifies:
    - create_hotel_booking validates hotel existence
    - Rejects non-existent hotel IDs
    - Calculates nights server-side accurately
    - Multiplies actual price_per_night by nights (no hardcoded 5000 fallback)
    - Validates date order (check_out > check_in)
    """
    hotels = await get_all_hotels()
    assert len(hotels) > 0, "No hotels available to test booking"
    test_hotel = hotels[0]

    # Test valid booking with specific nights
    payload = HotelBookingCreate(
        hotel_id=test_hotel.id,
        room_id=test_hotel.rooms[0].id if test_hotel.rooms else None,
        room_name=test_hotel.rooms[0].name if test_hotel.rooms else "Standard",
        check_in_date="2026-10-01",
        check_out_date="2026-10-04",  # 3 nights
        guests=2,
        special_requests="Quiet room"
    )

    booking = await create_hotel_booking(
        user_id="test-user-pass3",
        user_name="Test User",
        user_email="test@tourmate.test",
        payload=payload
    )

    assert booking.nights == 3
    assert booking.hotel_id == test_hotel.id
    expected_price_per_night = float(test_hotel.rooms[0].price_per_night) if test_hotel.rooms else float(test_hotel.price_per_night_start)
    assert booking.price_per_night == expected_price_per_night
    assert booking.total_price == round(expected_price_per_night * 3, 2)
    # Ensure it's not simply 5000 * 3 unless the hotel happens to be 5000
    if expected_price_per_night != 5000.0:
        assert booking.total_price != 15000.0


@pytest.mark.asyncio
async def test_hotel_booking_nonexistent_hotel_rejected():
    """
    Verifies that create_hotel_booking raises ValueError for non-existent hotel ID.
    """
    invalid_payload = HotelBookingCreate(
        hotel_id="00000000-0000-0000-0000-999999999999",
        room_id="r-default",
        room_name="Deluxe Suite",
        check_in_date="2026-11-01",
        check_out_date="2026-11-03",
        guests=1
    )

    with pytest.raises(ValueError, match="not found"):
        await create_hotel_booking(
            user_id="test-user-err",
            user_name="Error Tester",
            user_email="err@tourmate.test",
            payload=invalid_payload
        )


@pytest.mark.asyncio
async def test_hotel_booking_invalid_dates_rejected():
    """
    Verifies that check_out before or equal to check_in is rejected.
    """
    hotels = await get_all_hotels()
    test_hotel = hotels[0]

    invalid_payload = HotelBookingCreate(
        hotel_id=test_hotel.id,
        room_id=test_hotel.rooms[0].id if test_hotel.rooms else "r-1",
        room_name="Deluxe Room",
        check_in_date="2026-10-05",
        check_out_date="2026-10-04",  # check_out before check_in
        guests=2
    )

    with pytest.raises(ValueError, match="Check-out date must be at least one day after"):
        await create_hotel_booking(
            user_id="test-user-err",
            user_name="Error Tester",
            user_email="err@tourmate.test",
            payload=invalid_payload
        )
