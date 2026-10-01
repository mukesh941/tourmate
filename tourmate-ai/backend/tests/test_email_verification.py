import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.sql.user import User, EmailVerificationToken
from app.services.auth_service import hash_password
from unittest.mock import patch

from app.core.db import AsyncSessionLocal

@pytest.fixture
async def db_session():
    async with AsyncSessionLocal() as session:
        yield session

@pytest.fixture
def mock_send_email():
    with patch("app.services.auth_service.send_verification_email") as mock:
        yield mock

@pytest.mark.asyncio
async def test_registration_creates_unverified_user(client: AsyncClient, db_session: AsyncSession, mock_send_email):
    import uuid
    payload = {
        "name": "Test User",
        "email": f"test_verification_{uuid.uuid4().hex}@example.com",
        "password": "Password123!"
    }
    
    # 1. Registration
    response = await client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    
    # User should be unverified
    data = response.json()["data"]
    assert data["is_email_verified"] is False
    
    # No JWT should be returned
    assert "access_token" not in data
    
    # Email should be sent
    assert mock_send_email.called
    args = mock_send_email.call_args[0]
    assert args[0] == payload["email"]
    token = args[1]
    
    # Verify DB state
    stmt = select(User).where(User.email == payload["email"])
    user = (await db_session.execute(stmt)).scalar_one()
    assert user.is_email_verified is False
    assert user.password_hash != payload["password"]
    
    stmt = select(EmailVerificationToken).where(EmailVerificationToken.user_id == user.id)
    verification_token = (await db_session.execute(stmt)).scalar_one()
    assert verification_token.used_at is None
    assert verification_token.token_hash != token  # Token must be hashed
    
    # 2. Login fails because unverified
    login_payload = {"email": payload["email"], "password": payload["password"]}
    login_res = await client.post("/api/auth/login", json=login_payload)
    assert login_res.status_code == 401
    assert login_res.json()["detail"]["code"] == "email_unverified"
    
    # 3. Verification succeeds
    verify_res = await client.post("/api/auth/verify-email", json={"token": token})
    assert verify_res.status_code == 200
    
    # Verify DB updated
    await db_session.refresh(user)
    assert user.is_email_verified is True
    assert user.email_verified_at is not None
    
    await db_session.refresh(verification_token)
    assert verification_token.used_at is not None
    
    # Token cannot be reused
    verify_res2 = await client.post("/api/auth/verify-email", json={"token": token})
    assert verify_res2.status_code == 400
    
    # 4. Login succeeds now
    login_res2 = await client.post("/api/auth/login", json=login_payload)
    assert login_res2.status_code == 200
    assert "access_token" in login_res2.json()["data"]


@pytest.mark.asyncio
async def test_resend_verification(client: AsyncClient, db_session: AsyncSession, mock_send_email):
    import uuid
    payload = {
        "name": "Resend User",
        "email": f"resend_{uuid.uuid4().hex}@example.com",
        "password": "Password123!"
    }
    
    await client.post("/api/auth/register", json=payload)
    assert mock_send_email.call_count == 1
    
    resend_res = await client.post("/api/auth/resend-verification", json={"email": payload["email"]})
    assert resend_res.status_code == 200
    
    assert mock_send_email.call_count == 2
    args = mock_send_email.call_args[0]
    token = args[1]
    
    # New token works
    verify_res = await client.post("/api/auth/verify-email", json={"token": token})
    assert verify_res.status_code == 200

@pytest.mark.asyncio
async def test_existing_verified_user_can_login(client: AsyncClient, db_session: AsyncSession):
    # Simulate an existing user that has is_email_verified=True (due to migration)
    import uuid
    email = f"existing_verified_{uuid.uuid4().hex}@example.com"
    pwd = "Password123!"
    user = User(
        name="Existing",
        email=email,
        password_hash=hash_password(pwd),
        is_email_verified=True
    )
    db_session.add(user)
    await db_session.commit()
    
    login_res = await client.post("/api/auth/login", json={"email": email, "password": pwd})
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()["data"]
