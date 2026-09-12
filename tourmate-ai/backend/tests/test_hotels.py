import pytest
from httpx import AsyncClient
from app.main import app
from app.api.deps import get_current_user_dependency

@pytest.mark.asyncio
async def test_get_all_hotels(client: AsyncClient):
    response = await client.get("/api/hotels")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)
    assert len(data["data"]) > 0
    hotel = data["data"][0]
    assert "name" in hotel
    assert "city" in hotel
    assert "rooms" in hotel
    assert "price_per_night_start" in hotel

@pytest.mark.asyncio
async def test_filter_hotels_by_city(client: AsyncClient):
    response = await client.get("/api/hotels?city=Jaipur")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    for h in data["data"]:
        assert "jaipur" in h["city"].lower()

@pytest.mark.asyncio
async def test_get_hotel_by_id(client: AsyncClient):
    # Fetch first hotel
    list_res = await client.get("/api/hotels")
    first_hotel = list_res.json()["data"][0]
    hotel_id = first_hotel["id"]

    res = await client.get(f"/api/hotels/{hotel_id}")
    assert res.status_code == 200
    hotel_data = res.json()["data"]
    assert hotel_data["id"] == hotel_id
    assert hotel_data["name"] == first_hotel["name"]

@pytest.mark.asyncio
async def test_book_hotel_authenticated(client: AsyncClient, test_user):
    app.dependency_overrides[get_current_user_dependency] = lambda: test_user

    try:
        list_res = await client.get("/api/hotels")
        first_hotel = list_res.json()["data"][0]
        first_room = first_hotel["rooms"][0]

        booking_payload = {
            "hotel_id": first_hotel["id"],
            "room_id": first_room["id"],
            "room_name": first_room["name"],
            "check_in_date": "2026-10-15",
            "check_out_date": "2026-10-18",
            "guests": 2,
            "special_requests": "Quiet room with high floor"
        }

        res = await client.post(
            "/api/hotels/book",
            json=booking_payload
        )
        assert res.status_code == 200
        booking = res.json()["data"]
        assert booking["hotel_name"] == first_hotel["name"]
        assert booking["room_name"] == first_room["name"]
        assert booking["nights"] == 3
        assert booking["status"] == "confirmed"

        # Test reading my bookings
        my_bookings_res = await client.get("/api/hotels/bookings/me")
        assert my_bookings_res.status_code == 200
        my_bookings = my_bookings_res.json()["data"]
        assert len(my_bookings) >= 1
        assert any(b["id"] == booking["id"] for b in my_bookings)
    finally:
        app.dependency_overrides.clear()
