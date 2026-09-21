import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"success": True, "data": {"status": "ok"}, "error": None}


@pytest.mark.asyncio
async def test_rate_limiter_login(client: AsyncClient, monkeypatch):
    from app.services.auth_service import AuthError
    async def mock_login(payload):
        raise AuthError("Incorrect email or password.")
    monkeypatch.setattr("app.api.routes.auth.login_user", mock_login)

    # Limit is 5/minute
    for _ in range(5):
        await client.post("/api/auth/login", json={"email": "rate_limit_test@example.com", "password": "fake"})

    # The 6th request should be rate-limited
    response = await client.post("/api/auth/login", json={"email": "rate_limit_test@example.com", "password": "fake"})
    assert response.status_code == 429
    assert "Rate limit exceeded" in response.json()["error"]


@pytest.mark.asyncio
async def test_cors_preflight_production_vercel(client: AsyncClient):
    response = await client.options(
        "/api/auth/login",
        headers={
            "Origin": "https://frontend-delta-six-hf0z79dpo8.vercel.app",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type,Authorization",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "https://frontend-delta-six-hf0z79dpo8.vercel.app"
    assert response.headers.get("access-control-allow-credentials") == "true"


@pytest.mark.asyncio
async def test_cors_on_error_response(client: AsyncClient, monkeypatch):
    from app.core.limiter import limiter
    limiter.reset()
    from app.services.auth_service import AuthError
    async def mock_login(payload, db=None):
        raise AuthError("Invalid credentials test")
    monkeypatch.setattr("app.api.routes.auth.login_user", mock_login)

    response = await client.post(
        "/api/auth/login",
        json={"email": "cors_test@example.com", "password": "fake"},
        headers={"Origin": "https://frontend-delta-six-hf0z79dpo8.vercel.app"},
    )
    assert response.status_code == 401
    assert response.headers.get("access-control-allow-origin") == "https://frontend-delta-six-hf0z79dpo8.vercel.app"


@pytest.mark.asyncio
async def test_cors_on_unhandled_500_exception(client: AsyncClient, monkeypatch):
    from app.core.limiter import limiter
    limiter.reset()
    async def mock_login(payload, db=None):
        raise RuntimeError("Simulated unhandled DB crash")
    monkeypatch.setattr("app.api.routes.auth.login_user", mock_login)

    response = await client.post(
        "/api/auth/login",
        json={"email": "crash_test@example.com", "password": "fake"},
        headers={"Origin": "https://frontend-delta-six-hf0z79dpo8.vercel.app"},
    )
    assert response.status_code == 500
    assert response.headers.get("access-control-allow-origin") == "https://frontend-delta-six-hf0z79dpo8.vercel.app"
    data = response.json()
    assert data["success"] is False
    assert "Simulated unhandled DB crash" in data["error"]["detail"]
