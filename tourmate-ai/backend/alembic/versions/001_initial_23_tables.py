"""Initial migration: establishes PostgreSQL + pgvector foundation across 23 core domain tables.
Strictly conforms to the locked 23-table architecture and field specifications.

Revision ID: 001_initial_23_tables
Revises: 
Create Date: 2026-09-19 12:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = "001_initial_23_tables"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 0. Ensure pgvector extension exists
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # 1. users
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("name", sa.String(128), server_default="", nullable=False),
        sa.Column("role", sa.String(32), server_default="user", nullable=False),
        sa.Column("preferred_language", sa.String(10), server_default="en", nullable=False),
        sa.Column("token_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("length(email) >= 5", name="ck_users_email_length"),
    )
    op.create_index("idx_users_email", "users", ["email"])

    # 2. categories
    op.create_table(
        "categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(64), nullable=False, unique=True),
        sa.Column("slug", sa.String(64), nullable=False, unique=True),
        sa.Column("icon", sa.String(64), server_default="MapPin", nullable=False),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_categories_slug", "categories", ["slug"])

    # 3. user_interests
    op.create_table(
        "user_interests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("weight", sa.Float(), server_default="1.0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "category_id", name="uq_user_interests_user_category"),
        sa.CheckConstraint("weight >= 0.0 AND weight <= 5.0", name="ck_user_interests_weight_range"),
    )
    op.create_index("idx_user_interests_user_id", "user_interests", ["user_id"])
    op.create_index("idx_user_interests_category_id", "user_interests", ["category_id"])

    # 4. preferences
    op.create_table(
        "preferences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("budget_tier", sa.String(32), server_default="moderate", nullable=False),
        sa.Column("travel_style", sa.String(64), server_default="balanced", nullable=False),
        sa.Column("daily_start_time", sa.Time(), server_default="09:00:00", nullable=False),
        sa.Column("daily_end_time", sa.Time(), server_default="20:00:00", nullable=False),
        sa.Column("max_walking_distance_km", sa.Float(), server_default="5.0", nullable=False),
        sa.Column("preferred_transport_mode", sa.String(32), server_default="car", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_preferences_user_id", "preferences", ["user_id"])

    # 5. locations (canonical physical geographic information entity)
    op.create_table(
        "locations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("address", sa.String(255), server_default="", nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("city", sa.String(128), nullable=False),
        sa.Column("state", sa.String(128), server_default="", nullable=False),
        sa.Column("country", sa.String(128), nullable=False),
        sa.Column("postal_code", sa.String(32), server_default="", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("latitude >= -90.0 AND latitude <= 90.0", name="ck_locations_latitude_range"),
        sa.CheckConstraint("longitude >= -180.0 AND longitude <= 180.0", name="ck_locations_longitude_range"),
    )
    op.create_index("idx_locations_name", "locations", ["name"])
    op.create_index("idx_locations_city", "locations", ["city"])
    op.create_index("idx_locations_country", "locations", ["country"])
    op.create_index("idx_locations_lat_lon", "locations", ["latitude", "longitude"])

    # 6. pois
    op.create_table(
        "pois",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("locations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), server_default="", nullable=False),
        sa.Column("rating", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("price_tier", sa.Integer(), server_default="1", nullable=False),
        sa.Column("typical_visit_duration_minutes", sa.Integer(), server_default="90", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("embedding", Vector(384), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("rating >= 0.0 AND rating <= 5.0", name="ck_pois_rating_range"),
        sa.CheckConstraint("price_tier BETWEEN 1 AND 4", name="ck_pois_price_tier_range"),
        sa.CheckConstraint("typical_visit_duration_minutes > 0", name="ck_pois_visit_duration_positive"),
    )
    op.create_index("idx_pois_location_id", "pois", ["location_id"])
    op.create_index("idx_pois_category_id", "pois", ["category_id"])
    op.create_index("idx_pois_name", "pois", ["name"])
    op.execute("CREATE INDEX idx_pois_embedding ON pois USING hnsw (embedding vector_cosine_ops);")

    # 7. opening_hours
    op.create_table(
        "opening_hours",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("poi_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("pois.id", ondelete="CASCADE"), nullable=False),
        sa.Column("day_of_week", sa.Integer(), nullable=False),
        sa.Column("open_time", sa.Time(), nullable=False),
        sa.Column("close_time", sa.Time(), nullable=False),
        sa.Column("is_closed", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("poi_id", "day_of_week", name="uq_opening_hours_poi_day"),
        sa.CheckConstraint("day_of_week >= 0 AND day_of_week <= 6", name="ck_opening_hours_day_of_week"),
    )
    op.create_index("idx_opening_hours_poi_id", "opening_hours", ["poi_id"])

    # 8. knowledge_chunks (RAG: no location ownership)
    op.create_table(
        "knowledge_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("poi_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("pois.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(384), nullable=False),
        sa.Column("source", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_knowledge_chunks_poi_id", "knowledge_chunks", ["poi_id"])
    op.create_index("idx_knowledge_chunks_title", "knowledge_chunks", ["title"])
    op.execute("CREATE INDEX idx_knowledge_chunks_embedding ON knowledge_chunks USING hnsw (embedding vector_cosine_ops);")

    # 9. accommodations (daily route anchor lodging)
    op.create_table(
        "accommodations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("locations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("type", sa.String(32), server_default="hotel", nullable=False),
        sa.Column("budget_tier", sa.String(32), server_default="moderate", nullable=False),
        sa.Column("price_per_night", sa.Numeric(10, 2), server_default="0.00", nullable=False),
        sa.Column("currency", sa.String(3), server_default="INR", nullable=False),
        sa.Column("rating", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("external_booking_url", sa.String(1024), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("type IN ('hotel', 'hostel', 'dorm', 'guesthouse', 'resort')", name="ck_accommodations_type"),
        sa.CheckConstraint("budget_tier IN ('budget', 'moderate', 'luxury')", name="ck_accommodations_budget_tier"),
    )
    op.create_index("idx_accommodations_location_id", "accommodations", ["location_id"])
    op.create_index("idx_accommodations_tier", "accommodations", ["budget_tier"])
    op.create_index("idx_accommodations_name", "accommodations", ["name"])

    # 10. transport_options (multi-modal catalog)
    op.create_table(
        "transport_options",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("mode", sa.String(32), nullable=False),
        sa.Column("provider_name", sa.String(128), server_default="", nullable=False),
        sa.Column("origin_location_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("locations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("destination_location_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("locations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("estimated_cost", sa.Numeric(10, 2), nullable=True),
        sa.Column("currency", sa.String(3), server_default="INR", nullable=False),
        sa.Column("booking_url", sa.String(1024), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_transport_options_mode", "transport_options", ["mode"])
    op.create_index("idx_transport_options_origin", "transport_options", ["origin_location_id"])
    op.create_index("idx_transport_options_dest", "transport_options", ["destination_location_id"])

    # 11. trips
    op.create_table(
        "trips",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("locations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("total_days", sa.Integer(), server_default="1", nullable=False),
        sa.Column("budget", sa.Numeric(10, 2), nullable=True),
        sa.Column("status", sa.String(32), server_default="planning", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("end_date >= start_date", name="ck_trips_date_range"),
        sa.CheckConstraint("total_days >= 1 AND total_days <= 30", name="ck_trips_total_days_range"),
    )
    op.create_index("idx_trips_user_id", "trips", ["user_id"])
    op.create_index("idx_trips_location_id", "trips", ["location_id"])

    # 12. trip_accommodations
    op.create_table(
        "trip_accommodations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("trip_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("trips.id", ondelete="CASCADE"), nullable=False),
        sa.Column("accommodation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("accommodations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("check_in_date", sa.Date(), nullable=False),
        sa.Column("check_out_date", sa.Date(), nullable=False),
        sa.Column("is_confirmed", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("check_out_date >= check_in_date", name="ck_trip_acc_date_range"),
    )
    op.create_index("idx_trip_accommodations_trip_id", "trip_accommodations", ["trip_id"])
    op.create_index("idx_trip_accommodations_acc_id", "trip_accommodations", ["accommodation_id"])

    # 13. trip_transports
    op.create_table(
        "trip_transports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("trip_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("trips.id", ondelete="CASCADE"), nullable=False),
        sa.Column("transport_option_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("transport_options.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("departure_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("arrival_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("booking_reference", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_trip_transports_trip_id", "trip_transports", ["trip_id"])
    op.create_index("idx_trip_transports_opt_id", "trip_transports", ["transport_option_id"])

    # 14. poi_clusters
    op.create_table(
        "poi_clusters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("trip_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("trips.id", ondelete="CASCADE"), nullable=False),
        sa.Column("poi_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("pois.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("cluster_index", sa.Integer(), nullable=False),
        sa.Column("centroid_lat", sa.Float(), nullable=False),
        sa.Column("centroid_lon", sa.Float(), nullable=False),
        sa.Column("assigned_day", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("trip_id", "poi_id", name="uq_poi_clusters_trip_poi"),
    )
    op.create_index("idx_poi_clusters_trip_id", "poi_clusters", ["trip_id"])
    op.create_index("idx_poi_clusters_poi_id", "poi_clusters", ["poi_id"])

    # 15. itineraries (Trip -> Itinerary plan container)
    op.create_table(
        "itineraries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("trip_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("trips.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(128), server_default="Primary Plan", nullable=False),
        sa.Column("is_primary", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("total_distance_km", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("total_travel_time_minutes", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_itineraries_trip_id", "itineraries", ["trip_id"])

    # 16. itinerary_stops (Sequential sightseeing stops with day_number)
    op.create_table(
        "itinerary_stops",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("itinerary_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("itineraries.id", ondelete="CASCADE"), nullable=False),
        sa.Column("poi_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("pois.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("day_number", sa.Integer(), server_default="1", nullable=False),
        sa.Column("stop_order", sa.Integer(), nullable=False),
        sa.Column("arrival_time", sa.Time(), server_default="09:00:00", nullable=False),
        sa.Column("departure_time", sa.Time(), server_default="10:30:00", nullable=False),
        sa.Column("duration_minutes", sa.Integer(), server_default="90", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("itinerary_id", "day_number", "stop_order", name="uq_itinerary_stops_seq"),
        sa.CheckConstraint("duration_minutes > 0", name="ck_itinerary_stops_duration_positive"),
    )
    op.create_index("idx_itinerary_stops_seq", "itinerary_stops", ["itinerary_id", "day_number", "stop_order"])
    op.create_index("idx_itinerary_stops_poi_id", "itinerary_stops", ["poi_id"])

    # 17. routes (source_stop_id and target_stop_id nullable for boundary accommodation hops)
    op.create_table(
        "routes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("itinerary_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("itineraries.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_stop_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("itinerary_stops.id", ondelete="CASCADE"), nullable=True),
        sa.Column("target_stop_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("itinerary_stops.id", ondelete="CASCADE"), nullable=True),
        sa.Column("distance", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("duration", sa.Integer(), server_default="0", nullable=False),
        sa.Column("polyline", sa.Text(), nullable=True),
        sa.Column("geometry", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("mode", sa.String(32), server_default="driving", nullable=False),
        sa.Column("is_mock", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("source_stop_id IS NOT NULL OR target_stop_id IS NOT NULL", name="ck_routes_source_or_target_not_null"),
    )
    op.create_index("idx_routes_itinerary_id", "routes", ["itinerary_id"])
    op.create_index("idx_routes_source_stop_id", "routes", ["source_stop_id"])
    op.create_index("idx_routes_target_stop_id", "routes", ["target_stop_id"])

    # 18. alternative_routes
    op.create_table(
        "alternative_routes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("route_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("routes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("distance", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("duration", sa.Integer(), server_default="0", nullable=False),
        sa.Column("polyline", sa.Text(), nullable=True),
        sa.Column("geometry", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_alternative_routes_route_id", "alternative_routes", ["route_id"])

    # 19. images (complete media catalog)
    op.create_table(
        "images",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("url", sa.String(1024), nullable=False),
        sa.Column("thumbnail_url", sa.String(1024), nullable=True),
        sa.Column("caption", sa.String(255), nullable=True),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("source", sa.String(100), nullable=True),
        sa.Column("external_image_id", sa.String(255), nullable=True),
        sa.Column("license_type", sa.String(64), nullable=True),
        sa.Column("attribution_text", sa.String(255), nullable=True),
        sa.Column("is_fallback", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_images_source_external_id ON images (source, external_image_id) "
        "WHERE source IS NOT NULL AND external_image_id IS NOT NULL;"
    )

    # 20. poi_images
    op.create_table(
        "poi_images",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("poi_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("pois.id", ondelete="CASCADE"), nullable=False),
        sa.Column("image_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("images.id", ondelete="CASCADE"), nullable=False),
        sa.Column("is_primary", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("display_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("poi_id", "image_id", name="uq_poi_images_poi_image"),
    )
    op.create_index("idx_poi_images_poi_id", "poi_images", ["poi_id"])
    op.create_index("idx_poi_images_image_id", "poi_images", ["image_id"])

    # 21. accommodation_images
    op.create_table(
        "accommodation_images",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("accommodation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("accommodations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("image_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("images.id", ondelete="CASCADE"), nullable=False),
        sa.Column("is_primary", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("display_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("accommodation_id", "image_id", name="uq_accommodation_images_acc_image"),
    )
    op.create_index("idx_acc_images_acc_id", "accommodation_images", ["accommodation_id"])
    op.create_index("idx_acc_images_img_id", "accommodation_images", ["image_id"])

    # 22. feedback
    op.create_table(
        "feedback",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("poi_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("pois.id", ondelete="CASCADE"), nullable=True),
        sa.Column("trip_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("trips.id", ondelete="SET NULL"), nullable=True),
        sa.Column("itinerary_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("itineraries.id", ondelete="CASCADE"), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), server_default="", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("rating >= 1 AND rating <= 5", name="ck_feedback_rating_range"),
        sa.CheckConstraint("trip_id IS NOT NULL OR poi_id IS NOT NULL OR itinerary_id IS NOT NULL", name="ck_feedback_target_not_null"),
    )
    op.create_index("idx_feedback_user_id", "feedback", ["user_id"])
    op.create_index("idx_feedback_poi_id", "feedback", ["poi_id"])
    op.create_index("idx_feedback_trip_id", "feedback", ["trip_id"])
    op.create_index("idx_feedback_itinerary_id", "feedback", ["itinerary_id"])

    # 23. offers
    op.create_table(
        "offers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("locations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("poi_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("pois.id", ondelete="SET NULL"), nullable=True),
        sa.Column("accommodation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("accommodations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), server_default="", nullable=False),
        sa.Column("discount_percentage", sa.Numeric(5, 2), nullable=True),
        sa.Column("promo_code", sa.String(64), nullable=True),
        sa.Column("affiliate_url", sa.String(1024), nullable=True),
        sa.Column("valid_from", sa.Date(), nullable=False),
        sa.Column("valid_until", sa.Date(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("valid_until >= valid_from", name="ck_offers_validity_window"),
    )
    op.create_index("idx_offers_location_id", "offers", ["location_id"])
    op.create_index("idx_offers_poi_id", "offers", ["poi_id"])
    op.create_index("idx_offers_accommodation_id", "offers", ["accommodation_id"])


def downgrade() -> None:
    # Drop in reverse topological order
    op.drop_table("offers")
    op.drop_table("feedback")
    op.drop_table("accommodation_images")
    op.drop_table("poi_images")
    op.drop_table("images")
    op.drop_table("alternative_routes")
    op.drop_table("routes")
    op.drop_table("itinerary_stops")
    op.drop_table("itineraries")
    op.drop_table("poi_clusters")
    op.drop_table("trip_transports")
    op.drop_table("trip_accommodations")
    op.drop_table("trips")
    op.drop_table("transport_options")
    op.drop_table("accommodations")
    op.drop_table("knowledge_chunks")
    op.drop_table("opening_hours")
    op.drop_table("pois")
    op.drop_table("locations")
    op.drop_table("preferences")
    op.drop_table("user_interests")
    op.drop_table("categories")
    op.drop_table("users")
    op.execute("DROP EXTENSION IF EXISTS vector CASCADE;")
