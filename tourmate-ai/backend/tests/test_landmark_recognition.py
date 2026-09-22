import io
import json
import pytest
from unittest.mock import patch, MagicMock
from httpx import AsyncClient, ASGITransport
from PIL import Image
from app.main import app


def _create_dummy_image(color="blue", format="JPEG", size=(100, 100)) -> bytes:
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()


@pytest.mark.asyncio
async def test_landmark_recognition_canonical_grounding():
    """
    Test A: Image identified as Taj Mahal by Vision model
    Expected: Grounded against canonical TourMate POI in Agra, returning poi_id and canonical details.
    """
    fake_gemini_response = json.dumps({
        "is_landmark": True,
        "name": "Taj Mahal",
        "location": "Agra, Uttar Pradesh",
        "category": "Mausoleum / Heritage Site",
        "confidence": "High",
        "description": "An iconic ivory-white marble mausoleum on the right bank of the river Yamuna in Agra."
    })

    mock_model = MagicMock()
    mock_res = MagicMock()
    mock_res.text = fake_gemini_response
    mock_model.generate_content.return_value = mock_res

    image_bytes = _create_dummy_image()

    with patch("app.core.config.settings.gemini_api_key", "test-mock-key"), \
         patch("google.generativeai.GenerativeModel", return_value=mock_model):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            files = {"file": ("taj_mahal.jpg", image_bytes, "image/jpeg")}
            response = await ac.post("/api/ai/recognize-landmark", files=files)

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            res_data = data["data"]

            assert res_data["is_landmark"] is True
            assert "Taj Mahal" in res_data["name"]
            assert res_data["confidence"] == "High"
            assert res_data["is_grounded"] is True
            assert res_data["poi_id"] is not None
            assert "Agra" in res_data["location"]


@pytest.mark.asyncio
async def test_landmark_recognition_uncataloged_landmark_no_hallucination():
    """
    Test B: Image identified as Vidhana Soudha by Vision model.
    Expected: Recognized as Vidhana Soudha in Bengaluru, but honestly marked is_grounded=False
    and not mapped to a fake or generic 'palace' POI.
    """
    fake_gemini_response = json.dumps({
        "is_landmark": True,
        "name": "Vidhana Soudha",
        "location": "Bengaluru, Karnataka",
        "category": "Landmark / State Legislature",
        "confidence": "High",
        "description": "Seat of the state legislature of Karnataka in Bangalore, built in Neo-Dravidian style."
    })

    mock_model = MagicMock()
    mock_res = MagicMock()
    mock_res.text = fake_gemini_response
    mock_model.generate_content.return_value = mock_res

    image_bytes = _create_dummy_image()

    with patch("app.core.config.settings.gemini_api_key", "test-mock-key"), \
         patch("google.generativeai.GenerativeModel", return_value=mock_model):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            files = {"file": ("vidhana_soudha.jpg", image_bytes, "image/jpeg")}
            response = await ac.post("/api/ai/recognize-landmark", files=files)

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            res_data = data["data"]

            assert res_data["is_landmark"] is True
            assert res_data["name"] == "Vidhana Soudha"
            assert res_data["is_grounded"] is False
            assert res_data["poi_id"] is None
            assert "TourMate does not currently have this landmark in its verified POI database" in res_data["description"]


@pytest.mark.asyncio
async def test_landmark_recognition_non_landmark_object():
    """
    Test C: Image of everyday object (e.g. coffee cup or sneaker)
    Expected: is_landmark=False, confidence='None', clean message without hallucinated POI.
    """
    fake_gemini_response = json.dumps({
        "is_landmark": False,
        "name": "Unrecognized Landmark",
        "location": "",
        "category": "Non-Landmark",
        "confidence": "None",
        "description": "Unable to identify a recognized landmark or tourist attraction in this image."
    })

    mock_model = MagicMock()
    mock_res = MagicMock()
    mock_res.text = fake_gemini_response
    mock_model.generate_content.return_value = mock_res

    image_bytes = _create_dummy_image()

    with patch("app.core.config.settings.gemini_api_key", "test-mock-key"), \
         patch("google.generativeai.GenerativeModel", return_value=mock_model):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            files = {"file": ("coffee_cup.jpg", image_bytes, "image/jpeg")}
            response = await ac.post("/api/ai/recognize-landmark", files=files)

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            res_data = data["data"]

            assert res_data["is_landmark"] is False
            assert res_data["confidence"] == "None"
            assert res_data["is_grounded"] is False
            assert "Unable to identify" in res_data["description"]


@pytest.mark.asyncio
async def test_landmark_recognition_invalid_image_bytes():
    """
    Test D: Corrupt/non-image bytes uploaded.
    Expected: Handled safely with validation notice, no 500 crash.
    """
    corrupt_bytes = b"not a valid image byte stream"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        files = {"file": ("corrupt.jpg", corrupt_bytes, "image/jpeg")}
        response = await ac.post("/api/ai/recognize-landmark", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        res_data = data["data"]
        assert res_data["is_landmark"] is False
        assert res_data["name"] == "Invalid Image"


@pytest.mark.asyncio
async def test_landmark_recognition_empty_file():
    """
    Test E: Empty file upload.
    Expected: Rejected with 200 / Envelope(success=False, error=...)
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        files = {"file": ("empty.jpg", b"", "image/jpeg")}
        response = await ac.post("/api/ai/recognize-landmark", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "empty" in data["error"].lower()


@pytest.mark.asyncio
async def test_landmark_recognition_unsupported_mime():
    """
    Test F: Non-image MIME type (e.g. PDF or TXT).
    Expected: Rejected with clear validation error message.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        files = {"file": ("document.pdf", b"%PDF-1.4 ...", "application/pdf")}
        response = await ac.post("/api/ai/recognize-landmark", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "Unsupported image format" in data["error"]


@pytest.mark.asyncio
async def test_landmark_recognition_provider_failure_graceful_fallback():
    """
    Test G: Vision provider throws an exception / network error.
    Expected: Graceful handling returning unrecognized result without 500 crash.
    """
    mock_model = MagicMock()
    mock_model.generate_content.side_effect = RuntimeError("External Gemini timeout")

    image_bytes = _create_dummy_image()

    with patch("google.generativeai.GenerativeModel", return_value=mock_model):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            files = {"file": ("test_landmark.png", image_bytes, "image/png")}
            response = await ac.post("/api/ai/recognize-landmark", files=files)

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            res_data = data["data"]
            assert res_data["is_landmark"] is False
            assert res_data["confidence"] == "None"
