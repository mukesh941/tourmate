"""
Business logic for registration/login/current-user lookup.
Routes stay thin controllers; this is where DB + security helpers are orchestrated.
"""
from bson import ObjectId
from bson.errors import InvalidId

from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.models.user import UserInDB
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserPublic


class AuthError(Exception):
    """Raised for any auth failure the API layer should turn into a 4xx."""


def _to_public(doc: dict) -> UserPublic:
    return UserPublic(
        id=str(doc["_id"]),
        name=doc["name"],
        email=doc["email"],
        role=doc.get("role", "user"),
        preferred_language=doc.get("preferred_language", "en"),
    )


async def register_user(payload: RegisterRequest) -> UserPublic:
    db = get_db()
    existing = await db.users.find_one({"email": payload.email})
    if existing:
        raise AuthError("An account with this email already exists.")

    user = UserInDB(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role="admin" if payload.is_admin else "user",
    )
    result = await db.users.insert_one(user.model_dump())
    doc = await db.users.find_one({"_id": result.inserted_id})
    return _to_public(doc)


async def login_user(payload: LoginRequest) -> TokenResponse:
    db = get_db()
    doc = await db.users.find_one({"email": payload.email})
    if not doc or not verify_password(payload.password, doc["password_hash"]):
        raise AuthError("Incorrect email or password.")

    subject = str(doc["_id"])
    return TokenResponse(
        access_token=create_access_token(subject),
        refresh_token=create_refresh_token(subject),
    )


async def get_current_user(user_id: str) -> UserPublic:
    db = get_db()
    try:
        oid = ObjectId(user_id)
    except InvalidId as exc:
        raise AuthError("Invalid user id in token.") from exc

    doc = await db.users.find_one({"_id": oid})
    if not doc:
        raise AuthError("User not found.")
    return _to_public(doc)
