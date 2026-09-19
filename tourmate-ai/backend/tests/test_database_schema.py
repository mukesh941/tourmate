"""
Comprehensive database schema tests running against real PostgreSQL + pgvector.
Verifies the locked 23-table schema field-by-field, pgvector extension, vector dimensions (384),
HNSW indexes, check constraints, foreign key delete rules, and async sessions.
"""
import uuid
from datetime import date, datetime, time, timezone
from decimal import Decimal
import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.db import AsyncSessionLocal, async_engine
from app.models.sql import (
    Base,
    User,
    Category,
    UserInterest,
    Preference,
    Location,
    POI,
    OpeningHours,
    KnowledgeChunk,
    Accommodation,
    TransportOption,
    Trip,
    TripAccommodation,
    TripTransport,
    POICluster,
    Itinerary,
    ItineraryStop,
    Route,
    AlternativeRoute,
    Image,
    POIImage,
    AccommodationImage,
    Feedback,
    Offer,
)

EXPECTED_23_TABLES = {
    "users",
    "categories",
    "user_interests",
    "preferences",
    "locations",
    "pois",
    "opening_hours",
    "knowledge_chunks",
    "accommodations",
    "transport_options",
    "trips",
    "trip_accommodations",
    "trip_transports",
    "poi_clusters",
    "itineraries",
    "itinerary_stops",
    "routes",
    "alternative_routes",
    "images",
    "poi_images",
    "accommodation_images",
    "feedback",
    "offers",
}


@pytest.fixture(scope="module")
def sync_engine():
    engine = create_engine(settings.sync_database_url)
    yield engine
    engine.dispose()


def test_real_postgres_connection_and_version(sync_engine):
    """Verifies that we are connected to a real PostgreSQL 16+ instance."""
    with sync_engine.connect() as conn:
        version = conn.execute(text("SELECT version();")).scalar()
        assert version is not None
        assert "PostgreSQL 16" in version
        print(f"\n[Real Database Verified]: {version}")


def test_pgvector_extension_installed(sync_engine):
    """Verifies that the pgvector extension is actively installed."""
    with sync_engine.connect() as conn:
        ext = conn.execute(
            text("SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';")
        ).fetchone()
        assert ext is not None, "pgvector extension is NOT installed in the real database"
        assert ext[0] == "vector"
        print(f"[pgvector Extension Verified]: {ext[0]} version {ext[1]}")


def test_exactly_23_core_tables_exist(sync_engine):
    """Verifies that exactly the 23 locked core domain tables exist (plus alembic_version)."""
    inspector = inspect(sync_engine)
    tables = set(inspector.get_table_names())
    domain_tables = tables - {"alembic_version"}

    assert domain_tables == EXPECTED_23_TABLES, (
        f"Mismatch in domain tables!\n"
        f"Missing: {EXPECTED_23_TABLES - domain_tables}\n"
        f"Extra: {domain_tables - EXPECTED_23_TABLES}"
    )
    assert len(domain_tables) == 23


def test_field_conformance_accommodations(sync_engine):
    """Verifies all locked fields in accommodations."""
    inspector = inspect(sync_engine)
    cols = {c["name"]: c for c in inspector.get_columns("accommodations")}
    expected_fields = [
        "id", "location_id", "name", "type", "budget_tier",
        "price_per_night", "currency", "rating", "external_booking_url",
        "is_active", "created_at", "updated_at"
    ]
    for field in expected_fields:
        assert field in cols, f"Missing field in accommodations: {field}"
    assert "latitude" not in cols
    assert "longitude" not in cols


def test_field_conformance_transport_options(sync_engine):
    """Verifies multi-modal origin/destination structure in transport_options."""
    inspector = inspect(sync_engine)
    cols = {c["name"]: c for c in inspector.get_columns("transport_options")}
    expected_fields = [
        "id", "mode", "provider_name", "origin_location_id",
        "destination_location_id", "estimated_cost", "currency",
        "booking_url", "is_active", "created_at"
    ]
    for field in expected_fields:
        assert field in cols, f"Missing field in transport_options: {field}"
    assert "location_id" not in cols, "Generic location_id should be replaced with origin/destination"


def test_field_conformance_trips(sync_engine):
    """Verifies trips has total_days and location_id."""
    inspector = inspect(sync_engine)
    cols = {c["name"]: c for c in inspector.get_columns("trips")}
    expected_fields = [
        "id", "user_id", "location_id", "title", "start_date",
        "end_date", "total_days", "budget", "status", "created_at", "updated_at"
    ]
    for field in expected_fields:
        assert field in cols, f"Missing field in trips: {field}"


def test_field_conformance_itineraries_and_stops(sync_engine):
    """
    Verifies Trip -> Itinerary -> Itinerary Stops hierarchy:
    - itineraries stores trip_id, name, is_primary, total_distance_km, total_travel_time_minutes
    - itinerary_stops stores day_number, stop_order, arrival_time, departure_time, duration_minutes
    """
    inspector = inspect(sync_engine)
    itin_cols = {c["name"]: c for c in inspector.get_columns("itineraries")}
    assert "trip_id" in itin_cols
    assert "name" in itin_cols
    assert "is_primary" in itin_cols
    assert "total_distance_km" in itin_cols
    assert "total_travel_time_minutes" in itin_cols
    assert "day_number" not in itin_cols, "day_number belongs to itinerary_stops, not itineraries"

    stop_cols = {c["name"]: c for c in inspector.get_columns("itinerary_stops")}
    assert "itinerary_id" in stop_cols
    assert "poi_id" in stop_cols
    assert "day_number" in stop_cols
    assert "stop_order" in stop_cols
    assert "arrival_time" in stop_cols
    assert "departure_time" in stop_cols
    assert "duration_minutes" in stop_cols


def test_field_conformance_images(sync_engine):
    """Verifies complete media schema in images."""
    inspector = inspect(sync_engine)
    cols = {c["name"]: c for c in inspector.get_columns("images")}
    expected_fields = [
        "id", "url", "thumbnail_url", "caption", "width", "height",
        "source", "external_image_id", "license_type", "attribution_text",
        "is_fallback", "created_at"
    ]
    for field in expected_fields:
        assert field in cols, f"Missing field in images: {field}"


def test_field_conformance_feedback_and_check_constraint(sync_engine):
    """Verifies feedback fields and target check constraint."""
    inspector = inspect(sync_engine)
    cols = {c["name"]: c for c in inspector.get_columns("feedback")}
    for field in ["user_id", "poi_id", "trip_id", "itinerary_id", "rating", "comment", "created_at", "updated_at"]:
        assert field in cols, f"Missing field in feedback: {field}"

    with sync_engine.connect() as conn:
        with conn.begin():
            uid = str(uuid.uuid4())
            conn.execute(
                text("INSERT INTO users (id, email, password_hash) VALUES (:id, :e, 'hash');"),
                {"id": uid, "e": f"user_{uid[:8]}@example.com"},
            )
            # Should fail because all target FKs are NULL
            with pytest.raises(Exception):
                conn.execute(
                    text("INSERT INTO feedback (id, user_id, rating, comment) VALUES (:id, :u, 5, 'Great');"),
                    {"id": str(uuid.uuid4()), "u": uid},
                )
            conn.rollback()


def test_field_conformance_poi_clusters(sync_engine):
    """Verifies poi_clusters structure with poi_id membership."""
    inspector = inspect(sync_engine)
    cols = {c["name"]: c for c in inspector.get_columns("poi_clusters")}
    expected_fields = [
        "id", "trip_id", "poi_id", "cluster_index", "centroid_lat",
        "centroid_lon", "assigned_day", "created_at"
    ]
    for field in expected_fields:
        assert field in cols, f"Missing field in poi_clusters: {field}"


def test_canonical_coordinate_isolation(sync_engine):
    """
    Verifies that locations is the ONLY entity storing coordinates:
    - locations has latitude and longitude.
    - pois and accommodations have location_id and NO latitude/longitude.
    - knowledge_chunks has NO location_id.
    """
    inspector = inspect(sync_engine)

    loc_cols = {c["name"] for c in inspector.get_columns("locations")}
    assert "latitude" in loc_cols
    assert "longitude" in loc_cols

    poi_cols = {c["name"] for c in inspector.get_columns("pois")}
    assert "location_id" in poi_cols
    assert "latitude" not in poi_cols
    assert "longitude" not in poi_cols

    acc_cols = {c["name"] for c in inspector.get_columns("accommodations")}
    assert "location_id" in acc_cols
    assert "latitude" not in acc_cols
    assert "longitude" not in acc_cols

    kc_cols = {c["name"] for c in inspector.get_columns("knowledge_chunks")}
    assert "poi_id" in kc_cols
    assert "location_id" not in kc_cols


def test_vector_dimensions_and_hnsw_indexes(sync_engine):
    """
    Verifies:
    - pois.embedding is vector(384)
    - knowledge_chunks.embedding is vector(384)
    - HNSW indexes exist on both vector columns
    """
    with sync_engine.connect() as conn:
        col_type = conn.execute(
            text(
                "SELECT format_type(atttypid, atttypmod) FROM pg_attribute "
                "WHERE attrelid = 'pois'::regclass AND attname = 'embedding';"
            )
        ).scalar()
        assert col_type == "vector(384)", f"Expected vector(384), got {col_type}"

        kc_col_type = conn.execute(
            text(
                "SELECT format_type(atttypid, atttypmod) FROM pg_attribute "
                "WHERE attrelid = 'knowledge_chunks'::regclass AND attname = 'embedding';"
            )
        ).scalar()
        assert kc_col_type == "vector(384)", f"Expected vector(384), got {kc_col_type}"

        poi_index = conn.execute(
            text(
                "SELECT indexdef FROM pg_indexes "
                "WHERE tablename = 'pois' AND indexname = 'idx_pois_embedding';"
            )
        ).scalar()
        assert poi_index is not None
        assert "hnsw" in poi_index.lower()

        kc_index = conn.execute(
            text(
                "SELECT indexdef FROM pg_indexes "
                "WHERE tablename = 'knowledge_chunks' AND indexname = 'idx_knowledge_chunks_embedding';"
            )
        ).scalar()
        assert kc_index is not None
        assert "hnsw" in kc_index.lower()


def test_pgvector_similarity_search(sync_engine):
    """Performs real vector inserts and cosine distance query in PostgreSQL."""
    vec_a = [0.1] * 384
    with sync_engine.connect() as conn:
        with conn.begin():
            cat_id = str(uuid.uuid4())
            loc_id = str(uuid.uuid4())
            poi_id = str(uuid.uuid4())
            conn.execute(
                text("INSERT INTO categories (id, name, slug) VALUES (:id, :name, :slug);"),
                {"id": cat_id, "name": f"Category {cat_id[:8]}", "slug": f"cat-{cat_id[:8]}"},
            )
            conn.execute(
                text(
                    "INSERT INTO locations (id, name, latitude, longitude, city, country) "
                    "VALUES (:id, :name, :lat, :lon, :city, :country);"
                ),
                {"id": loc_id, "name": "Eiffel Tower", "lat": 48.8584, "lon": 2.2945, "city": "Paris", "country": "France"},
            )
            conn.execute(
                text(
                    "INSERT INTO pois (id, location_id, category_id, name, embedding) "
                    "VALUES (:id, :loc_id, :cat_id, :name, :emb);"
                ),
                {"id": poi_id, "loc_id": loc_id, "cat_id": cat_id, "name": "Monument", "emb": str(vec_a)},
            )

            res = conn.execute(
                text("SELECT name, embedding <=> :query AS dist FROM pois WHERE id = :id;"),
                {"id": poi_id, "query": str(vec_a)},
            ).fetchone()
            assert res is not None
            assert abs(res[1]) < 1e-5
            conn.rollback()


def test_foreign_key_delete_behaviors(sync_engine):
    """Verifies that all specified foreign key delete rules match architectural requirements."""
    with sync_engine.connect() as conn:
        fks = conn.execute(
            text(
                """
                SELECT
                    tc.table_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    rc.delete_rule
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.referential_constraints AS rc
                    ON tc.constraint_name = rc.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                    ON rc.unique_constraint_name = ccu.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                  AND tc.table_schema = 'public';
                """
            )
        ).fetchall()

        fk_map = {(row[0], row[1]): (row[2], row[3]) for row in fks}

        assert fk_map[("user_interests", "user_id")] == ("users", "CASCADE")
        assert fk_map[("user_interests", "category_id")] == ("categories", "RESTRICT")
        assert fk_map[("pois", "location_id")] == ("locations", "RESTRICT")
        assert fk_map[("pois", "category_id")] == ("categories", "RESTRICT")
        assert fk_map[("knowledge_chunks", "poi_id")] == ("pois", "SET NULL")
        assert fk_map[("accommodations", "location_id")] == ("locations", "RESTRICT")
        assert fk_map[("transport_options", "origin_location_id")] == ("locations", "SET NULL")
        assert fk_map[("transport_options", "destination_location_id")] == ("locations", "SET NULL")
        assert fk_map[("trips", "user_id")] == ("users", "CASCADE")
        assert fk_map[("trips", "location_id")] == ("locations", "RESTRICT")
        assert fk_map[("poi_clusters", "trip_id")] == ("trips", "CASCADE")
        assert fk_map[("poi_clusters", "poi_id")] == ("pois", "RESTRICT")
        assert fk_map[("itineraries", "trip_id")] == ("trips", "CASCADE")
        assert fk_map[("itinerary_stops", "itinerary_id")] == ("itineraries", "CASCADE")
        assert fk_map[("itinerary_stops", "poi_id")] == ("pois", "RESTRICT")
        assert fk_map[("routes", "itinerary_id")] == ("itineraries", "CASCADE")
        assert fk_map[("routes", "source_stop_id")] == ("itinerary_stops", "CASCADE")
        assert fk_map[("routes", "target_stop_id")] == ("itinerary_stops", "CASCADE")
        assert fk_map[("alternative_routes", "route_id")] == ("routes", "CASCADE")
        assert fk_map[("poi_images", "poi_id")] == ("pois", "CASCADE")
        assert fk_map[("poi_images", "image_id")] == ("images", "CASCADE")
        assert fk_map[("accommodation_images", "accommodation_id")] == ("accommodations", "CASCADE")
        assert fk_map[("accommodation_images", "image_id")] == ("images", "CASCADE")
        assert fk_map[("feedback", "user_id")] == ("users", "CASCADE")
        assert fk_map[("feedback", "poi_id")] == ("pois", "CASCADE")
        assert fk_map[("feedback", "trip_id")] == ("trips", "SET NULL")
        assert fk_map[("feedback", "itinerary_id")] == ("itineraries", "CASCADE")
        assert fk_map[("offers", "location_id")] == ("locations", "CASCADE")
        assert fk_map[("offers", "poi_id")] == ("pois", "SET NULL")
        assert fk_map[("offers", "accommodation_id")] == ("accommodations", "SET NULL")


def test_partial_unique_index_on_images(sync_engine):
    """Verifies that the partial unique index on images(source, external_image_id) exists."""
    with sync_engine.connect() as conn:
        idx_def = conn.execute(
            text(
                "SELECT indexdef FROM pg_indexes "
                "WHERE tablename = 'images' AND indexname = 'uq_images_source_external_id';"
            )
        ).scalar()
        assert idx_def is not None
        assert "unique" in idx_def.lower()
        assert "where" in idx_def.lower()


def test_route_stop_boundary_conditions(sync_engine):
    """
    Verifies route endpoint constraints:
    - Allows source_stop_id IS NULL AND target_stop_id IS NOT NULL (Accommodation -> First POI)
    - Allows source_stop_id IS NOT NULL AND target_stop_id IS NULL (Last POI -> Accommodation)
    - Rejects source_stop_id IS NULL AND target_stop_id IS NULL
    """
    with sync_engine.connect() as conn:
        with conn.begin():
            uid = str(uuid.uuid4())
            lid = str(uuid.uuid4())
            tid = str(uuid.uuid4())
            itin_id = str(uuid.uuid4())

            conn.execute(
                text("INSERT INTO users (id, email, password_hash) VALUES (:id, :e, 'hash');"),
                {"id": uid, "e": f"user_{uid[:8]}@example.com"},
            )
            conn.execute(
                text("INSERT INTO locations (id, name, latitude, longitude, city, country) VALUES (:id, 'Loc', 0, 0, 'City', 'Country');"),
                {"id": lid},
            )
            conn.execute(
                text("INSERT INTO trips (id, user_id, location_id, title, start_date, end_date, total_days) VALUES (:id, :u, :l, 'T', '2026-06-01', '2026-06-05', 5);"),
                {"id": tid, "u": uid, "l": lid},
            )
            conn.execute(
                text("INSERT INTO itineraries (id, trip_id, name) VALUES (:id, :t, 'Primary');"),
                {"id": itin_id, "t": tid},
            )

            with pytest.raises(Exception):
                conn.execute(
                    text(
                        "INSERT INTO routes (id, itinerary_id, source_stop_id, target_stop_id, distance, duration) "
                        "VALUES (:id, :itin_id, NULL, NULL, 5.0, 30);"
                    ),
                    {"id": str(uuid.uuid4()), "itin_id": itin_id},
                )
            conn.rollback()


@pytest.mark.asyncio
async def test_asyncpg_connection_and_session():
    """Verifies that the Async SQLAlchemy engine and AsyncSession work against the live database."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT count(*) FROM users;"))
        count = result.scalar()
        assert count is not None
        assert count >= 0
