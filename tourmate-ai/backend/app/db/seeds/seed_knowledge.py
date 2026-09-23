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


ACC_IMAGE_MAP = {
    # Agra
    "The Oberoi Amarvilas": "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=1200&q=80",
    "Tajview - IHCL SeleQtions": "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=1200&q=80",
    "Zostel Agra": "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?auto=format&fit=crop&w=1200&q=80",
    
    # New Delhi
    "The Imperial New Delhi": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1200&q=80",
    "Bloomrooms @ Janpath": "https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?auto=format&fit=crop&w=1200&q=80",
    "The Claridges New Delhi": "https://images.unsplash.com/photo-1566665797739-1674de7a421a?auto=format&fit=crop&w=1200&q=80",
    
    # Jaipur
    "Rambagh Palace": "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=1200&q=80",
    "Alsisar Haveli": "https://images.unsplash.com/photo-1566665797739-1674de7a421a?auto=format&fit=crop&w=1200&q=80",
    "Zostel Jaipur": "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?auto=format&fit=crop&w=1200&q=80",
    
    # Mumbai
    "The Taj Mahal Palace": "https://images.unsplash.com/photo-1582719508461-905c673771fd?auto=format&fit=crop&w=1200&q=80",
    "Residency Hotel Fort": "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=1200&q=80",
    "Zostel Mumbai": "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?auto=format&fit=crop&w=1200&q=80",
    
    # Bengaluru
    "The Leela Palace Bengaluru": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1200&q=80",
    "Bloomrooms @ Indiranagar": "https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?auto=format&fit=crop&w=1200&q=80",
    
    # Goa
    "Taj Fort Aguada Resort & Spa": "https://images.unsplash.com/photo-1582719508461-905c673771fd?auto=format&fit=crop&w=1200&q=80",
    "Santana Beach Resort": "https://images.unsplash.com/photo-1571896349842-33c89424de2d?auto=format&fit=crop&w=1200&q=80",
    "Zostel Goa (Morjim)": "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?auto=format&fit=crop&w=1200&q=80",
    
    # Varanasi
    "BrijRama Palace": "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=1200&q=80",
    "Stops Hostel Varanasi": "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?auto=format&fit=crop&w=1200&q=80",
    
    # Kochi / Kerala
    "Brunton Boatyard": "https://images.unsplash.com/photo-1571896349842-33c89424de2d?auto=format&fit=crop&w=1200&q=80",
    "Zostel Kochi": "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?auto=format&fit=crop&w=1200&q=80",
    
    # Udaipur
    "Taj Lake Palace": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1200&q=80",
    "Zostel Udaipur": "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?auto=format&fit=crop&w=1200&q=80",
    
    # Amritsar
    "Taj Swarna Amritsar": "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=1200&q=80",
    "Jugaadus Hostel": "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?auto=format&fit=crop&w=1200&q=80",
    
    # Hyderabad
    "Taj Falaknuma Palace": "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=1200&q=80",
    
    # Chennai
    "Taj Coromandel": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1200&q=80",
    
    # Mysuru
    "Lalitha Mahal Palace Hotel": "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=1200&q=80",
    
    # Manali
    "Johnson Lodge & Spa": "https://images.unsplash.com/photo-1512918728675-ed5a9ecdebfd?auto=format&fit=crop&w=1200&q=80",
    "Zostel Manali": "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?auto=format&fit=crop&w=1200&q=80",
    
    # Srinagar / Kashmir
    "The Lalit Grand Palace Srinagar": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1200&q=80",
    "Zostel Srinagar": "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?auto=format&fit=crop&w=1200&q=80",
}


def sync_accommodation_media(conn):
    for acc_name, img_url in ACC_IMAGE_MAP.items():
        conn.execute(
            text("""
                UPDATE images
                SET url = :img_url, thumbnail_url = :img_url, source = 'curated_unsplash', license_type = 'Unsplash License'
                WHERE id IN (
                    SELECT ai.image_id
                    FROM accommodation_images ai
                    JOIN accommodations a ON a.id = ai.accommodation_id
                    WHERE LOWER(TRIM(a.name)) = LOWER(TRIM(:acc_name))
                );
            """),
            {"img_url": img_url, "acc_name": acc_name}
        )


def seed_knowledge_corpus(conn) -> int:
    """
    Synchronously seeds canonical knowledge chunks and synchronizes accommodation media.
    """
    sync_accommodation_media(conn)
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
    for acc_name, img_url in ACC_IMAGE_MAP.items():
        await db.execute(
            text("""
                UPDATE images
                SET url = :img_url, thumbnail_url = :img_url, source = 'curated_unsplash', license_type = 'Unsplash License'
                WHERE id IN (
                    SELECT ai.image_id
                    FROM accommodation_images ai
                    JOIN accommodations a ON a.id = ai.accommodation_id
                    WHERE LOWER(TRIM(a.name)) = LOWER(TRIM(:acc_name))
                );
            """),
            {"img_url": img_url, "acc_name": acc_name}
        )

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
        print(f"Successfully seeded {count} canonical knowledge chunks and synchronized accommodation media into PostgreSQL.")
