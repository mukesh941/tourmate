import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport
from datetime import datetime

from app.main import app
from app.api.deps import get_current_user_dependency, get_async_db
from app.core.database import get_db
from app.schemas.auth import UserPublic
from app.schemas.place import TouristPlaceResponse, GeoJSONPointSchema, FeatureScoresSchema


@pytest.fixture
def mock_user_alice():
    return UserPublic(
        id="a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
        name="Alice Wonderland",
        email="alice@example.com",
        role="user",
        preferred_language="en",
    )


@pytest.fixture
def mock_user_bob():
    return UserPublic(
        id="b2c3d4e5-f6a7-8b9c-0d1e-2f3a4b5c6d7e",
        name="Bob Builder",
        email="bob@example.com",
        role="user",
        preferred_language="en",
    )


@pytest.fixture
def mock_mongo_db():
    fake_storage = []

    mock_collection = MagicMock()

    async def mock_insert_one(doc):
        new_doc = dict(doc)
        new_doc["_id"] = f"mongo_id_{len(fake_storage) + 1}"
        fake_storage.append(new_doc)
        res = MagicMock()
        res.inserted_id = new_doc["_id"]
        return res

    def mock_find(query):
        user_id = query.get("user_id")
        matching = [dict(d) for d in fake_storage if d.get("user_id") == user_id]
        
        cursor_mock = MagicMock()
        cursor_mock.sort = MagicMock(return_value=cursor_mock)
        cursor_mock.to_list = AsyncMock(return_value=matching)
        return cursor_mock

    mock_collection.insert_one = AsyncMock(side_effect=mock_insert_one)
    mock_collection.find = MagicMock(side_effect=mock_find)

    mock_db = {
        "application_bookings": mock_collection
    }
    return mock_db


@pytest.mark.asyncio
async def test_create_booking_with_user_public(mock_user_alice, mock_mongo_db):
    """Test 1 & 3: Booking creates successfully with UserPublic without TypeError/dict subscript errors."""
    app.dependency_overrides[get_current_user_dependency] = lambda: mock_user_alice
    app.dependency_overrides[get_db] = lambda: mock_mongo_db

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            payload = {
                "application_type": "smart_dining",
                "item_id": "rest_1",
                "item_name": "Skyline Rooftop Bistro",
                "booking_date": "2026-11-01",
                "booking_time": "19:30",
                "guests_count": 2,
                "notes": "Window seat preferred",
                "sub_selection": "Outdoor Balcony"
            }
            response = await client.post("/api/applications/book", json=payload)
            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
            
            data = response.json()
            assert data["success"] is True
            assert "booking_id" in data["data"]
            details = data["data"]["details"]
            assert details["user_id"] == "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d"
            assert details["user_email"] == "alice@example.com"
            assert details["user_name"] == "Alice Wonderland"
            assert details["item_name"] == "Skyline Rooftop Bistro"
            assert details["status"] == "confirmed"
    finally:
        app.dependency_overrides.pop(get_current_user_dependency, None)
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_get_my_bookings_and_isolation(mock_user_alice, mock_user_bob, mock_mongo_db):
    """Test 2 & 4: My bookings fetches current user's bookings and enforces user isolation."""
    # Alice creates a booking
    app.dependency_overrides[get_current_user_dependency] = lambda: mock_user_alice
    app.dependency_overrides[get_db] = lambda: mock_mongo_db

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Create Alice's booking
            payload_alice = {
                "application_type": "campus_tours",
                "item_id": "oxford-university",
                "item_name": "University of Oxford",
                "booking_date": "2026-12-10",
                "booking_time": "10:00",
                "guests_count": 1
            }
            res_book = await client.post("/api/applications/book", json=payload_alice)
            assert res_book.status_code == 200

            # Get Alice's bookings
            res_alice = await client.get("/api/applications/user/my-bookings")
            assert res_alice.status_code == 200
            alice_bookings = res_alice.json()["data"]
            assert len(alice_bookings) == 1
            assert alice_bookings[0]["user_id"] == str(mock_user_alice.id)
            assert alice_bookings[0]["item_name"] == "University of Oxford"

            # Switch to Bob
            app.dependency_overrides[get_current_user_dependency] = lambda: mock_user_bob

            # Bob checks my-bookings -> should be empty
            res_bob = await client.get("/api/applications/user/my-bookings")
            assert res_bob.status_code == 200
            bob_bookings = res_bob.json()["data"]
            assert len(bob_bookings) == 0

            # Bob creates a booking
            payload_bob = {
                "application_type": "hotel_bookings",
                "item_id": "taj-mahal-palace",
                "item_name": "The Taj Mahal Palace",
                "booking_date": "2026-12-15",
                "booking_time": "14:00",
                "guests_count": 2
            }
            res_bob_book = await client.post("/api/applications/book", json=payload_bob)
            assert res_bob_book.status_code == 200

            # Bob checks again -> only has 1
            res_bob2 = await client.get("/api/applications/user/my-bookings")
            assert res_bob2.status_code == 200
            bob_bookings2 = res_bob2.json()["data"]
            assert len(bob_bookings2) == 1
            assert bob_bookings2[0]["user_id"] == str(mock_user_bob.id)
            assert bob_bookings2[0]["item_name"] == "The Taj Mahal Palace"
    finally:
        app.dependency_overrides.pop(get_current_user_dependency, None)
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_google_places_fallback_no_broken_import(mock_user_alice):
    """Test 5: Fallback path does not crash with ModuleNotFoundError: No module named 'app.db.session'."""
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars

    mock_db_session = AsyncMock()
    mock_db_session.execute.return_value = mock_result

    app.dependency_overrides[get_current_user_dependency] = lambda: mock_user_alice
    app.dependency_overrides[get_async_db] = lambda: mock_db_session

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Calling nearby search with mock DB session and empty google result
            response = await client.get("/api/google/places/nearby?lat=12.9716&lng=77.5946&radius_km=5.0")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "places" in data["data"]
            assert data["data"]["places"] == []
    finally:
        app.dependency_overrides.pop(get_current_user_dependency, None)
        app.dependency_overrides.pop(get_async_db, None)

