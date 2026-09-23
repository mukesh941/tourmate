import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch

from app.main import app
from app.core.config import settings
from app.schemas.hotel import HotelResponse
from app.services.google_places_service import _normalize_lodging, deduplicate_places
from app.services.hotel_service import get_all_hotels, DESTINATION_ALIASES


@pytest.mark.asyncio
async def test_canonical_hotels_retrieval():
    """Verify canonical accommodations are retrieved with valid attributes."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/hotels")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        hotels = data["data"]
        assert len(hotels) >= 30
        
        # Verify first hotel structure
        h = hotels[0]
        assert "id" in h
        assert "name" in h
        assert "city" in h
        assert "price_per_night_start" in h
        assert "cover_image" in h
        assert h["cover_image"].startswith("http") or h["cover_image"].startswith("data:")


@pytest.mark.asyncio
async def test_destination_filtering_kerala():
    """Verify filtering by 'Kerala' returns Kerala accommodations (Kochi)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/hotels?city=Kerala")
        assert response.status_code == 200
        hotels = response.json()["data"]
        assert len(hotels) >= 2
        hotel_names = [h["name"] for h in hotels]
        assert "Brunton Boatyard" in hotel_names or "Zostel Kochi" in hotel_names
        for h in hotels:
            assert h["city"] in ["Kochi", "Kerala"] or "Kerala" in h["description"]


@pytest.mark.asyncio
async def test_destination_filtering_goa():
    """Verify filtering by 'Goa' returns Goa accommodations."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/hotels?city=Goa")
        assert response.status_code == 200
        hotels = response.json()["data"]
        assert len(hotels) >= 3
        hotel_names = [h["name"] for h in hotels]
        assert "Taj Fort Aguada Resort & Spa" in hotel_names
        assert "Santana Beach Resort" in hotel_names


@pytest.mark.asyncio
async def test_destination_filtering_jaipur():
    """Verify filtering by 'Jaipur' returns Jaipur accommodations."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/hotels?city=Jaipur")
        assert response.status_code == 200
        hotels = response.json()["data"]
        assert len(hotels) >= 3
        hotel_names = [h["name"] for h in hotels]
        assert "Rambagh Palace" in hotel_names
        assert "Alsisar Haveli" in hotel_names


@pytest.mark.asyncio
async def test_destination_filtering_agra():
    """Verify filtering by 'Agra' returns Agra accommodations."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/hotels?city=Agra")
        assert response.status_code == 200
        hotels = response.json()["data"]
        assert len(hotels) >= 3
        hotel_names = [h["name"] for h in hotels]
        assert "The Oberoi Amarvilas" in hotel_names


@pytest.mark.asyncio
async def test_destination_filtering_kashmir():
    """Verify filtering by 'Kashmir' returns Srinagar accommodations."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/hotels?city=Kashmir")
        assert response.status_code == 200
        hotels = response.json()["data"]
        assert len(hotels) >= 2
        hotel_names = [h["name"] for h in hotels]
        assert "The Lalit Grand Palace Srinagar" in hotel_names or "Zostel Srinagar" in hotel_names


@pytest.mark.asyncio
async def test_unknown_destination_returns_empty_list():
    """Verify querying an unknown destination returns a clean empty list without leaking other cities."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/hotels?city=NonExistentCityXYZ")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] == []


@pytest.mark.asyncio
async def test_external_lodging_normalization():
    """Verify Google Places lodging is normalized without fabricating fake prices or ratings."""
    mock_gplace = {
        "id": "ChIJ_mock_place_123",
        "displayName": {"text": "Backwaters Haven Resort"},
        "location": {"latitude": 9.4981, "longitude": 76.3388},
        "types": ["resort_hotel", "lodging", "point_of_interest"],
        "rating": 4.7,
        "userRatingCount": 350,
        "formattedAddress": "Finishing Point Road, Punnamada, Alappuzha",
        "editorialSummary": {"text": "Luxury lakeside resort in the backwaters."},
        "photos": []
    }
    normalized = _normalize_lodging(mock_gplace, destination_city="Alleppey")
    assert normalized["id"] == "google-ChIJ_mock_place_123"
    assert normalized["name"] == "Backwaters Haven Resort"
    assert normalized["city"] == "Alleppey"
    assert normalized["hotel_type"] == "Resort"
    assert normalized["rating"] == 4.7
    assert normalized["review_count"] == 350
    assert normalized["price_per_night_start"] is None  # Must NOT fabricate price
    assert normalized["source"] == "google"
    assert normalized["external_place_id"] == "ChIJ_mock_place_123"
    assert "Verified" in normalized["cover_image"]


@pytest.mark.asyncio
async def test_external_lodging_discovery_fallback():
    """Verify layered discovery searches external provider when canonical count is low."""
    mock_external = [
        {
            "id": "google-ext-1",
            "name": "Wayanad Wild Rainforest Lodge",
            "description": "Eco-friendly rainforest stay.",
            "city": "Wayanad",
            "address": "Lakkidi, Wayanad",
            "destination_id": "Wayanad",
            "location": {"type": "Point", "coordinates": [76.0421, 11.5218]},
            "rating": 4.8,
            "review_count": 210,
            "price_per_night_start": None,
            "currency": "₹",
            "cover_image": "data:image/svg+xml;charset=UTF-8,test",
            "images": ["data:image/svg+xml;charset=UTF-8,test"],
            "amenities": ["Nature Walk", "Pool"],
            "hotel_type": "Resort",
            "rooms": [],
            "source": "google",
            "external_place_id": "ext-1",
            "external_booking_url": "https://maps.google.com/?q=place_id:ext-1",
        }
    ]

    with patch("app.core.config.settings.google_maps_api_key", "mock-key-123"):
        with patch("app.services.google_places_service.search_lodging", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = mock_external
            
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.get("/api/hotels?city=Wayanad")
                assert response.status_code == 200
                hotels = response.json()["data"]
                assert len(hotels) >= 1
                assert any(h["name"] == "Wayanad Wild Rainforest Lodge" for h in hotels)
                mock_search.assert_called_once()


@pytest.mark.asyncio
async def test_external_lodging_deduplication():
    """Verify duplicate external records with existing canonical names are pruned."""
    mock_external = [
        {
            "id": "google-dup-1",
            "name": "The Oberoi Amarvilas",  # Duplicate of canonical
            "description": "Duplicate result",
            "city": "Agra",
            "address": "Agra",
            "location": {"type": "Point", "coordinates": [78.049, 27.169]},
            "rating": 4.9,
            "review_count": 500,
            "price_per_night_start": None,
            "currency": "₹",
            "cover_image": "data:image/svg+xml;charset=UTF-8,test",
            "images": [],
            "amenities": [],
            "hotel_type": "Hotel",
            "rooms": [],
            "source": "google",
            "external_place_id": "ext-dup",
        }
    ]

    with patch("app.core.config.settings.google_maps_api_key", "mock-key-123"):
        with patch("app.services.google_places_service.search_lodging", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = mock_external
            
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.get("/api/hotels?city=Agra")
                assert response.status_code == 200
                hotels = response.json()["data"]
                # There should be exactly 1 Oberoi Amarvilas (canonical)
                oberoi_entries = [h for h in hotels if h["name"] == "The Oberoi Amarvilas"]
                assert len(oberoi_entries) == 1
                assert oberoi_entries[0]["source"] == "canonical"


@pytest.mark.asyncio
async def test_external_provider_failure_resilience():
    """Verify provider exception does not crash the backend and returns canonical results."""
    with patch("app.core.config.settings.google_maps_api_key", "mock-key-123"):
        with patch("app.services.google_places_service.search_lodging", side_effect=Exception("Google API Timeout")):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.get("/api/hotels?city=Goa")
                assert response.status_code == 200
                hotels = response.json()["data"]
                assert len(hotels) >= 3


@pytest.mark.asyncio
async def test_api_key_not_exposed_in_hotel_responses():
    """Verify backend API key is never leaked in hotel payloads."""
    with patch("app.core.config.settings.google_maps_api_key", "secret-super-key-XYZ"):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/api/hotels")
            assert response.status_code == 200
            assert "secret-super-key-XYZ" not in response.text
