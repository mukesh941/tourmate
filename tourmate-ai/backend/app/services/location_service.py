"""
Location service for querying canonical PostgreSQL locations.
"""
from typing import List, Dict, Any
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.sql.location import Location


async def search_postgres_locations(query: str, db: AsyncSession, limit: int = 10) -> List[Dict[str, Any]]:
    """Search canonical locations in PostgreSQL by name, city, state, or country."""
    if not query or len(query.strip()) < 2:
        return []

    pattern = f"%{query.strip().lower()}%"
    stmt = (
        select(Location)
        .where(
            or_(
                func.lower(Location.name).like(pattern),
                func.lower(Location.city).like(pattern),
                func.lower(Location.state).like(pattern),
                func.lower(Location.country).like(pattern),
                func.lower(Location.address).like(pattern),
            )
        )
        .limit(limit)
    )

    result = await db.execute(stmt)
    locations = result.scalars().all()

    return [
        {
            "id": str(loc.id),
            "name": loc.name,
            "type": "location",
            "city": loc.city,
            "state": loc.state,
            "country": loc.country,
            "lat": loc.latitude,
            "lng": loc.longitude,
            "address": loc.address,
        }
        for loc in locations
    ]
