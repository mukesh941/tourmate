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


@pytest.mark.asyncio
async def test_normal_signup_creates_user(client: AsyncClient):
    import uuid
    from sqlalchemy import select
    from app.core.db import AsyncSessionLocal
    from app.models.sql.user import User

    unique_email = f"normal_user_{uuid.uuid4().hex[:8]}@example.com"
    response = await client.post(
        "/api/auth/register",
        json={
            "email": unique_email,
            "password": "Password123!",
            "name": "Normal User",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["role"] == "user"
    assert data["data"]["email"] == unique_email

    # Verify directly in database
    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User).where(User.email == unique_email))).scalar_one_or_none()
        assert user is not None
        assert user.role == "user"


@pytest.mark.asyncio
async def test_signup_request_with_is_admin_true_cannot_create_admin(client: AsyncClient):
    import uuid
    from sqlalchemy import select
    from app.core.db import AsyncSessionLocal
    from app.models.sql.user import User

    unique_email = f"attacker_is_admin_{uuid.uuid4().hex[:8]}@example.com"
    response = await client.post(
        "/api/auth/register",
        json={
            "email": unique_email,
            "password": "Password123!",
            "name": "Attacker Admin Attempt",
            "is_admin": True,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["role"] == "user"  # MUST BE 'user', NEVER 'admin'

    # Verify directly in database
    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User).where(User.email == unique_email))).scalar_one_or_none()
        assert user is not None
        assert user.role == "user"


@pytest.mark.asyncio
async def test_signup_request_with_role_admin_cannot_create_admin(client: AsyncClient):
    import uuid
    from sqlalchemy import select
    from app.core.db import AsyncSessionLocal
    from app.models.sql.user import User

    unique_email = f"attacker_role_admin_{uuid.uuid4().hex[:8]}@example.com"
    response = await client.post(
        "/api/auth/register",
        json={
            "email": unique_email,
            "password": "Password123!",
            "name": "Attacker Role Attempt",
            "role": "admin",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["role"] == "user"  # MUST BE 'user', NEVER 'admin'

    # Verify directly in database
    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User).where(User.email == unique_email))).scalar_one_or_none()
        assert user is not None
        assert user.role == "user"


@pytest.mark.asyncio
async def test_signup_request_with_both_admin_flags_cannot_create_admin(client: AsyncClient):
    import uuid
    from sqlalchemy import select
    from app.core.db import AsyncSessionLocal
    from app.models.sql.user import User

    unique_email = f"attacker_both_{uuid.uuid4().hex[:8]}@example.com"
    response = await client.post(
        "/api/auth/register",
        json={
            "email": unique_email,
            "password": "Password123!",
            "name": "Attacker Both Flags Attempt",
            "is_admin": True,
            "role": "admin",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["role"] == "user"  # MUST BE 'user', NEVER 'admin'

    # Verify directly in database
    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User).where(User.email == unique_email))).scalar_one_or_none()
        assert user is not None
        assert user.role == "user"


@pytest.mark.asyncio
async def test_login_and_jwt_workflow(client: AsyncClient):
    import uuid
    unique_email = f"login_user_{uuid.uuid4().hex[:8]}@example.com"
    password = "TestLoginPassword123!"

    # 1. Register user
    reg_res = await client.post(
        "/api/auth/register",
        json={"email": unique_email, "password": password, "name": "Login User"},
    )
    assert reg_res.status_code == 201

    # 2. Login
    login_res = await client.post(
        "/api/auth/login",
        json={"email": unique_email, "password": password},
    )
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert token_data["success"] is True
    access_token = token_data["data"]["access_token"]
    assert access_token is not None

    # 3. Access /auth/me with JWT
    me_res = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_res.status_code == 200
    user_me = me_res.json()["data"]
    assert user_me["email"] == unique_email
    assert user_me["role"] == "user"


@pytest.mark.asyncio
async def test_admin_provisioning_script():
    import uuid
    from sqlalchemy import select
    from app.core.db import AsyncSessionLocal
    from app.models.sql.user import User
    from app.scripts.create_admin import provision_admin

    admin_email = f"provisioned_admin_{uuid.uuid4().hex[:8]}@example.com"
    admin_pass = "SecureAdminPass123!"

    # 1. Provision new admin via secure script
    await provision_admin(email=admin_email, password=admin_pass, name="Provisioned Admin")

    # 2. Check directly in database
    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User).where(User.email == admin_email))).scalar_one_or_none()
        assert user is not None
        assert user.role == "admin"
        assert user.name == "Provisioned Admin"
        assert verify_password(admin_pass, user.password_hash) is True

    # 3. Promote an existing normal user
    normal_email = f"promote_target_{uuid.uuid4().hex[:8]}@example.com"
    normal_pass = "NormalTargetPass123!"
    async with AsyncSessionLocal() as session:
        target = User(
            email=normal_email,
            name="Target User",
            password_hash=hash_password(normal_pass),
            role="user",
            preferred_language="en",
            is_active=True,
        )
        session.add(target)
        await session.commit()

    # Promote via script
    await provision_admin(email=normal_email)
    async with AsyncSessionLocal() as session:
        promoted = (await session.execute(select(User).where(User.email == normal_email))).scalar_one_or_none()
        assert promoted is not None
        assert promoted.role == "admin"

