import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"success": True, "data": {"status": "ok"}, "error": None}

@pytest.mark.asyncio
async def test_rate_limiter_login():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Send 6 quick requests to trigger the rate limiter (limit is 5/minute)
        for _ in range(5):
            res = await ac.post("/api/auth/login", json={"email": "fake@example.com", "password": "fake"})
        
        # The 6th request should be rate-limited
        response = await ac.post("/api/auth/login", json={"email": "fake@example.com", "password": "fake"})
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.json()["error"]
