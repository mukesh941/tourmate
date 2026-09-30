"""
Link unlinked cities to their parent state records via parent_id.

Many of the 6,801 city records in the DB have the `state` field set correctly
but are missing the `parent_id` FK to their state's location record.

This script:
1. Builds a map: state_name -> state location UUID
2. For each city with parent_id IS NULL, sets parent_id = state UUID if state field matches
3. Reports summary stats

Does NOT modify any location data (name, coords, etc.) — only sets parent_id.
Does NOT delete or duplicate records.

Usage:
    cd backend
    python link_cities_to_states.py
"""
import asyncio
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select, text, update, func
from app.core.db import AsyncSessionLocal
from app.models.sql.location import Location

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


async def link_cities_to_states():
    linked = 0
    skipped = 0
    not_found = 0

    async with AsyncSessionLocal() as session:
        # Build state name -> UUID map (case-insensitive)
        state_result = await session.execute(
            select(Location.id, Location.name, Location.state)
            .where(Location.location_type == "state")
        )
        state_rows = state_result.fetchall()
        state_map = {}  # lowercase state name -> UUID
        for row in state_rows:
            key = row.name.lower().strip()
            state_map[key] = row.id
            if row.state:
                alt_key = row.state.lower().strip()
                state_map[alt_key] = row.id

        logger.info("Found %d state records, building map for %d keys", len(state_rows), len(state_map))

        # Get cities without parent_id
        unlinked_result = await session.execute(
            select(Location.id, Location.name, Location.state, Location.location_type)
            .where(
                Location.parent_id.is_(None),
                Location.location_type.in_(["city", "town", "district", "tourist_destination"])
            )
        )
        unlinked = unlinked_result.fetchall()
        logger.info("Found %d unlinked locations to process", len(unlinked))

        batch_updates = []
        for row in unlinked:
            if not row.state:
                skipped += 1
                continue

            state_key = row.state.lower().strip()
            state_id = state_map.get(state_key)

            if not state_id:
                not_found += 1
                continue

            batch_updates.append({"loc_id": row.id, "parent_id": state_id})

        logger.info("Will link %d records", len(batch_updates))

        # Execute updates in batches
        BATCH_SIZE = 500
        for i in range(0, len(batch_updates), BATCH_SIZE):
            batch = batch_updates[i:i + BATCH_SIZE]
            for item in batch:
                await session.execute(
                    update(Location)
                    .where(Location.id == item["loc_id"])
                    .values(parent_id=item["parent_id"])
                )
            await session.commit()
            linked += len(batch)
            logger.info("Linked batch %d-%d (%d so far)", i, i + len(batch), linked)

    logger.info("=" * 60)
    logger.info("City-to-state linking complete:")
    logger.info("  Linked: %d", linked)
    logger.info("  Skipped (no state field): %d", skipped)
    logger.info("  State not found: %d", not_found)
    logger.info("=" * 60)

    return linked, skipped, not_found


if __name__ == "__main__":
    asyncio.run(link_cities_to_states())
