"""Data migration: seed canonical geographic, POI, opening hours, media, and accommodation foundation.

Revision ID: 003_seed_geo_foundation
Revises: 002_seed_canonical_categories
Create Date: 2026-09-20 03:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
from app.db.seeds.seeder import seed_geographic_foundation

# revision identifiers, used by Alembic (max 32 chars).
revision: str = "003_seed_geo_foundation"
down_revision: Union[str, None] = "002_seed_canonical_categories"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    seed_geographic_foundation(conn)


def downgrade() -> None:
    conn = op.get_bind()
    from app.db.seeds.canonical_seed_data import PILOT_POIS, PILOT_ACCOMMODATIONS
    from sqlalchemy import text

    poi_ids = tuple(p["id"] for p in PILOT_POIS)
    acc_ids = tuple(a["id"] for a in PILOT_ACCOMMODATIONS)
    loc_ids = tuple(p["location_id"] for p in PILOT_POIS) + tuple(a["location_id"] for a in PILOT_ACCOMMODATIONS)

    # Delete in reverse FK dependency order
    if poi_ids:
        conn.execute(text("DELETE FROM opening_hours WHERE poi_id IN :ids;"), {"ids": poi_ids})
        conn.execute(text("DELETE FROM poi_images WHERE poi_id IN :ids;"), {"ids": poi_ids})
        conn.execute(text("DELETE FROM pois WHERE id IN :ids;"), {"ids": poi_ids})

    if acc_ids:
        conn.execute(text("DELETE FROM accommodation_images WHERE accommodation_id IN :ids;"), {"ids": acc_ids})
        conn.execute(text("DELETE FROM accommodations WHERE id IN :ids;"), {"ids": acc_ids})

    if loc_ids:
        conn.execute(text("DELETE FROM locations WHERE id IN :ids;"), {"ids": loc_ids})
