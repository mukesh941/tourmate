import asyncio
import os
import sys
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import get_db
from app.services.guide_service import get_all_guides, get_guide, create_booking, get_user_bookings
from app.schemas.guide import BookingCreate

async def verify_guides():
    print("==================================================")
    print("PROBLEM 5 - MONGODB GUIDES VERIFICATION")
    print("==================================================")
    
    db = get_db()
    
    # 1. Check count in MongoDB collection
    count = await db.guides.count_documents({})
    print(f"MongoDB 'guides' collection total count: {count}")
    assert count == 197, f"Expected 197 guides, found {count}"

    # 2. Verify all guides via get_all_guides()
    guides = await get_all_guides()
    print(f"get_all_guides() returned: {len(guides)} guides")
    assert len(guides) == 197, f"Expected 197 guides from service, got {len(guides)}"

    # 3. Check IDs and schema completeness
    ids = [g.id for g in guides]
    assert len(ids) == len(set(ids)), "Duplicate guide IDs found!"
    for g in guides:
        assert len(g.id) == 24, f"Invalid MongoDB ObjectId string length for guide: {g.id}"
        assert g.id not in ("g1", "g2", "g3", "g4"), f"Found mock ID: {g.id}"
        assert g.name, f"Guide {g.id} missing name"
        assert g.hourly_rate > 0, f"Guide {g.name} has non-positive hourly rate"
        assert g.image_url, f"Guide {g.name} missing image_url"
        assert g.location, f"Guide {g.name} missing location"
        assert isinstance(g.languages, list), f"Guide {g.name} languages is not a list"

    print("All 197 guides have valid MongoDB ObjectIds and complete fields.")

    # 4. Test case-insensitive location filtering
    delhi_guides = await get_all_guides("Delhi")
    delhi_lower = await get_all_guides("delhi")
    delhi_upper = await get_all_guides("NEW DELHI")
    print(f"Guides in 'Delhi': {len(delhi_guides)}, 'delhi': {len(delhi_lower)}, 'NEW DELHI': {len(delhi_upper)}")
    assert len(delhi_guides) > 0, "No guides found for 'Delhi'"
    assert len(delhi_guides) == len(delhi_lower) == len(delhi_upper), "Case-insensitive location filter mismatch"

    # 5. Test get_guide with valid and invalid IDs
    first_guide = guides[0]
    fetched = await get_guide(first_guide.id)
    assert fetched is not None, f"Failed to retrieve guide by ID: {first_guide.id}"
    assert fetched.id == first_guide.id
    assert fetched.name == first_guide.name

    invalid_fetched = await get_guide("g1")
    assert invalid_fetched is None, f"Expected None for invalid ID 'g1', got: {invalid_fetched}"

    invalid_hex = await get_guide("000000000000000000000000")
    assert invalid_hex is None, f"Expected None for non-existent ObjectId, got: {invalid_hex}"

    print("get_guide() lookup and safe invalid-ID handling verified.")

    # 6. Test booking validation and server-side pricing calculation
    test_user_id = "test-user-p5-verify"
    test_date = "2026-12-15"

    # Clean previous test booking if any
    await db.guide_bookings.delete_many({"user_id": test_user_id})

    # Test valid booking
    booking_payload = BookingCreate(
        guide_id=first_guide.id,
        date=test_date,
        hours=3
    )
    booking = await create_booking(test_user_id, booking_payload)
    print(f"Created booking: id={booking.id}, total_price={booking.total_price}, guide={booking.guide.name}")
    assert booking.hours == 3
    assert booking.hourly_rate == first_guide.hourly_rate
    assert booking.total_price == round(first_guide.hourly_rate * 3, 2)
    assert booking.guide.id == first_guide.id

    # Test duplicate booking rejection
    duplicate_failed = False
    try:
        await create_booking(test_user_id, booking_payload)
    except ValueError as e:
        duplicate_failed = True
        print(f"Duplicate booking correctly rejected: {e}")
    assert duplicate_failed, "Duplicate booking was not rejected!"

    # Test past date rejection
    past_date_failed = False
    try:
        past_payload = BookingCreate(guide_id=first_guide.id, date="2020-01-01", hours=2)
        await create_booking(test_user_id, past_payload)
    except ValueError as e:
        past_date_failed = True
        print(f"Past date correctly rejected: {e}")
    assert past_date_failed, "Past date booking was not rejected!"

    # Test invalid hours rejection
    hours_failed = False
    try:
        invalid_hours_payload = BookingCreate(guide_id=first_guide.id, date="2026-12-20", hours=10)
        await create_booking(test_user_id, invalid_hours_payload)
    except ValueError as e:
        hours_failed = True
        print(f"Invalid hours correctly rejected: {e}")
    assert hours_failed, "Invalid hours booking was not rejected!"

    # Test invalid guide ID rejection
    invalid_guide_failed = False
    try:
        invalid_guide_payload = BookingCreate(guide_id="g1", date="2026-12-20", hours=2)
        await create_booking(test_user_id, invalid_guide_payload)
    except ValueError as e:
        invalid_guide_failed = True
        print(f"Invalid guide ID correctly rejected: {e}")
    assert invalid_guide_failed, "Invalid guide booking was not rejected!"

    # Test get_user_bookings
    user_bookings = await get_user_bookings(test_user_id)
    print(f"User bookings retrieved: {len(user_bookings)}")
    assert len(user_bookings) == 1
    assert user_bookings[0].guide is not None
    assert user_bookings[0].guide.name == first_guide.name

    # Cleanup test booking
    await db.guide_bookings.delete_many({"user_id": test_user_id})

    print("==================================================")
    print("ALL VERIFICATIONS PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(verify_guides())
