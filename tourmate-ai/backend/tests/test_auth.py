import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"success": True, "data": {"status": "ok"}, "error": None}


@pytest.mark.asyncio
async def test_rate_limiter_login(client: AsyncClient):
    # Limit is 5/minute
    for _ in range(5):
        await client.post("/api/auth/login", json={"email": "rate_limit_test@example.com", "password": "fake"})

    # The 6th request should be rate-limited
    response = await client.post("/api/auth/login", json={"email": "rate_limit_test@example.com", "password": "fake"})
    assert response.status_code == 429
    assert "Rate limit exceeded" in response.json()["error"]
