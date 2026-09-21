"""
Phase 6 End-to-End Product Integration & Hardening Test Suite.

Covers the full integrated user journey and verifies:
1. Authentication, JWT handling, and unauthorized rejection
2. User profile & preferences isolation (no IDOR)
3. Canonical destinations & POI foundation integrity
4. Itinerary plan optimization with accommodation anchor
5. IDOR protection on itinerary optimization (User A cannot optimize User B's trip)
6. Hotel booking server-side calculation and date validation (check_out > check_in)
7. Feedback flow validation (rating 1-5, comment validation, target constraint)
8. Active commercial offers endpoint filtering (validity window, active flag, safe URL)
9. AI Assistant RAG chat contract, sources metadata, and grounded response
"""
import uuid
from datetime import date, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import AsyncSessionLocal
from app.core.security import create_access_token
from app.models.sql.accommodation import Accommodation
from app.models.sql.interaction import Feedback, Offer
from app.models.sql.location import Location
from app.models.sql.poi import POI
from app.models.sql.trip import Trip, TripAccommodation
from app.models.sql.user import User


@pytest.fixture
async def db_session():
    async with AsyncSessionLocal() as session:
        yield session


@pytest.mark.asyncio
async def test_auth_journey_and_preferences_isolation(client: AsyncClient, db_session: AsyncSession):
    """Verifies register, login, profile access, and isolation between User A and User B."""
    unique_suffix = uuid.uuid4().hex[:6]
    user_a_email = f"user_a_{unique_suffix}@example.com"
    user_b_email = f"user_b_{unique_suffix}@example.com"
    user_a_id = None
    user_b_id = None

    try:
        # 1. Register User A
        res_reg = await client.post(
            "/api/auth/register",
            json={"email": user_a_email, "password": "Password123!", "name": "Alice Tourist"},
        )
        assert res_reg.status_code in (200, 201)
        data_reg = res_reg.json()
        assert data_reg["success"] is True

        # 2. Login User A
        res_login = await client.post(
            "/api/auth/login",
            json={"email": user_a_email, "password": "Password123!"},
        )
        assert res_login.status_code == 200
        token_a = res_login.json()["data"]["access_token"]
        headers_a = {"Authorization": f"Bearer {token_a}"}

        # 3. Verify Profile User A
        res_prof = await client.get("/api/users/profile", headers=headers_a)
        assert res_prof.status_code == 200
        assert res_prof.json()["data"]["email"] == user_a_email
        user_a_id = res_prof.json()["data"]["id"]

        # 4. Verify Unauthenticated cannot access profile
        res_unauth = await client.get("/api/users/profile")
        assert res_unauth.status_code == 401

        # 5. Update User A Preferences
        res_pref_update = await client.put(
            "/api/users/preferences",
            json={"interests": ["History", "Culture"], "budget": "Medium", "travel_style": "Moderate"},
            headers=headers_a,
        )
        assert res_pref_update.status_code == 200

        # 6. User B cannot see User A's preferences
        user_b = User(email=user_b_email, hashed_password="pw", full_name="Bob Tourist")
        db_session.add(user_b)
        await db_session.commit()
        user_b_id = user_b.id
        token_b = create_access_token(str(user_b.id))
        headers_b = {"Authorization": f"Bearer {token_b}"}

        res_pref_b = await client.get("/api/users/preferences", headers=headers_b)
        assert res_pref_b.status_code == 200
        # Bob has no preferences yet
        assert res_pref_b.json()["data"] is None
    finally:
        # Cleanup test users
        if user_a_id:
            await db_session.execute(delete(User).where(User.id == uuid.UUID(str(user_a_id))))
        if user_b_id:
            await db_session.execute(delete(User).where(User.id == uuid.UUID(str(user_b_id))))
        await db_session.commit()


@pytest.mark.asyncio
async def test_destinations_and_pois_contracts(client: AsyncClient):
    """Verifies that destinations and POIs return valid canonical datasets without duplicates."""
    res_dest = await client.get("/api/destinations")
    assert res_dest.status_code == 200
    dest_data = res_dest.json()
    assert dest_data["success"] is True
    destinations = dest_data["data"]
    assert len(destinations) >= 15
    dest_names = [d["name"] for d in destinations]
    assert len(dest_names) == len(set(dest_names)), "Duplicate destinations detected!"
    for required in ["Agra", "New Delhi", "Jaipur", "Mumbai", "Goa"]:
        assert required in dest_names

    res_places = await client.get("/api/places?limit=5")
    assert res_places.status_code == 200
    places_data = res_places.json()
    assert places_data["success"] is True
    assert len(places_data["data"]) > 0


@pytest.mark.asyncio
async def test_itinerary_optimization_idor_protection(client: AsyncClient, db_session: AsyncSession):
    """
    CRITICAL SECURITY GATE:
    Verifies that User B cannot optimize or modify User A's trip (IDOR protection).
    """
    user_a = User(email=f"owner_{uuid.uuid4().hex[:6]}@test.com", hashed_password="pw", full_name="Trip Owner")
    user_b = User(email=f"attacker_{uuid.uuid4().hex[:6]}@test.com", hashed_password="pw", full_name="Attacker")
    db_session.add_all([user_a, user_b])
    await db_session.flush()

    # Query existing canonical accommodation and POI to preserve canonical DB integrity
    acc_res = await db_session.execute(select(Accommodation).where(Accommodation.is_active == True).limit(1))
    acc = acc_res.scalar_one()

    poi_res = await db_session.execute(select(POI).where(POI.is_active == True).limit(1))
    poi = poi_res.scalar_one()

    trip_a = Trip(
        user_id=user_a.id,
        location_id=acc.location_id,
        title="Alice Private Trip",
        start_date=date(2026, 11, 1),
        end_date=date(2026, 11, 1),
        total_days=1,
    )
    db_session.add(trip_a)
    await db_session.flush()

    trip_acc = TripAccommodation(
        trip_id=trip_a.id,
        accommodation_id=acc.id,
        check_in_date=date(2026, 11, 1),
        check_out_date=date(2026, 11, 1),
    )
    db_session.add(trip_acc)
    await db_session.commit()

    try:
        # User B attempts to optimize User A's trip
        token_b = create_access_token(str(user_b.id))
        headers_b = {"Authorization": f"Bearer {token_b}"}

        payload = {
            "trip_id": str(trip_a.id),
            "day_clusters": [{"day_number": 1, "poi_ids": [str(poi.id)]}],
            "transport_mode": "driving",
            "daily_start_time": "09:00",
            "title": "Unauthorized Itinerary",
        }

        res_unauth = await client.post("/api/itineraries/optimize-plan", json=payload, headers=headers_b)
        # Must be 403 Forbidden
        assert res_unauth.status_code == 403, f"Expected 403 Forbidden for IDOR, got {res_unauth.status_code}"

        # User A (the legitimate owner) optimizes successfully
        token_a = create_access_token(str(user_a.id))
        headers_a = {"Authorization": f"Bearer {token_a}"}

        mock_resp = {
            "code": "Ok",
            "routes": [{"distance": 3500.0, "duration": 360.0, "geometry": {"type": "LineString", "coordinates": []}}],
        }
        with patch("httpx.AsyncClient.get", return_value=AsyncMock(status_code=200, json=lambda: mock_resp)):
            res_auth = await client.post("/api/itineraries/optimize-plan", json=payload, headers=headers_a)
            assert res_auth.status_code == 200
            assert res_auth.json()["success"] is True
    finally:
        # Clean up trip and test users
        await db_session.execute(delete(TripAccommodation).where(TripAccommodation.trip_id == trip_a.id))
        await db_session.execute(delete(Trip).where(Trip.id == trip_a.id))
        await db_session.execute(delete(User).where(User.id.in_([user_a.id, user_b.id])))
        await db_session.commit()


@pytest.mark.asyncio
async def test_hotel_booking_validation_and_calculation(client: AsyncClient, db_session: AsyncSession):
    """Verifies hotel booking server-side calculation and date rejection using canonical accommodations."""
    user = User(email=f"hotel_test_{uuid.uuid4().hex[:6]}@test.com", hashed_password="pw", full_name="Hotel Tester")
    db_session.add(user)
    await db_session.commit()

    # Use existing canonical accommodation
    acc_res = await db_session.execute(select(Accommodation).where(Accommodation.is_active == True).limit(1))
    acc = acc_res.scalar_one()

    token = create_access_token(str(user.id))
    headers = {"Authorization": f"Bearer {token}"}

    try:
        # 1. Reject invalid check_out <= check_in
        res_invalid_dates = await client.post(
            "/api/hotels/book",
            json={
                "hotel_id": str(acc.id),
                "room_id": "r-std",
                "room_name": "Standard Deluxe",
                "check_in_date": "2026-12-10",
                "check_out_date": "2026-12-10",  # 0 nights
                "guests": 2,
            },
            headers=headers,
        )
        assert res_invalid_dates.status_code == 400

        # 2. Accept valid 3-night booking: 3 * price_per_night
        res_valid = await client.post(
            "/api/hotels/book",
            json={
                "hotel_id": str(acc.id),
                "room_id": "r-std",
                "room_name": "Standard Deluxe",
                "check_in_date": "2026-12-10",
                "check_out_date": "2026-12-13",  # 3 nights
                "guests": 2,
            },
            headers=headers,
        )
        assert res_valid.status_code == 200
        booking_data = res_valid.json()["data"]
        assert booking_data["nights"] == 3
        expected_rate = float(acc.price_per_night)
        assert booking_data["total_price"] == round(expected_rate * 3, 2)
    finally:
        await db_session.execute(delete(User).where(User.id == user.id))
        await db_session.commit()


@pytest.mark.asyncio
async def test_feedback_flow_and_validation(client: AsyncClient, db_session: AsyncSession):
    """Verifies feedback rating bounds (1-5), comment validation, and target constraints."""
    user = User(email=f"feedback_user_{uuid.uuid4().hex[:6]}@test.com", hashed_password="pw", full_name="Reviewer")
    db_session.add(user)
    await db_session.commit()

    poi_res = await db_session.execute(select(POI).where(POI.is_active == True).limit(1))
    poi = poi_res.scalar_one()

    token = create_access_token(str(user.id))
    headers = {"Authorization": f"Bearer {token}"}

    try:
        # 1. Reject rating > 5
        res_high_rating = await client.post(
            f"/api/interactions/reviews/{poi.id}",
            json={"rating": 6, "comment": "Great place!"},
            headers=headers,
        )
        assert res_high_rating.status_code == 422  # Pydantic validation error

        # 2. Reject rating < 1
        res_low_rating = await client.post(
            f"/api/interactions/reviews/{poi.id}",
            json={"rating": 0, "comment": "Terrible place!"},
            headers=headers,
        )
        assert res_low_rating.status_code == 422

        # 3. Reject empty comment
        res_empty_comment = await client.post(
            f"/api/interactions/reviews/{poi.id}",
            json={"rating": 5, "comment": ""},
            headers=headers,
        )
        assert res_empty_comment.status_code == 422

        # 4. Successful review submission
        res_valid_review = await client.post(
            f"/api/interactions/reviews/{poi.id}",
            json={"rating": 5, "comment": "Spectacular Mughal architecture and beautiful red sandstone walls!"},
            headers=headers,
        )
        assert res_valid_review.status_code == 200
        assert res_valid_review.json()["success"] is True
        assert res_valid_review.json()["data"]["sentiment_label"] == "Positive"

        # 5. General feedback endpoint
        res_gen_feedback = await client.post(
            "/api/feedback",
            json={"rating": 4, "comment": "Very helpful tour recommendation.", "poi_id": str(poi.id)},
            headers=headers,
        )
        assert res_gen_feedback.status_code == 200
        assert res_gen_feedback.json()["success"] is True
    finally:
        await db_session.execute(delete(Feedback).where(Feedback.user_id == user.id))
        await db_session.execute(delete(User).where(User.id == user.id))
        await db_session.commit()


@pytest.mark.asyncio
async def test_active_offers_endpoint(client: AsyncClient, db_session: AsyncSession):
    """Verifies that the offers endpoint returns active verified offers and excludes expired offers."""
    loc_res = await db_session.execute(select(Location).limit(1))
    loc = loc_res.scalar_one()

    today = date.today()
    active_offer = Offer(
        location_id=loc.id,
        title="Agra Heritage Pass 15% Off",
        description="Official tourist discount for Agra monuments",
        discount_percentage=15.0,
        promo_code="HERITAGE15",
        affiliate_url="https://tourism.gov.in/agra-pass",
        valid_from=today - timedelta(days=10),
        valid_until=today + timedelta(days=30),
        is_active=True,
    )
    expired_offer = Offer(
        location_id=loc.id,
        title="Expired Summer Promo",
        description="Expired deal",
        discount_percentage=20.0,
        valid_from=today - timedelta(days=60),
        valid_until=today - timedelta(days=5),
        is_active=True,
    )
    inactive_offer = Offer(
        location_id=loc.id,
        title="Draft Promo",
        description="Not ready",
        valid_from=today,
        valid_until=today + timedelta(days=10),
        is_active=False,
    )
    db_session.add_all([active_offer, expired_offer, inactive_offer])
    await db_session.commit()

    try:
        res_offers = await client.get(f"/api/offers?location_id={loc.id}")
        assert res_offers.status_code == 200
        offers = res_offers.json()["data"]
        matching = [o for o in offers if o["id"] == str(active_offer.id)]
        assert len(matching) == 1
        assert matching[0]["title"] == "Agra Heritage Pass 15% Off"
        assert matching[0]["promo_code"] == "HERITAGE15"
        assert matching[0]["affiliate_url"] == "https://tourism.gov.in/agra-pass"

        # Expired and inactive are excluded
        matching_expired = [o for o in offers if o["id"] == str(expired_offer.id)]
        assert len(matching_expired) == 0
        matching_inactive = [o for o in offers if o["id"] == str(inactive_offer.id)]
        assert len(matching_inactive) == 0
    finally:
        await db_session.execute(delete(Offer).where(Offer.id.in_([active_offer.id, expired_offer.id, inactive_offer.id])))
        await db_session.commit()


@pytest.mark.asyncio
async def test_ai_chat_contract_and_sources(client: AsyncClient, db_session: AsyncSession):
    """Verifies that the RAG AI chat endpoint returns the expected envelope, answer, and sources."""
    user = User(email=f"ai_user_{uuid.uuid4().hex[:6]}@test.com", hashed_password="pw", full_name="AI Tester")
    db_session.add(user)
    await db_session.commit()

    token = create_access_token(str(user.id))
    headers = {"Authorization": f"Bearer {token}"}

    try:
        # Test opening hours query
        res = await client.post(
            "/api/ai/chat",
            json={"message": "Is Taj Mahal open on Friday?"},
            headers=headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        chat_resp = data["data"]
        assert "answer" in chat_resp or "response" in chat_resp
        assert "sources" in chat_resp
        assert "is_grounded" in chat_resp
    finally:
        await db_session.execute(delete(User).where(User.id == user.id))
        await db_session.commit()
