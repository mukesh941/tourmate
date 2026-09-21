import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.anyio
async def test_guides_endpoint_non_blocking_without_mongo():
    """Verify GET /api/guides returns a safe envelope without connecting to MongoDB."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/guides")
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert isinstance(body["data"], list)
        assert len(body["data"]) == 0


@pytest.mark.anyio
async def test_restaurants_endpoint_postgres_backed():
    """Verify GET /api/restaurants returns a safe envelope from PostgreSQL."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/restaurants")
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert isinstance(body["data"], list)


@pytest.mark.anyio
async def test_activities_endpoint_postgres_backed():
    """Verify GET /api/activities returns a safe envelope from PostgreSQL."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/activities")
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert isinstance(body["data"], list)


@pytest.mark.anyio
async def test_itinerary_generate_optional_auth():
    """Verify POST /api/itineraries/generate works with optional authentication."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "destination_name": "Agra",
            "days": 1,
            "start_time": "09:00",
            "end_time": "18:00",
            "energy_level": "Moderate",
            "budget": "Medium",
            "travel_type": "Solo",
            "transportation_mode": "car",
            "local_transportation": "taxi",
            "interests": ["History"]
        }
        res = await client.post("/api/itineraries/generate", json=payload)
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert isinstance(body["data"], list)
        assert len(body["data"]) == 3  # Balanced, Explorer, Relaxed
        assert body["data"][0]["route_name"] == "Balanced"
