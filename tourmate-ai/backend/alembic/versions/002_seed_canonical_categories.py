"""Data migration: seed canonical categories for onboarding UI.

Revision ID: 002_seed_canonical_categories
Revises: 001_initial_23_tables
Create Date: 2026-09-20 03:10:00.000000

"""
from typing import Sequence, Union
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002_seed_canonical_categories"
down_revision: Union[str, None] = "001_initial_23_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO categories (id, name, slug, icon, description, created_at)
        VALUES 
            ('a0000000-0000-0000-0000-000000000001', 'History', 'history', 'Landmark', 'Historical landmarks, heritage monuments, and historical sites', NOW()),
            ('a0000000-0000-0000-0000-000000000002', 'Nature', 'nature', 'Trees', 'Parks, wildlife sanctuaries, scenic landscapes, and nature trails', NOW()),
            ('a0000000-0000-0000-0000-000000000003', 'Culture', 'culture', 'Palette', 'Cultural museums, arts, local traditions, and heritage', NOW()),
            ('a0000000-0000-0000-0000-000000000004', 'Adventure', 'adventure', 'Compass', 'Outdoor activities, trekking, water sports, and adventures', NOW()),
            ('a0000000-0000-0000-0000-000000000005', 'Food', 'food', 'Utensils', 'Local cuisine, iconic eateries, street food, and dining', NOW()),
            ('a0000000-0000-0000-0000-000000000006', 'Shopping', 'shopping', 'ShoppingBag', 'Bazaars, handicraft markets, malls, and shopping districts', NOW()),
            ('a0000000-0000-0000-0000-000000000007', 'Architecture', 'architecture', 'Building', 'Architectural wonders, palaces, forts, and urban design', NOW())
        ON CONFLICT (name) DO NOTHING;
    """)


def downgrade() -> None:
    op.execute("""
        DELETE FROM categories WHERE id IN (
            'a0000000-0000-0000-0000-000000000001',
            'a0000000-0000-0000-0000-000000000002',
            'a0000000-0000-0000-0000-000000000003',
            'a0000000-0000-0000-0000-000000000004',
            'a0000000-0000-0000-0000-000000000005',
            'a0000000-0000-0000-0000-000000000006',
            'a0000000-0000-0000-0000-000000000007'
        );
    """)
