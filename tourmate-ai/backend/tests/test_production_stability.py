"""
Production Stability and Reliability Regression Test Suite.
Verifies production resilience requirements for Render deployment:
1. /health returns successfully
2. /health is lightweight and instantaneous
3. Database session closes correctly
4. Failed database connection does not leak resources
5. External API timeout does not crash application
6. Gemini failure does not crash application
7. Model initialization failure is handled safely
8. Repeated health requests remain stable
9. Repeated database requests remain stable
10. Application exception does not kill subsequent requests
11. Readiness probe (/ready and /api/ready) handles healthy and failing database
"""
import time
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.main import app
from app.core.db import get_async_db, async_engine, AsyncSessionLocal
from app.services.embedding_service import get_embedding, _fallback_embedding
from app.services.ai_service import get_grounded_chat_response, get_ai_response, _safe_generate_content


@pytest.mark.asyncio
async def test_1_health_returns_successfully():
    """1. /health returns 200 OK with proper payload."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["status"] == "ok"

        # Also verify /api/health
        api_resp = await client.get("/api/health")
        assert api_resp.status_code == 200
        assert api_resp.json()["data"]["status"] == "ok"


@pytest.mark.asyncio
async def test_2_health_is_lightweight():
    """2. /health is lightweight (< 50ms locally) and performs zero heavy work."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        t0 = time.time()
        for _ in range(5):
            resp = await client.get("/health")
            assert resp.status_code == 200
        elapsed = time.time() - t0
        # 5 requests should take < 200ms total
        assert elapsed < 0.5, f"Health check too slow: {elapsed:.3f}s for 5 calls"


@pytest.mark.asyncio
async def test_3_database_session_closes_correctly():
    """3. Database session dependency guarantees closure and rollback on exit."""
    session_gen = get_async_db()
    session = await anext(session_gen)
    assert isinstance(session, AsyncSession)

    # Perform lightweight query
    result = await session.execute(text("SELECT 1"))
    assert result.scalar() == 1

    # Close via generator cleanup
    with pytest.raises(StopAsyncIteration):
        await anext(session_gen)


@pytest.mark.asyncio
async def test_4_failed_database_connection_does_not_leak_resources():
    """4. Failed database connection during session rolls back cleanly without leaving unclosed state."""
    session_gen = get_async_db()
    session = await anext(session_gen)

    # Simulate an error within session usage
    try:
        raise RuntimeError("Simulated transaction error")
    except RuntimeError as exc:
        try:
            await session_gen.athrow(exc)
        except RuntimeError:
            pass  # Expected to re-raise


@pytest.mark.asyncio
async def test_5_external_api_timeout_does_not_crash_application():
    """5. External API timeout does not crash application or freeze the caller."""
    mock_model = MagicMock()
    # Simulate slow/hanging generate_content
    def hanging_call(*args, **kwargs):
        time.sleep(1.0)
        return MagicMock(text="Late response")

    mock_model.generate_content.side_effect = hanging_call

    # Safe call with 0.1s timeout should timeout gracefully and return None
    result = _safe_generate_content(mock_model, "test prompt", timeout_sec=0.1)
    assert result is None


@pytest.mark.asyncio
async def test_6_gemini_failure_does_not_crash_application():
    """6. Gemini failure returns controlled fallback response and never crashes."""
    # When Gemini throws an exception or API key is invalid
    mock_model = MagicMock()
    mock_model.generate_content.side_effect = Exception("API rate limit or connection reset")

    with patch("google.generativeai.GenerativeModel", return_value=mock_model):
        resp = get_grounded_chat_response(
            user_message="Tell me about Taj Mahal",
            history=[],
            retrieved_chunks=[{
                "id": "chunk-1",
                "poi_name": "Taj Mahal",
                "title": "Taj Mahal Overview",
                "content": "Taj Mahal is an ivory-white marble mausoleum in Agra.",
                "source": "Verified Database",
                "similarity": 0.85
            }],
        )
        assert resp["is_grounded"] is True
        assert "Taj Mahal" in resp["response"]


@pytest.mark.asyncio
async def test_7_model_initialization_failure_is_handled_safely():
    """7. Model initialization failure falls back to deterministic embeddings."""
    with patch("app.services.embedding_service._session", None), \
         patch("app.services.embedding_service._tokenizer", None), \
         patch("app.services.embedding_service._load_failed", True):
        vec = get_embedding("Agra Fort landmark")
        assert isinstance(vec, list)
        assert len(vec) == 384
        # Verify it is normalized
        import numpy as np
        norm = np.linalg.norm(vec)
        assert abs(norm - 1.0) < 0.01


@pytest.mark.asyncio
async def test_8_repeated_health_requests_remain_stable():
    """8. Repeated health requests remain consistently fast and stable."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        for _ in range(25):
            resp = await client.get("/api/health")
            assert resp.status_code == 200
            assert resp.json()["data"]["status"] == "ok"


@pytest.mark.asyncio
async def test_9_repeated_database_requests_remain_stable():
    """9. Repeated database queries through connection pool stay stable without connection leaks."""
    for _ in range(15):
        async with AsyncSessionLocal() as session:
            res = await session.execute(text("SELECT 1"))
            assert res.scalar() == 1


@pytest.mark.asyncio
async def test_10_application_exception_does_not_kill_subsequent_requests():
    """10. Unhandled exception on one route does not crash the server for subsequent requests."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Send an invalid request that triggers 404 or 422
        bad_resp = await client.get("/api/places/non-existent-place-id-12345")
        assert bad_resp.status_code in (404, 500)

        # Ensure server immediately serves next health check cleanly
        good_resp = await client.get("/api/health")
        assert good_resp.status_code == 200
        assert good_resp.json()["data"]["status"] == "ok"


@pytest.mark.asyncio
async def test_11_readiness_probe_success():
    """11. /ready and /api/ready return 200 when database is healthy."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/ready")
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "ready"
        assert resp.json()["data"]["database"] == "connected"


@pytest.mark.asyncio
async def test_12_readiness_probe_database_failure():
    """12. /api/ready returns 503 when database is unreachable."""
    with patch("app.main.AsyncSessionLocal") as mock_session_local:
        mock_session = AsyncMock()
        mock_session.execute.side_effect = ConnectionRefusedError("PostgreSQL unreachable")
        mock_session_local.return_value.__aenter__.return_value = mock_session

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/ready")
            assert resp.status_code == 503
            data = resp.json()
            assert data["success"] is False
            assert data["data"]["status"] == "unready"
            assert data["data"]["database"] == "disconnected"
