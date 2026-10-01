"""
Comprehensive API test suite for Problem 5: Local Expert (Guides) and Booking.
Validates:
1. GET /api/guides returns real MongoDB guides (>= 100, no g1/g2/g3 mock IDs).
2. GET /api/guides?location=Delhi performs case-insensitive filtering.
3. GET /api/guides/{guide_id} handles valid ObjectId and invalid IDs (404).
4. POST /api/guides/book validates hours, dates, duplicate bookings, calculates total_price.
5. GET /api/guides/bookings/me returns user bookings with attached guide info.
"""
import pytest
from httpx import AsyncClient
from app.main import app
from app.core.database import get_db
from app.api.deps import get_current_user_dependency


@pytest.mark.asyncio
async def test_get_all_guides_api(client: AsyncClient):
    """GET /api/guides returns real MongoDB guides."""
    response = await client.get("/api/guides")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    guides = body["data"]
    assert isinstance(guides, list)
    assert len(guides) >= 100, f"Expected >= 100 guides from MongoDB, got {len(guides)}"

    # Check MongoDB IDs
    for g in guides[:20]:
        assert len(g["id"]) == 24, f"Invalid ObjectId string: {g['id']}"
        assert g["id"] not in ("g1", "g2", "g3", "g4"), f"Found mock ID: {g['id']}"
        assert g["name"]
        assert g["hourly_rate"] > 0
        assert g["image_url"]
        assert g["location"]
        assert isinstance(g["languages"], list)


@pytest.mark.asyncio
async def test_get_guides_location_filter_api(client: AsyncClient):
    """GET /api/guides?location=Delhi performs case-insensitive filtering."""
    res_delhi = await client.get("/api/guides?location=Delhi")
    assert res_delhi.status_code == 200
    data_delhi = res_delhi.json()["data"]
    assert len(data_delhi) > 0

    res_lower = await client.get("/api/guides?location=delhi")
    assert res_lower.status_code == 200
    data_lower = res_lower.json()["data"]

    assert len(data_delhi) == len(data_lower)
    for g in data_delhi:
        assert "delhi" in g["location"].lower()


@pytest.mark.asyncio
async def test_get_single_guide_api(client: AsyncClient):
    """GET /api/guides/{guide_id} retrieves guide or returns 404."""
    # Get all to pick a real ID
    all_res = await client.get("/api/guides")
    guides = all_res.json()["data"]
    first_guide = guides[0]

    # Valid ID
    res = await client.get(f"/api/guides/{first_guide['id']}")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["id"] == first_guide["id"]
    assert data["name"] == first_guide["name"]

    # Invalid ID formats
    res_invalid_short = await client.get("/api/guides/g1")
    assert res_invalid_short.status_code == 404

    res_invalid_hex = await client.get("/api/guides/000000000000000000000000")
    assert res_invalid_hex.status_code == 404


@pytest.mark.asyncio
async def test_book_guide_api(client: AsyncClient, test_user):
    """POST /api/guides/book verifies full booking flow and server pricing."""
    app.dependency_overrides[get_current_user_dependency] = lambda: test_user
    db = get_db()

    try:
        # Fetch a real guide
        all_res = await client.get("/api/guides")
        guide = all_res.json()["data"][0]

        test_date = "2026-12-25"
        # Clear prior test bookings if any
        await db.guide_bookings.delete_many({"guide_id": guide["id"], "date": test_date})

        # 1. Valid booking
        book_payload = {
            "guide_id": guide["id"],
            "date": test_date,
            "hours": 4
        }
        res = await client.post("/api/guides/book", json=book_payload)
        assert res.status_code == 200
        booking = res.json()["data"]
        assert booking["guide_id"] == guide["id"]
        assert booking["hours"] == 4
        assert booking["hourly_rate"] == guide["hourly_rate"]
        assert booking["total_price"] == round(guide["hourly_rate"] * 4, 2)
        assert booking["guide"]["id"] == guide["id"]
        assert booking["guide"]["name"] == guide["name"]

        # 2. Duplicate booking for same guide and date rejected
        res_dup = await client.post("/api/guides/book", json=book_payload)
        assert res_dup.status_code == 400
        assert "already booked" in res_dup.text

        # 3. Invalid guide ID rejected
        res_inv_guide = await client.post(
            "/api/guides/book",
            json={"guide_id": "g1", "date": "2026-12-28", "hours": 2}
        )
        assert res_inv_guide.status_code == 400
        assert "Guide not found" in res_inv_guide.text

        # 4. Past date rejected
        res_past = await client.post(
            "/api/guides/book",
            json={"guide_id": guide["id"], "date": "2020-01-01", "hours": 2}
        )
        assert res_past.status_code == 400
        assert "past" in res_past.text

        # 5. Invalid hours rejected
        res_hours = await client.post(
            "/api/guides/book",
            json={"guide_id": guide["id"], "date": "2026-12-29", "hours": 12}
        )
        assert res_hours.status_code == 400
        assert "Hours must be between" in res_hours.text

        # 6. GET /api/guides/bookings/me
        res_me = await client.get("/api/guides/bookings/me")
        assert res_me.status_code == 200
        my_bookings = res_me.json()["data"]
        assert len(my_bookings) >= 1
        assert any(b["id"] == booking["id"] for b in my_bookings)

        # Cleanup
        await db.guide_bookings.delete_many({"guide_id": guide["id"], "date": test_date})
    finally:
        app.dependency_overrides.clear()
