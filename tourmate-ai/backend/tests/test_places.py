import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_places_no_auth(client: AsyncClient):
    # Fetching places is a public endpoint
    response = await client.get("/api/places")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)


@pytest.mark.asyncio
async def test_get_destinations(client: AsyncClient):
    # Fetching destinations is a public endpoint
    response = await client.get("/api/destinations")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)


@pytest.mark.asyncio
async def test_get_categories(client: AsyncClient):
    # Fetching categories is a public endpoint
    response = await client.get("/api/categories")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)
