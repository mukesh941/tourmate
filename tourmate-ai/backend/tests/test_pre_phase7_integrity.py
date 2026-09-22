import pytest
import io
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.services.ai_service import predict_landmark_from_image


# ============================================================================
# BUG 5 TESTS: AUTHORITATIVE ITINERARY & FALSE DATA PREVENTION
# ============================================================================

@pytest.mark.anyio
async def test_itinerary_case_1_agra_multiday():
    """1. Agra multi-day itinerary: verified POIs (Taj Mahal, Agra Fort, Mehtab Bagh), no invented places."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "destination_name": "Agra",
            "days": 2,
            "start_time": "09:00",
            "end_time": "18:00",
            "budget": "Medium",
            "travel_type": "Couple"
        }
        res = await client.post("/api/itineraries/generate", json=payload)
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        options = body["data"]
        assert len(options) == 3
        
        # Verify that all activities correspond to verified Agra canonical POIs
        known_agra_pois = {"Taj Mahal", "Agra Fort", "Mehtab Bagh"}
        for opt in options:
            for day_data in opt["schedule"]:
                for act in day_data["activities"]:
                    assert act["name"] in known_agra_pois
                    assert act["estimated_cost"] > 0
                    assert act["openingHours"] != "Closed on scheduled dates"
                    assert "latitude" in act and act["latitude"] is not None


@pytest.mark.anyio
async def test_itinerary_case_2_bengaluru():
    """2. Bengaluru itinerary: verified POIs (Bangalore Palace, Lalbagh, Tipu Sultan's Palace)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "destination_name": "Bengaluru",
            "days": 1,
            "start_time": "09:00",
            "end_time": "18:00",
            "budget": "Medium",
            "travel_type": "Solo"
        }
        res = await client.post("/api/itineraries/generate", json=payload)
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        options = body["data"]
        
        known_blr_pois = {"Bangalore Palace", "Lalbagh Botanical Garden", "Tipu Sultan's Summer Palace"}
        for opt in options:
            for day_data in opt["schedule"]:
                for act in day_data["activities"]:
                    assert act["name"] in known_blr_pois
                    assert act["openingHours"] != ""


@pytest.mark.anyio
async def test_itinerary_case_3_jaipur():
    """3. Jaipur itinerary: verified POIs (Hawa Mahal, Amer Fort, Jantar Mantar)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "destination_name": "Jaipur",
            "days": 1,
            "start_time": "09:00",
            "end_time": "18:00",
            "budget": "Medium",
            "travel_type": "Family"
        }
        res = await client.post("/api/itineraries/generate", json=payload)
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        options = body["data"]
        
        known_jaipur_pois = {"Hawa Mahal", "Amer Fort", "Jantar Mantar"}
        for opt in options:
            for day_data in opt["schedule"]:
                for act in day_data["activities"]:
                    assert act["name"] in known_jaipur_pois


@pytest.mark.anyio
async def test_itinerary_case_4_closed_poi_handling():
    """4. Itinerary with closed POI: permanently/schedule-closed POIs are filtered out."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "destination_name": "Agra",
            "days": 1,
            "start_time": "09:00",
            "end_time": "18:00",
            "budget": "Medium"
        }
        res = await client.post("/api/itineraries/generate", json=payload)
        assert res.status_code == 200
        options = res.json()["data"]
        for opt in options:
            for day in opt["schedule"]:
                for act in day["activities"]:
                    # No scheduled activity should be closed
                    assert "closed" not in act["openingHours"].lower() or "09" in act["openingHours"]


@pytest.mark.anyio
async def test_itinerary_case_5_limited_available_time():
    """5. Itinerary with limited available time (<90 mins) fails gracefully."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "destination_name": "Agra",
            "days": 1,
            "start_time": "09:00",
            "end_time": "10:00",  # Only 60 mins: insufficient for safe visit
            "budget": "Medium"
        }
        res = await client.post("/api/itineraries/generate", json=payload)
        assert res.status_code == 400
        assert "short" in res.json()["detail"].lower()


@pytest.mark.anyio
async def test_itinerary_case_6_budget_constraints():
    """6. Itinerary with budget constraints: filters for lower price tier without inventing prices."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "destination_name": "Agra",
            "days": 1,
            "start_time": "09:00",
            "end_time": "18:00",
            "budget": "Budget"
        }
        res = await client.post("/api/itineraries/generate", json=payload)
        assert res.status_code == 200
        options = res.json()["data"]
        for opt in options:
            # Budget tier total cost is bounded and deterministic
            assert opt["total_estimated_cost"] <= 1500


@pytest.mark.anyio
async def test_itinerary_case_7_no_valid_candidates_fails_gracefully():
    """7. Itinerary with nonexistent destination fails gracefully without hallucinating fake places."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "destination_name": "AtlantisNonExistentCity",
            "days": 1,
            "start_time": "09:00",
            "end_time": "18:00"
        }
        res = await client.post("/api/itineraries/generate", json=payload)
        assert res.status_code == 404
        assert "no verified attractions found" in res.json()["detail"].lower()


# ============================================================================
# BUG 3 TESTS: AI LENS LANDMARK RECOGNITION & CANONICAL POI GROUNDING
# ============================================================================

def _make_test_image() -> bytes:
    import io
    from PIL import Image
    img = Image.new("RGB", (32, 32), color="red")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


@pytest.mark.anyio
async def test_landmark_case_1_known_canonical_poi(monkeypatch):
    """1. Known TourMate POI: returns exact name, verified location, and is_grounded=True."""
    # Mock vision response indicating Taj Mahal
    def mock_gemini_content(*args, **kwargs):
        class MockRes:
            text = '{"is_landmark": true, "name": "Taj Mahal", "location": "Agra, Uttar Pradesh", "category": "Historical Monument", "confidence": "High", "description": "Iconic marble mausoleum."}'
        return MockRes()

    class MockModel:
        def __init__(self, *args, **kwargs): pass
        def generate_content(self, *args, **kwargs): return mock_gemini_content()

    monkeypatch.setattr("app.services.ai_service.genai.GenerativeModel", MockModel)
    monkeypatch.setattr("app.services.ai_service.settings.gemini_api_key", "test-key")

    dummy_image = _make_test_image()
    result = await predict_landmark_from_image(dummy_image)
    assert result["name"] == "Taj Mahal"
    assert result["is_landmark"] is True
    assert result["is_grounded"] is True
    assert result["confidence"] == "High"
    assert "Agra" in result["location"]


@pytest.mark.anyio
async def test_landmark_case_2_vidhana_soudha(monkeypatch):
    """2. Vidhana Soudha: recognized accurately as Vidhana Soudha, Bengaluru without becoming generic 'palace'."""
    def mock_gemini_content(*args, **kwargs):
        class MockRes:
            text = '{"is_landmark": true, "name": "Vidhana Soudha", "location": "Bengaluru, Karnataka", "category": "Landmark / Government Building", "confidence": "High", "description": "Neo-Dravidian legislative building of Karnataka."}'
        return MockRes()

    class MockModel:
        def __init__(self, *args, **kwargs): pass
        def generate_content(self, *args, **kwargs): return mock_gemini_content()

    monkeypatch.setattr("app.services.ai_service.genai.GenerativeModel", MockModel)
    monkeypatch.setattr("app.services.ai_service.settings.gemini_api_key", "test-key")

    dummy_image = _make_test_image()
    result = await predict_landmark_from_image(dummy_image)
    assert result["name"] == "Vidhana Soudha"
    assert "Bengaluru" in result["location"]
    assert "Government Building" in result["category"] or "Landmark" in result["category"]
    assert result["confidence"] == "High"
    assert result["name"] != "Palace"


@pytest.mark.anyio
async def test_landmark_case_3_unrelated_image(monkeypatch):
    """3. Unrelated image (e.g. coffee, shoe, animal): returns appropriate 'unable to identify' response."""
    def mock_gemini_content(*args, **kwargs):
        class MockRes:
            text = '{"is_landmark": false, "name": "Unrecognized Landmark", "location": "", "category": "Non-Landmark", "confidence": "None", "description": "Unable to identify a recognized landmark or tourist attraction in this image."}'
        return MockRes()

    class MockModel:
        def __init__(self, *args, **kwargs): pass
        def generate_content(self, *args, **kwargs): return mock_gemini_content()

    monkeypatch.setattr("app.services.ai_service.genai.GenerativeModel", MockModel)
    monkeypatch.setattr("app.services.ai_service.settings.gemini_api_key", "test-key")

    dummy_image = _make_test_image()
    result = await predict_landmark_from_image(dummy_image)
    assert result["is_landmark"] is False
    assert result["confidence"] == "None"
    assert "Unable to identify" in result["description"]
    assert result["name"] != "Palace"
