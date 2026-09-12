import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_applications_overview(client: AsyncClient):
    response = await client.get("/api/applications")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    apps = data["data"]
    assert "campus_tours" in apps
    assert "hotel_bookings" in apps
    assert "historical_sites" in apps
    assert "restaurant_reservations" in apps

@pytest.mark.asyncio
async def test_get_application_by_type(client: AsyncClient):
    response = await client.get("/api/applications/hotel_bookings")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["title"] == "Hotel Room Bookings"
    assert len(data["data"]["hotels"]) > 0

@pytest.mark.asyncio
async def test_get_invalid_application_type(client: AsyncClient):
    response = await client.get("/api/applications/unknown_app")
    assert response.status_code == 404
