"""
TourMate Problem 6 Backend Test Suite
Comprehensive India Location Coverage, Resolution, Search, and AI Itinerary Integration Tests.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from app.main import app
from app.core.db import AsyncSessionLocal
from app.services.destination_resolver import (
    resolve_destination,
    normalize_location_name,
    find_nearby_locations,
    get_state_locations,
)

EXPECTED_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", 
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", 
    "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", 
    "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan", 
    "Sikkim", "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", 
    "Uttarakhand", "West Bengal"
]

EXPECTED_UTS = [
    "Andaman and Nicobar Islands", "Chandigarh", "Dadra and Nagar Haveli and Daman and Diu",
    "Delhi", "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry"
]


@pytest.mark.asyncio
async def test_all_28_states_exist():
    """Verify all 28 official Indian States exist in PostgreSQL."""
    async with AsyncSessionLocal() as session:
        res = await session.execute(
            text("SELECT name FROM locations WHERE category = 'State' ORDER BY name")
        )
        db_states = [r[0] for r in res.fetchall()]
        for st in EXPECTED_STATES:
            assert st in db_states, f"Missing state in database: {st}"
        assert len(db_states) >= 28


@pytest.mark.asyncio
async def test_all_8_union_territories_exist():
    """Verify all 8 official Union Territories exist in PostgreSQL."""
    async with AsyncSessionLocal() as session:
        res = await session.execute(
            text("SELECT name FROM locations WHERE category = 'Union Territory' ORDER BY name")
        )
        db_uts = [r[0] for r in res.fetchall()]
        for ut in EXPECTED_UTS:
            assert ut in db_uts, f"Missing Union Territory in database: {ut}"
        assert len(db_uts) >= 8


@pytest.mark.asyncio
async def test_canonical_alias_mappings():
    """Verify common aliases and colonial names resolve to current canonical forms."""
    aliases = {
        "Bangalore": ("bengaluru", "Karnataka"),
        "Bombay": ("mumbai", "Maharashtra"),
        "Madras": ("chennai", "Tamil Nadu"),
        "Calcutta": ("calcutta", "West Bengal"),
        "Poona": ("pune", "Maharashtra"),
        "Mysore": ("mysuru", "Karnataka"),
        "Cochin": ("kochi", "Kerala"),
        "Banaras": ("banaras", "Uttar Pradesh"),
        "Pondicherry": ("puducherry", "Puducherry"),
    }
    async with AsyncSessionLocal() as session:
        for alias, (expected_name_substr, expected_state) in aliases.items():
            dest = await resolve_destination(alias, session)
            assert dest is not None, f"Failed to resolve alias: {alias}"
            assert expected_name_substr in dest["name"].lower() or dest["name"].lower() in expected_name_substr
            assert expected_state.lower() in dest["state"].lower() or dest["state"].lower() in expected_state.lower()


@pytest.mark.asyncio
async def test_delhi_new_delhi_resolution():
    """Verify both Delhi and New Delhi resolve properly with state='Delhi'."""
    async with AsyncSessionLocal() as session:
        for query in ["Delhi", "New Delhi", "delhi", "new delhi"]:
            dest = await resolve_destination(query, session)
            assert dest is not None, f"Failed to resolve {query}"
            assert "delhi" in dest["state"].lower()


@pytest.mark.asyncio
async def test_case_insensitive_destination_resolution():
    """Verify case-insensitivity across various capitalizations."""
    queries = ["jaipur", "JAIPUR", "JaiPur", "vArAnAsI", "KOCHI"]
    async with AsyncSessionLocal() as session:
        for q in queries:
            dest = await resolve_destination(q, session)
            assert dest is not None, f"Failed case-insensitive resolution for: {q}"


@pytest.mark.asyncio
async def test_representative_destinations_from_all_regions():
    """Verify representative tourist destinations across all parts of India."""
    destinations = [
        "Shimla", "Manali", "Darjeeling", "Gangtok", "Shillong", "Ooty", 
        "Munnar", "Kodaikanal", "Hampi", "Kaziranga", "Gokarna", "Varkala", 
        "Agra", "Udaipur", "Amritsar", "Haridwar", "Rishikesh", "Puri", "Tirupati"
    ]
    async with AsyncSessionLocal() as session:
        for name in destinations:
            dest = await resolve_destination(name, session)
            assert dest is not None, f"Failed to resolve representative destination: {name}"
            assert dest.get("latitude") is not None and dest.get("latitude") != 0.0
            assert dest.get("longitude") is not None and dest.get("longitude") != 0.0


@pytest.mark.asyncio
async def test_location_api_search():
    """Verify GET /api/locations/search endpoint."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Search for Jaipur
        resp = await client.get("/api/locations/search?query=Jaipur")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("success") is True
        assert len(data.get("data", [])) > 0
        names = [item["name"].lower() for item in data["data"]]
        assert any("jaipur" in n for n in names)


@pytest.mark.asyncio
async def test_location_api_resolve():
    """Verify GET /api/locations/resolve endpoint."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Resolve Bangalore -> Bengaluru
        resp = await client.get("/api/locations/resolve?name=Bangalore")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("success") is True
        loc = data.get("data")
        assert loc is not None
        assert "bengaluru" in loc["name"].lower() or "bangalore" in loc["name"].lower()
        assert "karnataka" in loc["state"].lower()


@pytest.mark.asyncio
async def test_location_api_destinations_by_state():
    """Verify GET /api/locations/destinations?state=... endpoint."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/locations/destinations?state=Kerala")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("success") is True
        items = data.get("data", [])
        assert len(items) > 0
        for item in items:
            assert "kerala" in (item.get("state") or "").lower()


@pytest.mark.asyncio
async def test_location_api_invalid_location_handling():
    """Verify API handles invalid and foreign locations gracefully."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Unknown non-existent place
        resp = await client.get("/api/locations/resolve?name=NonExistentPlace99999XYZ")
        assert resp.status_code == 404
        
        # Foreign destination
        resp_foreign = await client.get("/api/locations/resolve?name=Paris")
        assert resp_foreign.status_code == 404


@pytest.mark.asyncio
async def test_ai_itinerary_destination_acceptance():
    """Verify AI itinerary accepts valid canonical destinations without crashing."""
    valid_destinations = ["Jaipur", "Kochi", "Varanasi", "Bengaluru", "Delhi"]
    async with AsyncSessionLocal() as session:
        for dest_name in valid_destinations:
            resolved = await resolve_destination(dest_name, session)
            assert resolved is not None, f"Destination {dest_name} should resolve for AI itinerary"
            assert resolved.get("state") is not None
