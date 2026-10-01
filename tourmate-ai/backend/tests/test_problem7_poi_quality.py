"""
TourMate Problem 7 Test Suite:
POI / Attraction Coverage, Data Quality, Relationship Integrity, and Destination Isolation.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from app.main import app
from app.core.db import AsyncSessionLocal
from app.services.destination_resolver import resolve_destination


@pytest.mark.asyncio
async def test_poi_foreign_key_and_location_relationship():
    """1. Verify every POI references a valid location with valid coordinates inside India."""
    async with AsyncSessionLocal() as session:
        # Check for unresolvable location references
        res_unresolved = await session.execute(text("""
            SELECT count(p.id) FROM pois p
            LEFT JOIN locations l ON p.location_id = l.id
            WHERE l.id IS NULL
        """))
        assert res_unresolved.scalar() == 0, "Found POIs with orphaned location_id"

        # Check for non-empty names and valid coordinates
        res_coords = await session.execute(text("""
            SELECT p.name, l.latitude, l.longitude, l.city, l.state 
            FROM pois p
            JOIN locations l ON p.location_id = l.id
        """))
        pois = res_coords.fetchall()
        assert len(pois) > 0, "POIs table should not be empty"
        for p in pois:
            name, lat, lng, city, state = p
            assert name and len(name.strip()) > 0, "POI name cannot be empty"
            assert 6.0 <= lat <= 38.0, f"POI {name} latitude {lat} outside India"
            assert 68.0 <= lng <= 98.0, f"POI {name} longitude {lng} outside India"
            assert city, f"POI {name} location missing city"
            assert state, f"POI {name} location missing state"


@pytest.mark.asyncio
async def test_poi_category_integrity():
    """Verify all POIs map to one of the 7 canonical categories."""
    canonical_set = {"History", "Nature", "Culture", "Adventure", "Food", "Shopping", "Architecture"}
    async with AsyncSessionLocal() as session:
        res = await session.execute(text("""
            SELECT DISTINCT c.name FROM pois p
            JOIN categories c ON p.category_id = c.id
        """))
        categories = {row[0] for row in res.fetchall()}
        assert categories.issubset(canonical_set), f"Invalid categories found: {categories - canonical_set}"


@pytest.mark.asyncio
async def test_no_duplicate_pois_within_location():
    """6. Verify no duplicate POI names exist within the same location."""
    async with AsyncSessionLocal() as session:
        res = await session.execute(text("""
            SELECT p.location_id, lower(trim(p.name)), count(*) 
            FROM pois p 
            GROUP BY p.location_id, lower(trim(p.name)) 
            HAVING count(*) > 1
        """))
        duplicates = res.fetchall()
        assert len(duplicates) == 0, f"Found duplicate POIs: {duplicates}"


@pytest.mark.asyncio
async def test_poi_destination_search_and_alias_mapping():
    """2. Verify POI search returns correct destination and resolves aliases (Delhi, Bangalore, Bombay, etc.)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Test Delhi alias
        res_delhi = await client.get("/api/places?destination=Delhi")
        assert res_delhi.status_code == 200
        delhi_places = res_delhi.json()["data"]
        assert len(delhi_places) >= 4
        delhi_names = {p["name"] for p in delhi_places}
        assert "Qutub Minar" in delhi_names
        assert "Red Fort" in delhi_names

        # Test Bangalore alias
        res_blr = await client.get("/api/places?destination=Bangalore")
        assert res_blr.status_code == 200
        blr_places = res_blr.json()["data"]
        assert len(blr_places) >= 3
        blr_names = {p["name"] for p in blr_places}
        assert "Bangalore Palace" in blr_names

        # Test Bombay alias
        res_bom = await client.get("/api/places?destination=Bombay")
        assert res_bom.status_code == 200
        bom_places = res_bom.json()["data"]
        assert len(bom_places) >= 2
        bom_names = {p["name"] for p in bom_places}
        assert "Gateway of India" in bom_names


@pytest.mark.asyncio
async def test_destination_isolation_no_cross_city_leakage():
    """3. Verify no unrelated-city POIs are returned for a specific destination."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res_jaipur = await client.get("/api/places?destination=Jaipur")
        assert res_jaipur.status_code == 200
        places = res_jaipur.json()["data"]
        for p in places:
            assert "taj mahal" not in p["name"].lower()
            assert "gateway of india" not in p["name"].lower()
            assert p["destination_id"] == "Jaipur"


@pytest.mark.asyncio
async def test_destination_with_zero_pois_returns_empty_safely():
    """5. Verify destinations with zero POIs return an empty list gracefully without crashing."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Nonexistent destination
        res_unknown = await client.get("/api/places?destination=AtlantisCity999")
        assert res_unknown.status_code == 200
        data_unknown = res_unknown.json()
        assert data_unknown["success"] is True
        assert data_unknown["data"] == []

        # Real city that has no POIs in DB
        res_empty_city = await client.get("/api/places?destination=Silvassa")
        assert res_empty_city.status_code == 200
        assert res_empty_city.json()["data"] == []


@pytest.mark.asyncio
async def test_ai_itinerary_uses_valid_grounded_pois():
    """8. Verify AI itinerary uses canonical PostgreSQL POIs and coordinates."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "destination_name": "Jaipur",
            "days": 1,
            "start_time": "09:00",
            "end_time": "18:00",
            "budget": "Medium"
        }
        res = await client.post("/api/itineraries/generate", json=payload)
        assert res.status_code == 200
        options = res.json()["data"]
        assert len(options) == 3
        balanced = options[0]
        activities = balanced["schedule"][0]["activities"]
        assert len(activities) > 0
        for act in activities:
            assert act["place_id"]
            assert act["name"] in {"Amer Fort", "Hawa Mahal", "Jantar Mantar"}
            assert 26.0 <= act["latitude"] <= 27.5
            assert 75.0 <= act["longitude"] <= 76.5


@pytest.mark.asyncio
async def test_regression_problem5_guides_intact():
    """10. Verify Problem 5 Local Expert (197 guides) remains functional."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/guides")
        assert res.status_code == 200
        guides = res.json()["data"]
        assert len(guides) >= 100
        for g in guides[:10]:
            assert len(g["id"]) == 24
            assert g["id"] not in ("g1", "g2", "g3", "g4")
