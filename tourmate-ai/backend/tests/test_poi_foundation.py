"""
Phase 2 Geographic & POI Data Foundation Test Suite.
Verifies PostgreSQL canonical records, relational integrity, schema boundaries,
vector embeddings, API compatibility, and Google API independence.
"""
import uuid
import math
import numpy as np
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine, inspect, text
from app.main import app
from app.core.config import settings
from app.db.seeds.seeder import seed_geographic_foundation


@pytest.fixture(scope="module")
def sync_engine():
    engine = create_engine(settings.sync_database_url)
    yield engine
    engine.dispose()


def test_locations_contain_pilot_data(sync_engine):
    """1. Verify locations table contains pilot data."""
    with sync_engine.connect() as conn:
        count = conn.execute(text("SELECT count(*) FROM locations;")).scalar()
        assert count >= 18, f"Expected at least 18 locations, found {count}"


def test_pois_contain_pilot_data(sync_engine):
    """2. Verify pois table contains pilot data."""
    with sync_engine.connect() as conn:
        count = conn.execute(text("SELECT count(*) FROM pois;")).scalar()
        assert count == 12, f"Expected 12 pilot POIs, found {count}"


def test_accommodations_contain_pilot_data(sync_engine):
    """3. Verify accommodations table contains pilot data."""
    with sync_engine.connect() as conn:
        count = conn.execute(text("SELECT count(*) FROM accommodations;")).scalar()
        assert count == 6, f"Expected 6 pilot accommodations, found {count}"


def test_poi_location_foreign_keys_resolve(sync_engine):
    """4. Verify every POI location_id resolves to an existing location."""
    with sync_engine.connect() as conn:
        unresolved = conn.execute(
            text("""
                SELECT count(*) FROM pois p
                LEFT JOIN locations l ON p.location_id = l.id
                WHERE l.id IS NULL;
            """)
        ).scalar()
        assert unresolved == 0, f"Found {unresolved} POIs with unresolvable location_id"


def test_poi_category_foreign_keys_resolve(sync_engine):
    """5. Verify every POI category_id resolves to an existing category."""
    with sync_engine.connect() as conn:
        unresolved = conn.execute(
            text("""
                SELECT count(*) FROM pois p
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE c.id IS NULL;
            """)
        ).scalar()
        assert unresolved == 0, f"Found {unresolved} POIs with unresolvable category_id"


def test_categories_belong_to_canonical_seven(sync_engine):
    """6. Verify every category assigned to a POI is one of the 7 canonical categories."""
    canonical_set = {"History", "Nature", "Culture", "Adventure", "Food", "Shopping", "Architecture"}
    with sync_engine.connect() as conn:
        cats = conn.execute(
            text("SELECT DISTINCT c.name FROM pois p JOIN categories c ON p.category_id = c.id;")
        ).fetchall()
        poi_categories = {row[0] for row in cats}
        assert poi_categories.issubset(canonical_set), f"Found non-canonical categories: {poi_categories - canonical_set}"


def test_pois_contain_no_coordinate_columns(sync_engine):
    """7. Verify POIs table contains no latitude or longitude columns."""
    inspector = inspect(sync_engine)
    poi_cols = {c["name"] for c in inspector.get_columns("pois")}
    assert "latitude" not in poi_cols, "pois table must not have a latitude column"
    assert "longitude" not in poi_cols, "pois table must not have a longitude column"
    assert "location_id" in poi_cols, "pois table must reference location_id"


def test_accommodations_contain_no_coordinate_columns(sync_engine):
    """8. Verify accommodations table contains no latitude or longitude columns."""
    inspector = inspect(sync_engine)
    acc_cols = {c["name"] for c in inspector.get_columns("accommodations")}
    assert "latitude" not in acc_cols, "accommodations table must not have a latitude column"
    assert "longitude" not in acc_cols, "accommodations table must not have a longitude column"
    assert "location_id" in acc_cols, "accommodations table must reference location_id"


def test_coordinates_are_valid(sync_engine):
    """9. Verify all location coordinates are within valid geographic bounds."""
    with sync_engine.connect() as conn:
        invalid = conn.execute(
            text("""
                SELECT count(*) FROM locations
                WHERE latitude < -90.0 OR latitude > 90.0
                   OR longitude < -180.0 OR longitude > 180.0;
            """)
        ).scalar()
        assert invalid == 0, f"Found {invalid} locations with out-of-range coordinates"


def test_ratings_and_price_tiers_within_limits(sync_engine):
    """10, 11, 12. Verify ratings, price tiers, and visit durations conform to constraints."""
    with sync_engine.connect() as conn:
        invalid = conn.execute(
            text("""
                SELECT count(*) FROM pois
                WHERE rating < 0.0 OR rating > 5.0
                   OR price_tier < 1 OR price_tier > 4
                   OR typical_visit_duration_minutes <= 0;
            """)
        ).scalar()
        assert invalid == 0, f"Found {invalid} POIs violating rating, price tier, or duration limits"


def test_accommodations_types_and_tiers_valid(sync_engine):
    """13, 14, 15. Verify accommodation types, budget tiers, and currencies conform."""
    with sync_engine.connect() as conn:
        invalid = conn.execute(
            text("""
                SELECT count(*) FROM accommodations
                WHERE type NOT IN ('hotel', 'hostel', 'dorm', 'guesthouse', 'resort')
                   OR budget_tier NOT IN ('budget', 'moderate', 'luxury')
                   OR currency != 'INR'
                   OR price_per_night < 0.0;
            """)
        ).scalar()
        assert invalid == 0, f"Found {invalid} accommodations with invalid type, tier, or currency"


def test_opening_hours_days_conformance(sync_engine):
    """16. Verify opening hours days are 0-6."""
    with sync_engine.connect() as conn:
        invalid = conn.execute(
            text("SELECT count(*) FROM opening_hours WHERE day_of_week < 0 OR day_of_week > 6;")
        ).scalar()
        assert invalid == 0, f"Found {invalid} opening hours with invalid day_of_week"


def test_media_references_resolve_and_no_duplicates(sync_engine):
    """17, 18. Verify image references resolve and no duplicate images exist."""
    with sync_engine.connect() as conn:
        poi_img_unresolved = conn.execute(
            text("SELECT count(*) FROM poi_images pi LEFT JOIN images i ON pi.image_id = i.id WHERE i.id IS NULL;")
        ).scalar()
        assert poi_img_unresolved == 0, "Found unresolved poi_images references"

        acc_img_unresolved = conn.execute(
            text("SELECT count(*) FROM accommodation_images ai LEFT JOIN images i ON ai.image_id = i.id WHERE i.id IS NULL;")
        ).scalar()
        assert acc_img_unresolved == 0, "Found unresolved accommodation_images references"

        # Unique external images
        dups = conn.execute(
            text("""
                SELECT source, external_image_id, count(*)
                FROM images
                WHERE source IS NOT NULL AND external_image_id IS NOT NULL
                GROUP BY source, external_image_id
                HAVING count(*) > 1;
            """)
        ).fetchall()
        assert len(dups) == 0, f"Found duplicate canonical images: {dups}"


def test_embeddings_dimension_and_normalization(sync_engine):
    """19, 20. Verify every seeded embedding has dimension 384 and L2 norm approx 1.0."""
    with sync_engine.connect() as conn:
        res = conn.execute(text("SELECT id, name, embedding FROM pois;"))
        rows = res.fetchall()
        assert len(rows) == 12
        for r in rows:
            vec_raw = r[2]
            assert vec_raw is not None, f"POI {r[1]} has null embedding"
            # Parse vector
            if isinstance(vec_raw, str):
                vec = [float(x) for x in vec_raw.strip("[]").split(",")]
            else:
                vec = list(vec_raw)
            assert len(vec) == 384, f"POI {r[1]} embedding dimension is {len(vec)}, expected 384"
            norm = np.linalg.norm(vec)
            assert math.isclose(norm, 1.0, rel_tol=1e-3), f"POI {r[1]} embedding is not normalized: norm={norm}"


def test_seeder_idempotency(sync_engine):
    """21. Verify running the seed twice does not duplicate records."""
    with sync_engine.begin() as conn:
        seed_geographic_foundation(conn)

    with sync_engine.connect() as conn:
        poi_count = conn.execute(text("SELECT count(*) FROM pois;")).scalar()
        assert poi_count == 12, f"Expected 12 POIs after repeat seed, found {poi_count}"
        loc_count = conn.execute(text("SELECT count(*) FROM locations;")).scalar()
        assert loc_count >= 18, f"Expected at least 18 locations after repeat seed, found {loc_count}"


@pytest.mark.asyncio
async def test_api_places_flow():
    """22-28. Test GET /api/places, GET /api/places/{id}, spatial search, and contract."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. GET /api/places
        res = await ac.get("/api/places")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        body = res.json()
        assert body["success"] is True
        places = body["data"]
        assert len(places) >= 12, f"Expected at least 12 places, got {len(places)}"

        # 2. Verify contract fields
        p = places[0]
        assert "id" in p
        assert "name" in p
        assert "description" in p
        assert "category_id" in p
        assert "rating" in p
        assert "price_level" in p
        assert "visit_duration_minutes" in p
        assert "feature_scores" in p

        # 3. Verify coordinates order is [longitude, latitude]
        assert p["location"] is not None
        assert p["location"]["type"] == "Point"
        coords = p["location"]["coordinates"]
        assert len(coords) == 2
        lng, lat = coords[0], coords[1]
        assert -180.0 <= lng <= 180.0
        assert -90.0 <= lat <= 90.0

        # 4. Verify images is always a list
        assert isinstance(p["images"], list)
        assert len(p["images"]) > 0

        # 5. GET /api/places/{id}
        taj_id = "b0000000-0000-0000-0000-000000000001"
        res_single = await ac.get(f"/api/places/{taj_id}")
        assert res_single.status_code == 200
        single = res_single.json()["data"]
        assert single["id"] == taj_id
        assert single["name"] == "Taj Mahal"
        assert single["rating"] == 4.9
        assert single["location"]["coordinates"] == [78.0421, 27.1751]

        # 6. Spatial search near Agra center (27.1751, 78.0421)
        res_spatial = await ac.get("/api/places?lat=27.1751&lng=78.0421&radius_km=20")
        assert res_spatial.status_code == 200
        spatial_places = res_spatial.json()["data"]
        names = [sp["name"] for sp in spatial_places]
        assert "Taj Mahal" in names
        assert "Agra Fort" in names
        assert "Gateway of India" not in names  # Mumbai place excluded

        # 7. Category filtering
        res_arch = await ac.get("/api/places?category_id=Architecture")
        assert res_arch.status_code == 200
        arch_places = res_arch.json()["data"]
        arch_names = [ap["name"] for ap in arch_places]
        assert "Taj Mahal" in arch_names
        assert "Amer Fort" not in arch_names  # History
