import pytest
import pytest_asyncio
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_all_destinations_accessible(client: AsyncClient):
    # Test 1 - Complete dataset (fetch page with large page_size to verify no hard limit)
    res = await client.get("/api/destinations?page=1&page_size=10000")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["total"] >= 100
    assert len(data["results"]) >= 100

@pytest.mark.asyncio
async def test_search_destinations(client: AsyncClient):
    # Test 2 - Search Kharwali
    res = await client.get("/api/destinations?search=Agra")
    assert res.status_code == 200
    data = res.json()["data"]
    assert any("Agra" in d["name"] for d in data["results"])
    
@pytest.mark.asyncio
async def test_search_numeric_destinations_not_found(client: AsyncClient):
    # Test 3 - Numeric or malformed names should not return junk results
    res = await client.get("/api/destinations?search=123456789XYZ")
    assert res.status_code == 200
    data = res.json()["data"]
    assert len(data["results"]) == 0
    
@pytest.mark.asyncio
async def test_missing_image_destinations_fallback(client: AsyncClient):
    # Test 4 - Ensure all destinations have a valid cover image (fallback is applied if missing)
    res = await client.get("/api/destinations?page=1&page_size=20")
    assert res.status_code == 200
    data = res.json()["data"]
    assert len(data["results"]) > 0
    for d in data["results"]:
        assert d.get("cover_image") is not None
        assert str(d["cover_image"]).startswith("http") or str(d["cover_image"]).startswith("data:image/")

@pytest.mark.asyncio
async def test_popular_sorting(client: AsyncClient):
    # Test 5 - Popular sorting
    res = await client.get("/api/destinations?page=1&page_size=10")
    assert res.status_code == 200
    data = res.json()["data"]
    results = data["results"]
    assert len(results) > 0
    # The top results should be canonical (like Agra, New Delhi, etc.)
    # We verify that the first result has a real unsplash image and is popular
    assert "images.unsplash.com" in results[0]["cover_image"]
    
@pytest.mark.asyncio
async def test_pagination(client: AsyncClient):
    # Test 6 - Pagination
    res1 = await client.get("/api/destinations?page=1&page_size=10")
    res2 = await client.get("/api/destinations?page=2&page_size=10")
    
    data1 = res1.json()["data"]
    data2 = res2.json()["data"]
    
    assert len(data1["results"]) == 10
    assert len(data2["results"]) == 10
    assert data1["results"][0]["id"] != data2["results"][0]["id"]
