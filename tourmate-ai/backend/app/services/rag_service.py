"""
RAG Service for TourMate AI Assistant.

Handles:
- Semantic query embedding via all-MiniLM-L6-v2 ONNX.
- pgvector cosine similarity search on knowledge_chunks.
- POI-aware chunk filtering and prioritization.
- Configurable similarity thresholding and top-K.
- Grounded prompt formulation and authority guardrail detection.
"""
import re
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.services.embedding_service import get_embedding


def is_route_or_distance_query(message: str) -> bool:
    """
    Detects if a user question is asking for distance, driving time, or step-by-step routing directions.
    The LLM is NOT authoritative for road calculations and must defer to Phase 4 routing engine.
    """
    lower = message.lower()
    patterns = [
        r"\bhow\s+far\b",
        r"\bdistance\s+between\b",
        r"\bdriving\s+time\b",
        r"\btravel\s+time\s+from\b",
        r"\bhow\s+long\s+does\s+it\s+take\s+to\s+drive\b",
        r"\broute\s+from\s+.+\s+to\b",
        r"\bdirections\s+from\s+.+\s+to\b",
        r"\bshortest\s+path\s+between\b",
        r"\boptimized\s+route\b",
    ]
    return any(re.search(p, lower) for p in patterns)


async def retrieve_knowledge_chunks(
    query: str,
    db: AsyncSession,
    poi_id: Optional[uuid.UUID] = None,
    top_k: Optional[int] = None,
    min_similarity: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieves top-K knowledge chunks matching query from PostgreSQL pgvector.
    Applies configurable similarity threshold and POI-awareness.
    """
    k = top_k if top_k is not None else settings.rag_top_k
    threshold = min_similarity if min_similarity is not None else settings.rag_min_similarity

    # Generate 384-d normalized query vector
    query_vec = get_embedding(query)
    query_vec_str = str(query_vec)

    # POI-aware filter: if poi_id is provided, restrict to (poi_id = :poi_id OR poi_id IS NULL)
    if poi_id:
        sql = text("""
            SELECT kc.id, kc.poi_id, p.name AS poi_name, kc.title, kc.content, kc.source,
                   1 - (kc.embedding <=> :query_vec) AS similarity
            FROM knowledge_chunks kc
            LEFT JOIN pois p ON kc.poi_id = p.id
            WHERE (kc.poi_id = :poi_id OR kc.poi_id IS NULL)
            ORDER BY kc.embedding <=> :query_vec ASC, kc.id ASC
            LIMIT :top_k;
        """)
        params = {"query_vec": query_vec_str, "poi_id": poi_id, "top_k": k}
    else:
        sql = text("""
            SELECT kc.id, kc.poi_id, p.name AS poi_name, kc.title, kc.content, kc.source,
                   1 - (kc.embedding <=> :query_vec) AS similarity
            FROM knowledge_chunks kc
            LEFT JOIN pois p ON kc.poi_id = p.id
            ORDER BY kc.embedding <=> :query_vec ASC, kc.id ASC
            LIMIT :top_k;
        """)
        params = {"query_vec": query_vec_str, "top_k": k}

    result = await db.execute(sql, params)
    rows = result.fetchall()

    chunks = []
    for row in rows:
        sim = float(row.similarity)
        if sim >= threshold:
            chunks.append({
                "id": str(row.id),
                "poi_id": str(row.poi_id) if row.poi_id else None,
                "poi_name": row.poi_name,
                "title": row.title,
                "content": row.content,
                "source": row.source,
                "similarity": round(sim, 4),
            })

    return chunks


def build_grounded_system_prompt(language: str = "en") -> str:
    """
    Constructs strict system instructions forbidding hallucination and numerical route calculations.
    """
    prompt = (
        "You are TourMate AI, an authoritative, friendly local travel guide. "
        "Your answers must be grounded STRICTLY in the provided verified knowledge context.\n\n"
        "STRICT AUTHORITY RULES:\n"
        "1. Base your factual claims exclusively on the provided Context.\n"
        "2. If the answer cannot be determined from the provided Context, state: "
        "'I do not have verified knowledge about that in my database.' Do NOT fabricate facts.\n"
        "3. Do NOT calculate, guess, or estimate road driving distances, driving times, or step-by-step navigation paths. "
        "For travel routes, inform the user: 'For accurate road distances, directions, and travel times, "
        "please use TourMate AI's Route Optimization feature on the Itinerary page, which computes verified road networks.'\n"
        "4. Do NOT invent opening hours, prices, or live dynamic conditions not present in the Context.\n"
        "5. Keep your tone helpful, factual, and concise."
    )
    if language == "hi":
        prompt += "\n\nPlease always reply in Hindi."
    else:
        prompt += "\n\nPlease always reply in English."
    return prompt


def format_context_block(chunks: List[Dict[str, Any]]) -> str:
    """
    Formats retrieved chunks into a clean, labeled Context block for prompt injection.
    """
    if not chunks:
        return ""

    context_lines = ["[VERIFIED KNOWLEDGE CONTEXT]"]
    for i, c in enumerate(chunks, 1):
        poi_label = f" (POI: {c['poi_name']})" if c.get("poi_name") else ""
        context_lines.append(f"--- Document {i}: {c['title']}{poi_label} ---")
        context_lines.append(f"Source: {c['source']}")
        context_lines.append(c["content"])
        context_lines.append("")
    context_lines.append("[END CONTEXT]")
    return "\n".join(context_lines)
