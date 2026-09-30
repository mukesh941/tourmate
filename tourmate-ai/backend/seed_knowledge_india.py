"""
Seed knowledge_chunks for all tourist_destinations and major cities in the TourMate DB.

This script generates factual, location-grounded knowledge chunks for every
tourist_destination record in the locations table, using a template-based approach
that draws ONLY from verified database fields.

Usage:
    cd backend
    python seed_knowledge_india.py

The script:
1. Loads all tourist_destination locations from the DB
2. Generates 1-2 knowledge_chunks per location using factual templates
3. Embeds them with the same embedding model used for queries
4. Inserts only new chunks (skips existing ones by title)
5. Does NOT call external APIs or invent data
"""
import asyncio
import logging
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select, text, func, case
from app.core.db import AsyncSessionLocal
from app.models.sql.location import Location
from app.models.sql.knowledge import KnowledgeChunk
from app.services.embedding_service import get_embedding

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


# ── Template Generators ───────────────────────────────────────────────────────

def generate_destination_chunk(loc: Location) -> dict:
    """
    Generate a single knowledge_chunk from a tourist_destination or city Location record.
    Uses ONLY verified fields: name, state, description, category, best_time_to_visit.
    Does NOT invent any facts.
    """
    name = loc.name
    state = loc.state or "India"
    loc_type = loc.location_type or "destination"
    category = loc.category or ""
    desc = loc.description or ""
    best_time = loc.best_time_to_visit or ""
    city = loc.city or name
    lat = loc.latitude
    lon = loc.longitude

    # Build a factual description
    parts = []

    if loc_type == "tourist_destination":
        parts.append(f"{name} is a tourist destination located in {state}, India.")
    elif loc_type == "city":
        parts.append(f"{name} is a city in {state}, India.")
    elif loc_type == "state":
        parts.append(f"{name} is an Indian state/union territory.")
    else:
        parts.append(f"{name} is a location in {state}, India.")

    if category:
        parts.append(f"It is known for its {category.lower()} character.")

    if desc:
        parts.append(desc)

    if best_time:
        parts.append(f"Best time to visit {name}: {best_time}.")

    if lat and lon:
        parts.append(f"Geographic coordinates: {lat:.4f}N, {lon:.4f}E.")

    content = " ".join(parts)

    title = f"{name}: Travel Guide and Overview ({state})"
    source = "tourmate_location_database / geographic_verified"

    return {
        "title": title,
        "content": content,
        "source": source,
    }


def generate_state_chunk(loc: Location) -> dict:
    """Generate knowledge_chunk for a state-level location."""
    name = loc.name
    desc = loc.description or ""
    best_time = loc.best_time_to_visit or ""
    category = loc.category or ""

    parts = [f"{name} is an Indian state/union territory."]
    if desc:
        parts.append(desc)
    if category:
        parts.append(f"Known for: {category}.")
    if best_time:
        parts.append(f"Best time to visit: {best_time}.")

    content = " ".join(parts)
    return {
        "title": f"{name}: State Overview and Travel Guide",
        "content": content,
        "source": "tourmate_location_database / state_verified",
    }


async def get_existing_titles(session) -> set:
    """Fetch all existing knowledge_chunk titles to avoid duplicates."""
    result = await session.execute(text("SELECT title FROM knowledge_chunks"))
    rows = result.fetchall()
    return {row[0] for row in rows}


async def seed_knowledge():
    """Main seeder: processes all tourist_destinations and states."""
    inserted = 0
    skipped = 0
    errors = 0

    async with AsyncSessionLocal() as session:
        existing_titles = await get_existing_titles(session)
        logger.info("Existing knowledge_chunks titles: %d", len(existing_titles))

        # Fetch all tourist_destinations
        stmt = select(Location).where(
            Location.location_type.in_(["tourist_destination", "state", "city"])
        ).order_by(
            case(
                (Location.location_type == "state", 1),
                (Location.location_type == "tourist_destination", 2),
                (Location.location_type == "city", 3),
                else_=4
            )
        )
        result = await session.execute(stmt)
        locations = result.scalars().all()

        logger.info("Processing %d locations...", len(locations))

        batch = []

        for i, loc in enumerate(locations):
            try:
                if loc.location_type == "state":
                    chunk_data = generate_state_chunk(loc)
                else:
                    chunk_data = generate_destination_chunk(loc)

                title = chunk_data["title"]

                if title in existing_titles:
                    skipped += 1
                    continue

                # Generate embedding
                content_for_embed = f"{title}. {chunk_data['content']}"
                embedding = get_embedding(content_for_embed)

                chunk = KnowledgeChunk(
                    title=title,
                    content=chunk_data["content"],
                    embedding=embedding,
                    source=chunk_data["source"],
                    poi_id=None,
                )
                batch.append(chunk)
                existing_titles.add(title)

                # Commit in batches of 50
                if len(batch) >= 50:
                    session.add_all(batch)
                    await session.commit()
                    inserted += len(batch)
                    logger.info("Committed batch: %d total inserted so far", inserted)
                    batch = []

            except Exception as e:
                logger.error("Error processing location %s: %s", loc.name, e)
                errors += 1

        # Commit remaining
        if batch:
            session.add_all(batch)
            await session.commit()
            inserted += len(batch)

    logger.info("=" * 60)
    logger.info("Knowledge seeding complete:")
    logger.info("  Inserted: %d", inserted)
    logger.info("  Skipped (already existed): %d", skipped)
    logger.info("  Errors: %d", errors)
    logger.info("=" * 60)

    return inserted, skipped, errors


if __name__ == "__main__":
    asyncio.run(seed_knowledge())
