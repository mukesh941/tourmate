"""
Single Motor (async MongoDB) client, shared across the app.
Import `get_db()` in services/routes - never open a new connection per-request.
"""
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

_client: AsyncIOMotorClient | None = None


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is not None:
        try:
            if _client.get_io_loop().is_closed():
                _client = None
        except Exception:
            _client = None

    if _client is None:
        _client = AsyncIOMotorClient(settings.mongo_uri)
    return _client


def close_client():
    global _client
    if _client is not None:
        _client.close()
        _client = None


def get_db():
    return get_client()[settings.mongo_db_name]


async def ensure_indexes():
    """Create indexes idempotently. Called once on startup."""
    try:
        db = get_db()
        await db.users.create_index("email", unique=True)
        await db.tourist_places.create_index("name")
        await db.tourist_places.create_index([("location", "2dsphere")])
        await db.tourist_places.create_index("destination_id")
    except Exception as e:
        print(f"Warning: Index creation skipped or delayed: {e}")
