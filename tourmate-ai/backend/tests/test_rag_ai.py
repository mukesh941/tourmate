"""
Phase 5 RAG & Grounded AI Assistant Comprehensive Test Suite.

Verifies all 23 required operational points:
1. embedding dimension = 384
2. embedding normalization
3. query/stored embedding compatibility
4. knowledge corpus integrity
5. deterministic seeding/idempotency
6. pgvector similarity ranking
7. top-K behavior
8. threshold behavior
9. POI-specific retrieval
10. destination-level retrieval
11. empty retrieval
12. grounded prompt construction
13. local deterministic fallback
14. insufficient-evidence refusal
15. route/distance authority guardrail
16. opening-hours/price guardrail
17. authenticated chat
18. unauthenticated chat -> 401
19. PostgreSQL UUID place_id
20. invalid/legacy place_id graceful handling
21. response contract contains data.response
22. sources metadata
23. correct is_grounded semantics
"""
import uuid
import numpy as np
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from app.main import app
from app.core.config import settings
from app.core.db import AsyncSessionLocal
from app.db.seeds.canonical_knowledge_data import CANONICAL_KNOWLEDGE_CHUNKS
from app.db.seeds.seed_knowledge import seed_knowledge_corpus, seed_knowledge_corpus_async
from app.services.embedding_service import get_embedding
from app.services.auth_service import create_access_token
from app.models.sql.user import User
from app.services.rag_service import (
    retrieve_knowledge_chunks,
    build_grounded_system_prompt,
    format_context_block,
    is_route_or_distance_query,
)
from app.services.ai_service import get_grounded_chat_response


@pytest.fixture
async def db_session():
    async with AsyncSessionLocal() as session:
        yield session


@pytest.fixture
async def test_user(db_session):
    user_id = uuid.uuid4()
    test_email = f"rag_tester_{uuid.uuid4().hex[:8]}@example.com"
    user = User(
        id=user_id,
        email=test_email,
        password_hash="hashed_pw",
        name="RAG Tester",
        role="user",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token = create_access_token(str(user.id))
    yield user, token

    # Cleanup user
    await db_session.execute(text("DELETE FROM users WHERE id = :uid"), {"uid": user_id})
    await db_session.commit()


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


# -----------------------------------------------------------------------------
# 1. Embedding Dimension = 384
# -----------------------------------------------------------------------------
def test_embedding_dimension():
    vec = get_embedding("Taj Mahal is an ivory-white marble mausoleum.")
    assert isinstance(vec, list)
    assert len(vec) == 384
    assert all(isinstance(x, float) for x in vec)


# -----------------------------------------------------------------------------
# 2. Embedding Normalization
# -----------------------------------------------------------------------------
def test_embedding_normalization():
    vec = get_embedding("Agra Fort was built by Mughal Emperor Akbar.")
    norm = np.linalg.norm(vec)
    assert norm == pytest.approx(1.0, abs=1e-4)


# -----------------------------------------------------------------------------
# 3. Query / Stored Embedding Compatibility
# -----------------------------------------------------------------------------
def test_embedding_compatibility():
    chunk = CANONICAL_KNOWLEDGE_CHUNKS[0]
    stored_text = f"{chunk['title']}\n{chunk['content']}"
    stored_vec = get_embedding(stored_text)
    query_vec = get_embedding("Taj Mahal architecture and mausoleum")

    # Cosine similarity between unit vectors is dot product
    sim = np.dot(stored_vec, query_vec)
    assert 0.0 < sim <= 1.0
    assert sim > 0.50  # Highly similar semantic content


# -----------------------------------------------------------------------------
# 4. Knowledge Corpus Integrity
# -----------------------------------------------------------------------------
def test_knowledge_corpus_integrity():
    # Exactly 17 chunks: 13 POI chunks for 12 POIs + 4 destination chunks
    assert len(CANONICAL_KNOWLEDGE_CHUNKS) == 17

    poi_chunks = [c for c in CANONICAL_KNOWLEDGE_CHUNKS if c["poi_id"] is not None]
    dest_chunks = [c for c in CANONICAL_KNOWLEDGE_CHUNKS if c["poi_id"] is None]

    assert len(poi_chunks) == 13
    assert len(dest_chunks) == 4

    # Verify unique IDs
    ids = [c["id"] for c in CANONICAL_KNOWLEDGE_CHUNKS]
    assert len(set(ids)) == len(ids)

    # Verify honest provenance
    for c in CANONICAL_KNOWLEDGE_CHUNKS:
        assert "editorial_verified" in c["source"]
        assert len(c["title"]) > 5
        assert len(c["content"]) > 50


# -----------------------------------------------------------------------------
# 5. Deterministic Seeding / Idempotency
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_seeding_idempotency(db_session):
    # Seed async twice
    count1 = await seed_knowledge_corpus_async(db_session)
    count2 = await seed_knowledge_corpus_async(db_session)

    assert count1 == 17
    assert count2 == 17

    # Total rows in DB must be exactly 17
    res = await db_session.execute(text("SELECT count(*) FROM knowledge_chunks;"))
    total_in_db = res.scalar()
    assert total_in_db == 17


# -----------------------------------------------------------------------------
# 6. pgvector Similarity Ranking
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_pgvector_similarity_ranking(db_session):
    chunks = await retrieve_knowledge_chunks(
        query="white marble mausoleum on Yamuna river built by Shah Jahan",
        db=db_session,
        top_k=3,
        min_similarity=0.40,
    )
    assert len(chunks) > 0
    top_chunk = chunks[0]
    assert "Taj Mahal" in top_chunk["title"]
    assert top_chunk["similarity"] > 0.50


# -----------------------------------------------------------------------------
# 7. Top-K Behavior
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_top_k_behavior(db_session):
    chunks = await retrieve_knowledge_chunks(
        query="fortress and royal palace architecture in India",
        db=db_session,
        top_k=2,
        min_similarity=0.30,
    )
    assert len(chunks) <= 2


# -----------------------------------------------------------------------------
# 8. Threshold Behavior
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_threshold_behavior(db_session):
    # Completely unrelated question
    chunks = await retrieve_knowledge_chunks(
        query="Who won the 1994 FIFA World Cup in soccer?",
        db=db_session,
        top_k=5,
        min_similarity=0.40,
    )
    # Must return empty because similarity is ~0.03 (< 0.40)
    assert chunks == []


# -----------------------------------------------------------------------------
# 9. POI-Specific Retrieval
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_poi_specific_retrieval(db_session):
    taj_uuid = uuid.UUID("b0000000-0000-0000-0000-000000000001")
    chunks = await retrieve_knowledge_chunks(
        query="Taj Mahal visiting guidelines and history",
        db=db_session,
        poi_id=taj_uuid,
        top_k=4,
        min_similarity=0.30,
    )
    assert len(chunks) > 0
    for c in chunks:
        # Either strictly Taj Mahal chunk or general destination chunk
        assert c["poi_id"] == str(taj_uuid) or c["poi_id"] is None
        # Must not be another POI (e.g. Qutub Minar or Amer Fort)
        if c["poi_id"]:
            assert c["poi_name"] == "Taj Mahal"


# -----------------------------------------------------------------------------
# 10. Destination-Level Retrieval
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_destination_level_retrieval(db_session):
    chunks = await retrieve_knowledge_chunks(
        query="Agra city travel overview and best months to visit",
        db=db_session,
        poi_id=None,
        top_k=3,
        min_similarity=0.40,
    )
    assert len(chunks) > 0
    dest_chunk = next((c for c in chunks if "Agra: Destination Overview" in c["title"]), None)
    assert dest_chunk is not None
    assert dest_chunk["poi_id"] is None


# -----------------------------------------------------------------------------
# 11. Empty Retrieval
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_empty_retrieval(db_session):
    chunks = await retrieve_knowledge_chunks(
        query="Quantum gravity string theory equations",
        db=db_session,
        top_k=3,
        min_similarity=0.90,  # Unattainable threshold
    )
    assert chunks == []


# -----------------------------------------------------------------------------
# 12. Grounded Prompt Construction
# -----------------------------------------------------------------------------
def test_grounded_prompt_construction():
    system_prompt = build_grounded_system_prompt("en")
    assert "STRICT AUTHORITY RULES" in system_prompt
    assert "Route Optimization feature on the Itinerary page" in system_prompt
    assert "Do NOT invent opening hours, prices" in system_prompt

    sample_chunks = [
        {
            "id": "test-1",
            "poi_name": "Taj Mahal",
            "title": "Taj Mahal Architecture",
            "source": "editorial_verified",
            "content": "Ivory-white marble mausoleum commissioned in 1631.",
        }
    ]
    context_block = format_context_block(sample_chunks)
    assert "[VERIFIED KNOWLEDGE CONTEXT]" in context_block
    assert "Taj Mahal Architecture" in context_block
    assert "Ivory-white marble mausoleum" in context_block
    assert "[END CONTEXT]" in context_block


# -----------------------------------------------------------------------------
# 13. Local Deterministic Fallback
# -----------------------------------------------------------------------------
def test_local_deterministic_fallback():
    sample_chunks = [
        {
            "id": "c1",
            "poi_name": "Taj Mahal",
            "title": "Taj Mahal Architecture",
            "source": "editorial_verified",
            "content": "The Taj Mahal is an ivory-white marble mausoleum on the Yamuna river.",
            "similarity": 0.75,
        }
    ]
    res = get_grounded_chat_response(
        user_message="Tell me about the Taj Mahal",
        history=[],
        retrieved_chunks=sample_chunks,
        language="en",
    )
    assert res["is_grounded"] is True
    assert "Taj Mahal is an ivory-white marble mausoleum" in res["response"]
    assert len(res["sources"]) == 1
    assert res["sources"][0]["title"] == "Taj Mahal Architecture"


# -----------------------------------------------------------------------------
# 14. Insufficient-Evidence Refusal
# -----------------------------------------------------------------------------
def test_insufficient_evidence_refusal():
    res = get_grounded_chat_response(
        user_message="Who won the 1994 World Cup?",
        history=[],
        retrieved_chunks=[],
        language="en",
    )
    assert res["is_grounded"] is False
    assert "I do not have verified knowledge about that in my database" in res["response"]
    assert res["sources"] == []


# -----------------------------------------------------------------------------
# 15. Route / Distance Authority Guardrail
# -----------------------------------------------------------------------------
def test_route_distance_guardrail():
    queries = [
        "How far is Taj Mahal from Agra Fort?",
        "What is the distance between Red Fort and Qutub Minar?",
        "Driving time from Hawa Mahal to Amer Fort?",
        "Directions from Gateway of India to CST?",
    ]
    for q in queries:
        assert is_route_or_distance_query(q) is True
        res = get_grounded_chat_response(
            user_message=q,
            history=[],
            retrieved_chunks=[],
            language="en",
        )
        assert res["is_grounded"] is True
        assert "Route Optimization feature on the Itinerary page" in res["response"]
        assert "verified OpenStreetMap" in res["response"]


# -----------------------------------------------------------------------------
# 16. Opening-Hours & Price Guardrail in Prompt
# -----------------------------------------------------------------------------
def test_opening_hours_price_guardrail_prompt():
    prompt = build_grounded_system_prompt("en")
    assert "Do NOT invent opening hours, prices, or live dynamic conditions" in prompt


# -----------------------------------------------------------------------------
# 17. Authenticated Chat Endpoint
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_api_chat_authenticated(client, test_user):
    user, token = test_user
    res = await client.post(
        "/api/ai/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "What is the Taj Mahal?"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "response" in data["data"]
    assert "sources" in data["data"]
    assert data["data"]["is_grounded"] is True


# -----------------------------------------------------------------------------
# 18. Unauthenticated Chat -> 401
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_api_chat_unauthenticated(client):
    res = await client.post(
        "/api/ai/chat",
        json={"message": "Hello"},
    )
    assert res.status_code == 401


# -----------------------------------------------------------------------------
# 19. PostgreSQL UUID place_id
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_api_chat_postgresql_uuid_place_id(client, test_user):
    user, token = test_user
    taj_id = "b0000000-0000-0000-0000-000000000001"
    res = await client.post(
        "/api/ai/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "message": "When was it built and who commissioned it?",
            "place_id": taj_id,
        },
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["is_grounded"] is True
    sources = data["sources"]
    assert any("Taj Mahal" in s["title"] for s in sources)


# -----------------------------------------------------------------------------
# 20. Invalid / Legacy place_id Graceful Handling
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_api_chat_invalid_place_id_graceful(client, test_user):
    user, token = test_user
    # Send non-UUID legacy string (e.g. 24-char hex mongo id or gibberish)
    res = await client.post(
        "/api/ai/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "message": "Tell me about Agra Fort",
            "place_id": "60c72b2f9b1d8b2bad8b4567",
        },
    )
    # Must NOT return 500 or crash; must gracefully fall back to general retrieval
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["is_grounded"] is True
    assert "Agra Fort" in data["response"]


# -----------------------------------------------------------------------------
# 21. Response Contract data.response Compatibility
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_api_chat_response_contract(client, test_user):
    user, token = test_user
    res = await client.post(
        "/api/ai/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "What is Mehtab Bagh?"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert isinstance(body["data"]["response"], str)
    assert len(body["data"]["response"]) > 20


# -----------------------------------------------------------------------------
# 22. Sources Metadata
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_api_chat_sources_metadata(client, test_user):
    user, token = test_user
    res = await client.post(
        "/api/ai/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "What is Qutub Minar?"},
    )
    assert res.status_code == 200
    sources = res.json()["data"]["sources"]
    assert isinstance(sources, list)
    assert len(sources) >= 1
    src = sources[0]
    assert "title" in src
    assert "source" in src
    assert "similarity" in src
    assert isinstance(src["similarity"], float)


# -----------------------------------------------------------------------------
# 23. Correct is_grounded Semantics
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_correct_is_grounded_semantics(client, test_user):
    user, token = test_user

    # Case A: Factual query with matching knowledge -> is_grounded = True
    res_a = await client.post(
        "/api/ai/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "Who built Hawa Mahal in Jaipur?"},
    )
    assert res_a.json()["data"]["is_grounded"] is True

    # Case B: Out-of-domain query with no matching knowledge -> is_grounded = False
    res_b = await client.post(
        "/api/ai/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "Who was the quarterback for the Green Bay Packers in 1996?"},
    )
    assert res_b.json()["data"]["is_grounded"] is False
    assert res_b.json()["data"]["sources"] == []

    # Case C: Route calculation query -> is_grounded = True (guardrail successfully executed)
    res_c = await client.post(
        "/api/ai/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "How far is Amer Fort from Hawa Mahal?"},
    )
    assert res_c.json()["data"]["is_grounded"] is True
    assert "Route Optimization" in res_c.json()["data"]["response"]
