import pytest
from httpx import AsyncClient
from app.services.auth_service import hash_password, verify_password


@pytest.mark.asyncio
async def test_security_headers_present(client: AsyncClient):
    response = await client.get("/api/health")
    assert response.status_code == 200
    headers = response.headers

    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert "1; mode=block" in headers.get("X-XSS-Protection", "")
    assert "max-age=" in headers.get("Strict-Transport-Security", "")


def test_password_hashing_security():
    raw_password = "SuperSecretPassword123!"
    hashed = hash_password(raw_password)

    # Must not store plaintext
    assert hashed != raw_password
    # Starts with bcrypt signature
    assert hashed.startswith("$2")
    # Verifies correctly
    assert verify_password(raw_password, hashed) is True
    # Rejects incorrect password
    assert verify_password("WrongPassword", hashed) is False


@pytest.mark.asyncio
async def test_protected_route_rejects_missing_token(client: AsyncClient):
    response = await client.get("/api/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_route_rejects_invalid_token(client: AsyncClient):
    response = await client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer invalid.jwt.token.here"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_route_forbidden_for_regular_user(client: AsyncClient, test_user):
    from app.main import app
    from app.api.deps import get_current_user_dependency

    app.dependency_overrides[get_current_user_dependency] = lambda: test_user
    try:
        response = await client.get("/api/admin/stats")
        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_admin_route_allowed_for_admin_user(client: AsyncClient, admin_user):
    from app.main import app
    from app.api.deps import get_current_user_dependency

    app.dependency_overrides[get_current_user_dependency] = lambda: admin_user
    try:
        response = await client.get("/api/admin/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "users" in data["data"]
        assert "destinations" in data["data"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_input_validation_invalid_email(client: AsyncClient):
    # Invalid email format should be caught by Pydantic EmailStr validation
    response = await client.post(
        "/api/auth/register",
        json={
            "email": "not-a-valid-email",
            "password": "ValidPassword123!",
            "name": "Test Name",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_input_validation_missing_fields(client: AsyncClient):
    # Missing required field 'password'
    response = await client.post(
        "/api/auth/register",
        json={
            "email": "valid@example.com",
            "name": "Test Name",
        },
    )
    assert response.status_code == 422
