"""
Test suite for Location Resolution, State Validation, and Regression.
Ensures:
- Canonical destinations and all locations have valid non-empty states.
- Specific regression test for '4 Arm (Kharwali)' possessing state 'Rajasthan'.
- Alias resolution maps common historical/alternative names correctly.
- Foreign and unknown locations are safely handled without false positives.
"""
import pytest
from sqlalchemy import text
from app.core.db import AsyncSessionLocal
from app.services.destination_resolver import resolve_destination


@pytest.mark.asyncio
async def test_locations_all_have_non_empty_states():
    """Verify that all locations in PostgreSQL have a non-empty state."""
    async with AsyncSessionLocal() as session:
        res = await session.execute(text("SELECT count(*) FROM locations WHERE state IS NULL OR state = ''"))
        count = res.scalar()
        assert count == 0, f"Found {count} locations with missing or empty state"


@pytest.mark.asyncio
async def test_regression_destination_kharwali_state():
    """Verify specifically that 4 Arm (Kharwali) has state 'Rajasthan'."""
    async with AsyncSessionLocal() as session:
        res = await session.execute(text("SELECT id, name, city, state, country FROM locations WHERE name = '4 Arm (Kharwali)'"))
        row = res.fetchone()
        assert row is not None, "Location '4 Arm (Kharwali)' not found in database"
        assert row.state == "Rajasthan", f"Expected state 'Rajasthan', got {row.state!r}"
        assert row.country == "India"


@pytest.mark.asyncio
async def test_alias_resolution():
    """Verify alias mapping for legacy city names."""
    alias_map = {
        "Bangalore": ("bengaluru", "Karnataka"),
        "Bombay": ("mumbai", "Maharashtra"),
        "Madras": ("chennai", "Tamil Nadu"),
        "Calcutta": (("kolkata", "calcutta"), "West Bengal"),
        "Poona": ("pune", "Maharashtra"),
        "Mysore": ("mysuru", "Karnataka"),
        "Cochin": ("kochi", "Kerala"),
    }
    async with AsyncSessionLocal() as session:
        for alias, (expected_names, expected_state) in alias_map.items():
            dest = await resolve_destination(alias, session)
            assert dest is not None, f"Failed to resolve alias: {alias}"
            if isinstance(expected_names, str):
                expected_names = (expected_names,)
            assert dest["name"].lower() in expected_names, (
                f"Expected alias {alias} to resolve to one of {expected_names}, got {dest['name']}"
            )
            assert dest["state"].lower() == expected_state.lower(), (
                f"Expected state {expected_state}, got {dest['state']}"
            )



@pytest.mark.asyncio
async def test_foreign_and_unknown_locations():
    """Verify foreign locations and gibberish queries return None."""
    unknown_queries = ["XYZUnknownPlace999", "Paris", "London", "Tokyo"]
    async with AsyncSessionLocal() as session:
        for query in unknown_queries:
            dest = await resolve_destination(query, session)
            assert dest is None, f"Expected {query} to not resolve, but got {dest}"
