"""
Deterministic and idempotent seeder for Phase 2 Geographic & POI Foundation.
Can be executed via Alembic migration (sync connection) or directly via CLI.
"""
import asyncio
import sys
import uuid
from datetime import time
from sqlalchemy import text, Table, MetaData
from sqlalchemy.dialects.postgresql import insert
from app.db.seeds.canonical_seed_data import PILOT_POIS, PILOT_ACCOMMODATIONS


def seed_geographic_foundation(conn):
    """
    Seeds canonical locations, POIs, opening hours, accommodations, and media.
    Idempotent using ON CONFLICT DO NOTHING.
    Works with synchronous SQLAlchemy connection (such as during Alembic migration).
    """
    # 1. Fetch category map
    cat_rows = conn.execute(text("SELECT id, name FROM categories;")).fetchall()
    cat_map = {row[1]: row[0] for row in cat_rows}

    for required_cat in ["History", "Nature", "Culture", "Adventure", "Food", "Shopping", "Architecture"]:
        if required_cat not in cat_map:
            raise ValueError(f"Required canonical category '{required_cat}' is not seeded in PostgreSQL.")

    # 2. Ingest POIs
    for poi in PILOT_POIS:
        loc = poi["location"]
        # Insert location
        conn.execute(
            text("""
                INSERT INTO locations (id, name, address, latitude, longitude, city, state, country, postal_code)
                VALUES (:id, :name, :address, :lat, :lon, :city, :state, :country, :postal_code)
                ON CONFLICT (id) DO NOTHING;
            """),
            {
                "id": loc["id"],
                "name": loc["name"],
                "address": loc["address"],
                "lat": loc["latitude"],
                "lon": loc["longitude"],
                "city": loc["city"],
                "state": loc["state"],
                "country": loc["country"],
                "postal_code": loc["postal_code"],
            },
        )

        cat_id = cat_map[poi["category_name"]]
        # Insert POI
        conn.execute(
            text("""
                INSERT INTO pois (
                    id, location_id, category_id, name, description, rating,
                    price_tier, typical_visit_duration_minutes, is_active, embedding
                )
                VALUES (
                    :id, :loc_id, :cat_id, :name, :desc, :rating,
                    :price_tier, :dur, :active, :emb
                )
                ON CONFLICT (id) DO NOTHING;
            """),
            {
                "id": poi["id"],
                "loc_id": poi["location_id"],
                "cat_id": str(cat_id),
                "name": poi["name"],
                "desc": poi["description"],
                "rating": poi["rating"],
                "price_tier": poi["price_tier"],
                "dur": poi["typical_visit_duration_minutes"],
                "active": poi["is_active"],
                "emb": str(poi["embedding"]),
            },
        )

        # Insert images and poi_images
        for idx, img in enumerate(poi.get("images", [])):
            conn.execute(
                text("""
                    INSERT INTO images (
                        id, url, thumbnail_url, caption, source,
                        external_image_id, license_type, attribution_text, is_fallback
                    )
                    VALUES (
                        :id, :url, :thumb, :caption, :source,
                        :ext_id, :license, :attr, false
                    )
                    ON CONFLICT (id) DO NOTHING;
                """),
                {
                    "id": img["id"],
                    "url": img["url"],
                    "thumb": img.get("thumbnail_url"),
                    "caption": img.get("caption"),
                    "source": img.get("source"),
                    "ext_id": img.get("external_image_id"),
                    "license": img.get("license_type"),
                    "attr": img.get("attribution_text"),
                },
            )

            conn.execute(
                text("""
                    INSERT INTO poi_images (id, poi_id, image_id, is_primary, display_order)
                    VALUES (:id, :poi_id, :img_id, :primary, :order)
                    ON CONFLICT (poi_id, image_id) DO NOTHING;
                """),
                {
                    "id": str(uuid.uuid5(uuid.UUID(poi["id"]), img["id"])),
                    "poi_id": poi["id"],
                    "img_id": img["id"],
                    "primary": img.get("is_primary", True),
                    "order": idx,
                },
            )

        # Insert opening hours
        for oh in poi.get("opening_hours", []):
            oh_id = str(uuid.uuid5(uuid.UUID(poi["id"]), f"day_{oh['day_of_week']}"))
            conn.execute(
                text("""
                    INSERT INTO opening_hours (id, poi_id, day_of_week, open_time, close_time, is_closed)
                    VALUES (:id, :poi_id, :dow, :open_t, :close_t, :closed)
                    ON CONFLICT (poi_id, day_of_week) DO NOTHING;
                """),
                {
                    "id": oh_id,
                    "poi_id": poi["id"],
                    "dow": oh["day_of_week"],
                    "open_t": oh["open_time"],
                    "close_t": oh["close_time"],
                    "closed": oh["is_closed"],
                },
            )

    # 3. Ingest Accommodations
    for acc in PILOT_ACCOMMODATIONS:
        loc = acc["location"]
        # Insert location
        conn.execute(
            text("""
                INSERT INTO locations (id, name, address, latitude, longitude, city, state, country, postal_code)
                VALUES (:id, :name, :address, :lat, :lon, :city, :state, :country, :postal_code)
                ON CONFLICT (id) DO NOTHING;
            """),
            {
                "id": loc["id"],
                "name": loc["name"],
                "address": loc["address"],
                "lat": loc["latitude"],
                "lon": loc["longitude"],
                "city": loc["city"],
                "state": loc["state"],
                "country": loc["country"],
                "postal_code": loc["postal_code"],
            },
        )

        # Insert accommodation
        conn.execute(
            text("""
                INSERT INTO accommodations (
                    id, location_id, name, type, budget_tier,
                    price_per_night, currency, rating, external_booking_url, is_active
                )
                VALUES (
                    :id, :loc_id, :name, :type, :tier,
                    :price, :currency, :rating, :url, :active
                )
                ON CONFLICT (id) DO NOTHING;
            """),
            {
                "id": acc["id"],
                "loc_id": acc["location_id"],
                "name": acc["name"],
                "type": acc["type"],
                "tier": acc["budget_tier"],
                "price": acc["price_per_night"],
                "currency": acc["currency"],
                "rating": acc["rating"],
                "url": acc.get("external_booking_url"),
                "active": acc["is_active"],
            },
        )

        # Insert images and accommodation_images
        for idx, img in enumerate(acc.get("images", [])):
            conn.execute(
                text("""
                    INSERT INTO images (
                        id, url, thumbnail_url, caption, source,
                        external_image_id, license_type, attribution_text, is_fallback
                    )
                    VALUES (
                        :id, :url, :thumb, :caption, :source,
                        :ext_id, :license, :attr, false
                    )
                    ON CONFLICT (id) DO NOTHING;
                """),
                {
                    "id": img["id"],
                    "url": img["url"],
                    "thumb": img.get("thumbnail_url"),
                    "caption": img.get("caption"),
                    "source": img.get("source"),
                    "ext_id": img.get("external_image_id"),
                    "license": img.get("license_type"),
                    "attr": img.get("attribution_text"),
                },
            )

            conn.execute(
                text("""
                    INSERT INTO accommodation_images (id, accommodation_id, image_id, is_primary, display_order)
                    VALUES (:id, :acc_id, :img_id, :primary, :order)
                    ON CONFLICT (accommodation_id, image_id) DO NOTHING;
                """),
                {
                    "id": str(uuid.uuid5(uuid.UUID(acc["id"]), img["id"])),
                    "acc_id": acc["id"],
                    "img_id": img["id"],
                    "primary": img.get("is_primary", True),
                    "order": idx,
                },
            )


def run_standalone():
    """CLI runner using sync database connection."""
    from sqlalchemy import create_engine
    from app.core.config import settings

    sync_url = settings.sync_database_url
    print(f"Connecting to {sync_url}...")
    engine = create_engine(sync_url)
    with engine.begin() as conn:
        seed_geographic_foundation(conn)
    print("Seeding completed successfully.")


if __name__ == "__main__":
    run_standalone()
