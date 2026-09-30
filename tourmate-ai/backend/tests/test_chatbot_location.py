import pytest
import uuid
from typing import Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.testclient import TestClient

from app.core.db import AsyncSessionLocal
from app.services.destination_resolver import (
    extract_destination_from_message,
    resolve_destination,
    full_destination_resolution,
    CITY_ALIASES
)
from app.services.rag_service import is_route_or_distance_query

@pytest.fixture
async def db_session():
    async with AsyncSessionLocal() as session:
        yield session

@pytest.mark.asyncio
async def test_destination_extraction_goa():
    msg = "Plan a trip to Goa for 3 days"
    dest = extract_destination_from_message(msg)
    assert dest == "Goa"

@pytest.mark.asyncio
async def test_destination_extraction_udupi():
    msg = "I want to visit Udupi"
    dest = extract_destination_from_message(msg)
    assert dest == "Udupi"
    
    msg2 = "Tell me about Mysuru"
    dest2 = extract_destination_from_message(msg2)
    assert dest2 == "Mysuru"

@pytest.mark.asyncio
async def test_destination_extraction_aliases():
    assert extract_destination_from_message("Tell me about Bangalore") == "Bengaluru"
    assert extract_destination_from_message("Tell me about Mysore") == "Mysuru"
    assert extract_destination_from_message("Tell me about Bombay") == "Mumbai"
    assert extract_destination_from_message("Tell me about Delhi") == "Delhi"

def test_route_question_detection():
    assert is_route_or_distance_query("How do I travel from Bengaluru to Mysuru?")
    assert is_route_or_distance_query("How do I get from Udupi to Mangaluru?")
    assert is_route_or_distance_query("How do I travel from Goa to Bengaluru?")

@pytest.mark.asyncio
async def test_foreign_location_protection(db_session: AsyncSession):
    msg = "Plan a trip to Paris"
    dest_resolved, intent_info = await full_destination_resolution(msg, db_session)
    assert dest_resolved is not None
    assert dest_resolved.get("is_foreign") is True
    
    msg = "Tell me about London"
    dest_resolved, intent_info = await full_destination_resolution(msg, db_session)
    assert dest_resolved is not None
    assert dest_resolved.get("is_foreign") is True

@pytest.mark.asyncio
async def test_conversation_context(db_session: AsyncSession):
    # This requires full_destination_resolution logic
    msg1 = "Tell me about Udupi"
    dest1, _ = await full_destination_resolution(msg1, db_session)
    assert dest1 and dest1["name"] == "Udupi"
    
    msg2 = "What should I visit there?"
    dest2, _ = await full_destination_resolution(msg2, db_session, session_destination=dest1)
    assert dest2 and dest2["name"] == "Udupi"

@pytest.mark.asyncio
async def test_destination_correction(db_session: AsyncSession):
    msg1 = "Tell me about Mumbai"
    dest1, _ = await full_destination_resolution(msg1, db_session)
    assert dest1 and dest1["name"] == "Mumbai"
    
    msg2 = "No, I mean Goa"
    dest2, _ = await full_destination_resolution(msg2, db_session, session_destination=dest1)
    assert dest2 and dest2["name"] == "Goa"

@pytest.mark.asyncio
async def test_destination_switching(db_session: AsyncSession):
    msg1 = "Tell me about Goa"
    dest1, _ = await full_destination_resolution(msg1, db_session)
    assert dest1 and dest1["name"] == "Goa"
    
    msg2 = "Now tell me about Jaipur"
    dest2, _ = await full_destination_resolution(msg2, db_session, session_destination=dest1)
    assert dest2 and dest2["name"] == "Jaipur"
