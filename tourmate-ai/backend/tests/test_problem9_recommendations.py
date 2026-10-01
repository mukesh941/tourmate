import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import text
from app.core.db import AsyncSessionLocal
from app.core.security import create_access_token
from app.models.sql.user import User, Preference, UserInterest
from app.models.sql.category import Category


@pytest.fixture
async def db_session():
    async with AsyncSessionLocal() as session:
        yield session


@pytest.fixture
async def sample_user(db_session):
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email=f"prob9_tester_{user_id.hex[:8]}@example.com",
        password_hash="hashed_pw_test",
        name="Problem 9 Tester",
        role="user",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token = create_access_token(str(user.id))
    yield user, token

    # Cleanup
    await db_session.execute(text("DELETE FROM users WHERE id = :uid"), {"uid": user_id})
    await db_session.commit()


@pytest.mark.asyncio
async def test_guest_recommendations_without_auth(client: AsyncClient):
    """
    Step 4 / Guest:
    GET /api/places/recommendations without Authorization header must succeed
    with HTTP 200 and return curated general recommendations.
    """
    response = await client.get("/api/places/recommendations")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)
    assert len(data["data"]) > 0

    first_item = data["data"][0]
    assert "id" in first_item
    assert "name" in first_item
    assert "rating" in first_item
    assert "description" in first_item


@pytest.mark.asyncio
async def test_authenticated_user_recommendations(client: AsyncClient, sample_user):
    """
    Step 4 / Authenticated:
    GET /api/places/recommendations with valid Bearer token must succeed
    with HTTP 200 and personalized recommendations.
    """
    user, token = sample_user
    response = await client.get(
        "/api/places/recommendations",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)
    assert len(data["data"]) > 0


@pytest.mark.asyncio
async def test_recommendations_with_invalid_token(client: AsyncClient):
    """
    Step 4 / Invalid Token:
    GET /api/places/recommendations with an invalid or malformed Bearer token
    should gracefully treat the user as a guest and return HTTP 200 with general recommendations.
    """
    response = await client.get(
        "/api/places/recommendations",
        headers={"Authorization": "Bearer invalid.expired.token"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)
    assert len(data["data"]) > 0


@pytest.mark.asyncio
async def test_recommendations_with_destination_filter_guest(client: AsyncClient):
    """
    Guest can also filter recommendations by destination (e.g. Jaipur or Agra).
    """
    response = await client.get("/api/places/recommendations?destination=Jaipur&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)
    assert len(data["data"]) <= 5


@pytest.mark.asyncio
async def test_protected_endpoints_remain_protected(client: AsyncClient):
    """
    Verifies that changing /recommendations to optional auth does NOT bypass security
    on genuinely protected endpoints.
    """
    # 1. Recommendation plan requires authentication
    res_plan = await client.post(
        "/api/places/recommendations/plan",
        json={"destination": "Jaipur", "total_days": 2, "daily_start_time": "09:00"}
    )
    assert res_plan.status_code == 401

    # 2. User profile requires authentication
    res_profile = await client.get("/api/users/profile")
    assert res_profile.status_code == 401

    # 3. Admin places requires admin authentication
    res_admin = await client.post(
        "/api/places",
        json={"name": "Test Place", "description": "Test", "destination_id": "Goa"}
    )
    assert res_admin.status_code == 401
