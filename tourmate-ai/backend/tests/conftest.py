import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import close_client
from app.services.auth_service import create_access_token
from app.schemas.auth import UserPublic


from app.core.db import async_engine


@pytest.fixture(autouse=True)
async def cleanup_db_client():
    yield
    close_client()
    await async_engine.dispose()


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
def test_user():
    return UserPublic(
        id="65f1a2b3c4d5e6f7a8b9c0d1",
        email="testuser@example.com",
        name="Test User",
        role="user",
        preferred_language="en",
    )


@pytest.fixture
def admin_user():
    return UserPublic(
        id="65f1a2b3c4d5e6f7a8b9c0d2",
        email="adminuser@example.com",
        name="Admin User",
        role="admin",
        preferred_language="en",
    )


@pytest.fixture
def user_token(test_user):
    return create_access_token({"sub": test_user.id, "email": test_user.email, "role": test_user.role})


@pytest.fixture
def admin_token(admin_user):
    return create_access_token({"sub": admin_user.id, "email": admin_user.email, "role": admin_user.role})
