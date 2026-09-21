"""
Idempotent Seeder for Phase 5 RAG Knowledge Corpus.
Populates PostgreSQL knowledge_chunks with verified embeddings using all-MiniLM-L6-v2.
"""
import sys
import uuid
from typing import Optional
from sqlalchemy import text
from app.core.config import settings
from app.db.seeds.canonical_knowledge_data import CANONICAL_KNOWLEDGE_CHUNKS
from app.services.embedding_service import get_embedding


def seed_knowledge_corpus(conn) -> int:
    """
    Synchronously seeds canonical knowledge chunks into PostgreSQL knowledge_chunks table.
    Computes 384-dimensional normalized embeddings using all-MiniLM-L6-v2.
    Idempotent: updates existing chunk records by ID or inserts new ones.
    """
    seeded_count = 0

    for chunk in CANONICAL_KNOWLEDGE_CHUNKS:
        # Use precomputed 384-d normalized embedding if present, or compute via ONNX
        if "embedding" in chunk and chunk["embedding"]:
            embedding_vec = chunk["embedding"]
        else:
            text_to_embed = f"{chunk['title']}\n{chunk['content']}"
            embedding_vec = get_embedding(text_to_embed)

        # Ensure embedding is valid 384-d vector
        if len(embedding_vec) != 384:
            raise ValueError(
                f"Invalid embedding dimension {len(embedding_vec)} for chunk '{chunk['title']}'. Expected 384."
            )

        poi_id_val = chunk["poi_id"]

        conn.execute(
            text("""
                INSERT INTO knowledge_chunks (
                    id, poi_id, title, content, embedding, source, created_at
                ) VALUES (
                    :id, :poi_id, :title, :content, :embedding, :source, NOW()
                )
                ON CONFLICT (id) DO UPDATE SET
                    poi_id = EXCLUDED.poi_id,
                    title = EXCLUDED.title,
                    content = EXCLUDED.content,
                    embedding = EXCLUDED.embedding,
                    source = EXCLUDED.source;
            """),
            {
                "id": chunk["id"],
                "poi_id": poi_id_val,
                "title": chunk["title"],
                "content": chunk["content"],
                "embedding": str(embedding_vec),
                "source": chunk["source"],
            },
        )
        seeded_count += 1

    return seeded_count


async def seed_knowledge_corpus_async(db) -> int:
    """
    Asynchronously seeds canonical knowledge chunks using an AsyncSession.
    """
    seeded_count = 0
    for chunk in CANONICAL_KNOWLEDGE_CHUNKS:
        if "embedding" in chunk and chunk["embedding"]:
            embedding_vec = chunk["embedding"]
        else:
            text_to_embed = f"{chunk['title']}\n{chunk['content']}"
            embedding_vec = get_embedding(text_to_embed)

        if len(embedding_vec) != 384:
            raise ValueError(
                f"Invalid embedding dimension {len(embedding_vec)} for chunk '{chunk['title']}'"
            )

        await db.execute(
            text("""
                INSERT INTO knowledge_chunks (
                    id, poi_id, title, content, embedding, source, created_at
                ) VALUES (
                    :id, :poi_id, :title, :content, :embedding, :source, NOW()
                )
                ON CONFLICT (id) DO UPDATE SET
                    poi_id = EXCLUDED.poi_id,
                    title = EXCLUDED.title,
                    content = EXCLUDED.content,
                    embedding = EXCLUDED.embedding,
                    source = EXCLUDED.source;
            """),
            {
                "id": chunk["id"],
                "poi_id": chunk["poi_id"],
                "title": chunk["title"],
                "content": chunk["content"],
                "embedding": str(embedding_vec),
                "source": chunk["source"],
            },
        )
        seeded_count += 1

    await db.commit()
    return seeded_count


if __name__ == "__main__":
    from sqlalchemy import create_engine

    engine = create_engine(settings.sync_database_url)
    with engine.begin() as connection:
        count = seed_knowledge_corpus(connection)
        print(f"Successfully seeded {count} canonical knowledge chunks into PostgreSQL.")
