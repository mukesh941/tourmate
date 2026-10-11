import pytest
import uuid
from httpx import AsyncClient
from datetime import datetime, timedelta, date
from app.models.sql.hotel import Hotel, RoomType, RoomInventory, RoomRate, HotelBooking
from app.models.sql.location import Location
from app.models.sql.user import User
from app.core.db import AsyncSessionLocal
from app.api.deps import get_current_user_dependency
from app.main import app
from app.schemas.auth import UserPublic

@pytest.fixture
async def async_session():
    async with AsyncSessionLocal() as session:
        yield session

@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer testtoken"}

@pytest.fixture
def test_pg_user():
    return UserPublic(
        id=str(uuid.uuid4()),
        name="Test User",
        email=f"test_{uuid.uuid4()}@example.com",
        role="user",
        preferred_language="en",
        is_email_verified=True,
    )

@pytest.fixture
async def setup_hotel_data(async_session, test_pg_user):
    from app.models.sql.user import User
    test_user_db = User(
        id=uuid.UUID(test_pg_user.id),
        name=test_pg_user.name,
        email=test_pg_user.email,
        hashed_password="fake",
    )
    async_session.add(test_user_db)

    loc = Location(name="Test City Location", city="Test City", country="Test Country", latitude=0, longitude=0)
    async_session.add(loc)
    await async_session.commit()
    await async_session.refresh(loc)

    hotel = Hotel(
        name="Test Hotel",
        description="A nice hotel",
        address="123 Test St",
        city="Test City",
        location_id=loc.id,
        is_active=True
    )
    async_session.add(hotel)
    await async_session.commit()
    await async_session.refresh(hotel)

    rt = RoomType(
        hotel_id=hotel.id,
        name="Standard Room",
        max_adults=2,
        total_rooms=5,
        is_active=True
    )
    async_session.add(rt)
    await async_session.commit()
    await async_session.refresh(rt)

    d1 = datetime.utcnow().date() + timedelta(days=1)
    d2 = datetime.utcnow().date() + timedelta(days=2)
    
    inv1 = RoomInventory(room_type_id=rt.id, inventory_date=d1, total_rooms=5)
    inv2 = RoomInventory(room_type_id=rt.id, inventory_date=d2, total_rooms=5)
    async_session.add_all([inv1, inv2])

    rate1 = RoomRate(room_type_id=rt.id, rate_date=d1, price_per_night=100)
    rate2 = RoomRate(room_type_id=rt.id, rate_date=d2, price_per_night=150)
    async_session.add_all([rate1, rate2])

    await async_session.commit()

    rt2 = RoomType(
        hotel_id=hotel.id,
        name="Luxury Suite",
        max_adults=4,
        total_rooms=2,
        is_active=True
    )
    async_session.add(rt2)
    await async_session.commit()
    await async_session.refresh(rt2)

    inv3 = RoomInventory(room_type_id=rt2.id, inventory_date=d1, total_rooms=2)
    inv4 = RoomInventory(room_type_id=rt2.id, inventory_date=d2, total_rooms=2)
    async_session.add_all([inv3, inv4])

    rate3 = RoomRate(room_type_id=rt2.id, rate_date=d1, price_per_night=300)
    rate4 = RoomRate(room_type_id=rt2.id, rate_date=d2, price_per_night=300)
    async_session.add_all([rate3, rate4])
    await async_session.commit()

    return {"hotel": hotel, "room_type": rt, "room_type_2": rt2, "d1": d1, "d2": d2}

@pytest.mark.asyncio
async def test_hotel_search(client, setup_hotel_data):
    response = await client.get("/api/hotels?city=Test City")
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) >= 1
    assert any(h["name"] == "Test Hotel" for h in data)

@pytest.mark.asyncio
async def test_hotel_details(client, setup_hotel_data):
    hotel = setup_hotel_data["hotel"]
    response = await client.get(f"/api/hotels/{hotel.id}")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["name"] == "Test Hotel"
    assert len(data["rooms"]) == 2
    assert any(r["name"] == "Standard Room" for r in data["rooms"])
    assert any(r["name"] == "Luxury Suite" for r in data["rooms"])

@pytest.mark.asyncio
async def test_availability_check(client, setup_hotel_data):
    hotel = setup_hotel_data["hotel"]
    d1 = setup_hotel_data["d1"].strftime("%Y-%m-%d")
    d2 = (setup_hotel_data["d2"] + timedelta(days=1)).strftime("%Y-%m-%d")
    
    response = await client.get(f"/api/hotels/{hotel.id}/availability?check_in={d1}&check_out={d2}&rooms=1")
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data["room_types"]) == 2
    
    rt1_avail = next(r for r in data["room_types"] if r["room_name"] == "Standard Room")
    assert rt1_avail["status"] == "Available"
    assert rt1_avail["total_price"] == 250.0

    rt2_avail = next(r for r in data["room_types"] if r["room_name"] == "Luxury Suite")
    assert rt2_avail["status"] == "Available"
    assert rt2_avail["total_price"] == 600.0

@pytest.mark.asyncio
async def test_availability_check_multiple_rooms(client, setup_hotel_data):
    hotel = setup_hotel_data["hotel"]
    d1 = setup_hotel_data["d1"].strftime("%Y-%m-%d")
    d2 = (setup_hotel_data["d2"] + timedelta(days=1)).strftime("%Y-%m-%d")
    
    # Check for 2 rooms
    response = await client.get(f"/api/hotels/{hotel.id}/availability?check_in={d1}&check_out={d2}&rooms=2")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["room_types"][0]["status"] == "Available"
    assert data["room_types"][0]["total_price"] == 500.0

    # Check for 6 rooms (more than total_rooms=5)
    response = await client.get(f"/api/hotels/{hotel.id}/availability?check_in={d1}&check_out={d2}&rooms=6")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["room_types"][0]["status"] == "Unavailable"

@pytest.mark.asyncio
async def test_missing_inventory_availability(client, setup_hotel_data):
    hotel = setup_hotel_data["hotel"]
    d1 = setup_hotel_data["d1"].strftime("%Y-%m-%d")
    d3 = (setup_hotel_data["d2"] + timedelta(days=2)).strftime("%Y-%m-%d")
    
    response = await client.get(f"/api/hotels/{hotel.id}/availability?check_in={d1}&check_out={d3}&rooms=1")
    assert response.status_code == 200
    data = response.json()["data"]
    assert "not verified" in data["room_types"][0]["status"].lower()

@pytest.mark.asyncio
async def test_create_hotel_booking(client, setup_hotel_data, auth_headers, test_pg_user):
    app.dependency_overrides[get_current_user_dependency] = lambda: test_pg_user
    try:
        hotel = setup_hotel_data["hotel"]
        rt = setup_hotel_data["room_type"]
        d1 = setup_hotel_data["d1"].strftime("%Y-%m-%d")
        d2 = (setup_hotel_data["d2"] + timedelta(days=1)).strftime("%Y-%m-%d")

        payload = {
            "hotel_id": str(hotel.id),
            "room_id": str(rt.id),
            "room_name": rt.name,
            "check_in_date": d1,
            "check_out_date": d2,
            "guests": 2
        }

        response = await client.post(f"/api/hotels/{hotel.id}/bookings", json=payload, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["status"] == "confirmed"
        assert data["total_price"] == 250.0
        
        # Check if inventory was reduced
        response2 = await client.get(f"/api/hotels/{hotel.id}/availability?check_in={d1}&check_out={d2}&rooms=5")
        assert response2.status_code == 200
        assert response2.json()["data"]["room_types"][0]["status"] == "Unavailable"
    finally:
        app.dependency_overrides.pop(get_current_user_dependency, None)

@pytest.mark.asyncio
async def test_create_multiple_rooms_booking(client, setup_hotel_data, auth_headers, test_pg_user):
    app.dependency_overrides[get_current_user_dependency] = lambda: test_pg_user
    try:
        hotel = setup_hotel_data["hotel"]
        rt = setup_hotel_data["room_type"]
        d1 = setup_hotel_data["d1"].strftime("%Y-%m-%d")
        d2 = (setup_hotel_data["d2"] + timedelta(days=1)).strftime("%Y-%m-%d")

        payload = {
            "hotel_id": str(hotel.id),
            "room_id": str(rt.id),
            "room_name": rt.name,
            "check_in_date": d1,
            "check_out_date": d2,
            "guests": 4,
            "rooms": 2
        }

        response = await client.post(f"/api/hotels/{hotel.id}/bookings", json=payload, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["status"] == "confirmed"
        assert data["total_price"] == 500.0
        assert data["rooms"] == 2
        
        # Check if inventory was reduced properly
        response2 = await client.get(f"/api/hotels/{hotel.id}/availability?check_in={d1}&check_out={d2}&rooms=4")
        assert response2.status_code == 200
        assert response2.json()["data"]["room_types"][0]["status"] == "Unavailable"
        
        response3 = await client.get(f"/api/hotels/{hotel.id}/availability?check_in={d1}&check_out={d2}&rooms=3")
        assert response3.status_code == 200
        assert response3.json()["data"]["room_types"][0]["status"] == "Available"

        # Invalid booking with 0 rooms
        payload["rooms"] = 0
        response4 = await client.post(f"/api/hotels/{hotel.id}/bookings", json=payload, headers=auth_headers)
        assert response4.status_code == 422 # Pydantic validation
        
        # Invalid booking over capacity
        payload["rooms"] = 4
        response5 = await client.post(f"/api/hotels/{hotel.id}/bookings", json=payload, headers=auth_headers)
        assert response5.status_code == 400
        assert "Insufficient rooms available" in response5.json()["detail"]

    finally:
        app.dependency_overrides.pop(get_current_user_dependency, None)

@pytest.mark.asyncio
async def test_concurrent_booking(client, setup_hotel_data, auth_headers, test_pg_user):
    import asyncio
    app.dependency_overrides[get_current_user_dependency] = lambda: test_pg_user
    try:
        hotel = setup_hotel_data["hotel"]
        rt = setup_hotel_data["room_type"]
        d1 = setup_hotel_data["d1"].strftime("%Y-%m-%d")
        d2 = (setup_hotel_data["d2"] + timedelta(days=1)).strftime("%Y-%m-%d")

        payload = {
            "hotel_id": str(hotel.id),
            "room_id": str(rt.id),
            "room_name": rt.name,
            "check_in_date": d1,
            "check_out_date": d2,
            "guests": 2,
            "rooms": 4
        }
        
        # Total rooms is 5. Concurrent requests for 4 rooms should only allow one to succeed.
        reqs = [
            client.post(f"/api/hotels/{hotel.id}/bookings", json=payload, headers=auth_headers),
            client.post(f"/api/hotels/{hotel.id}/bookings", json=payload, headers=auth_headers)
        ]
        
        responses = await asyncio.gather(*reqs, return_exceptions=True)
        
        successes = 0
        failures = 0
        for r in responses:
            if isinstance(r, Exception):
                failures += 1
            else:
                if r.status_code == 200:
                    successes += 1
                else:
                    failures += 1
                    
        assert successes == 1
        assert failures == 1
    finally:
        app.dependency_overrides.pop(get_current_user_dependency, None)

@pytest.mark.asyncio
async def test_user_hotel_bookings_and_cancel(client, setup_hotel_data, auth_headers, test_pg_user):
    app.dependency_overrides[get_current_user_dependency] = lambda: test_pg_user
    try:
        hotel = setup_hotel_data["hotel"]
        rt = setup_hotel_data["room_type"]
        d1 = setup_hotel_data["d1"].strftime("%Y-%m-%d")
        d2 = (setup_hotel_data["d2"] + timedelta(days=1)).strftime("%Y-%m-%d")

        payload = {
            "hotel_id": str(hotel.id),
            "room_id": str(rt.id),
            "room_name": rt.name,
            "check_in_date": d1,
            "check_out_date": d2,
            "guests": 2
        }

        # Create booking first
        await client.post(f"/api/hotels/{hotel.id}/bookings", json=payload, headers=auth_headers)

        # Get user bookings
        response = await client.get("/api/hotel-bookings/my", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) >= 1
        booking_id = data[-1]["id"]
        
        # Cancel booking
        response = await client.post(f"/api/hotel-bookings/{booking_id}/cancel", headers=auth_headers)
        assert response.status_code == 200
        
        # Try cancelling again
        response = await client.post(f"/api/hotel-bookings/{booking_id}/cancel", headers=auth_headers)
        assert response.status_code == 404
    finally:
        app.dependency_overrides.pop(get_current_user_dependency, None)
