"""Data migration: seed canonical 17 RAG knowledge chunks into PostgreSQL.

Revision ID: 005_seed_knowledge_corpus
Revises: 004_expand_geo_dataset
Create Date: 2026-09-21 22:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
from app.db.seeds.seed_knowledge import seed_knowledge_corpus

# revision identifiers, used by Alembic (max 32 chars).
revision: str = "005_seed_knowledge_corpus"
down_revision: Union[str, None] = "004_expand_geo_dataset"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    seed_knowledge_corpus(conn)


def downgrade() -> None:
    conn = op.get_bind()
    from sqlalchemy import text
    from app.db.seeds.canonical_knowledge_data import CANONICAL_KNOWLEDGE_CHUNKS

    chunk_ids = tuple(c["id"] for c in CANONICAL_KNOWLEDGE_CHUNKS)
    if chunk_ids:
        conn.execute(text("DELETE FROM knowledge_chunks WHERE id IN :ids;"), {"ids": chunk_ids})
