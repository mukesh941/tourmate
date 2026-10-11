import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_itinerary_generate_days_1(client: AsyncClient):
    payload = {
        "destination_name": "Test",
        "days": 1,
        "travel_type": "Solo",
        "budget": "Medium",
        "energy_level": "Moderate"
    }
    res = await client.post("/api/itineraries/generate", json=payload)
    # Could be a 401 if unauthenticated, or 200, but shouldn't be 422
    assert res.status_code != 422

@pytest.mark.asyncio
async def test_itinerary_generate_days_7(client: AsyncClient):
    payload = {
        "destination_name": "Test",
        "days": 7,
        "travel_type": "Solo",
        "budget": "Medium",
        "energy_level": "Moderate"
    }
    res = await client.post("/api/itineraries/generate", json=payload)
    assert res.status_code != 422

@pytest.mark.asyncio
async def test_itinerary_generate_days_8(client: AsyncClient):
    payload = {
        "destination_name": "Test",
        "days": 8,
        "travel_type": "Solo",
        "budget": "Medium",
        "energy_level": "Moderate"
    }
    res = await client.post("/api/itineraries/generate", json=payload)
    assert res.status_code != 422

@pytest.mark.asyncio
async def test_itinerary_generate_days_14(client: AsyncClient):
    payload = {
        "destination_name": "Test",
        "days": 14,
        "travel_type": "Solo",
        "budget": "Medium",
        "energy_level": "Moderate"
    }
    res = await client.post("/api/itineraries/generate", json=payload)
    assert res.status_code != 422

@pytest.mark.asyncio
async def test_itinerary_generate_days_0(client: AsyncClient):
    payload = {
        "destination_name": "Test",
        "days": 0,
        "travel_type": "Solo",
        "budget": "Medium",
        "energy_level": "Moderate"
    }
    res = await client.post("/api/itineraries/generate", json=payload)
    assert res.status_code == 422  # validation error

@pytest.mark.asyncio
async def test_itinerary_generate_days_15(client: AsyncClient):
    payload = {
        "destination_name": "Test",
        "days": 15,
        "travel_type": "Solo",
        "budget": "Medium",
        "energy_level": "Moderate"
    }
    res = await client.post("/api/itineraries/generate", json=payload)
    assert res.status_code == 422  # validation error

@pytest.mark.asyncio
async def test_itinerary_actual_generation_14_days(client: AsyncClient):
    payload = {
        "destination_name": "Mumbai",
        "days": 14,
        "travel_type": "Solo",
        "budget": "Medium",
        "energy_level": "Moderate"
    }
    res = await client.post("/api/itineraries/generate", json=payload)
    assert res.status_code == 200
    data = res.json()["data"]
    
    # 7. Actual 14-day itinerary generation
    assert len(data) > 0
    itinerary_option = data[0]
    
    # 9. Correct number of itinerary days returned
    # 10. No hidden 7-day truncation
    schedule = itinerary_option["schedule"]
    assert len(schedule) == 14
    
    # 8. Budget calculation for 14 days
    # In ai_service.py fallback logic, cost is cost_per_day * num_days. 
    # Let's ensure it's greater than 0 and proportional (just sanity check)
    total_cost = itinerary_option["total_estimated_cost"]
    assert total_cost > 0
