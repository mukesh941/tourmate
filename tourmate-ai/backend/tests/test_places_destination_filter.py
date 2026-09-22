import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_places_all_without_destination(client: AsyncClient):
    """1. /api/places without destination returns all active POIs."""
    response = await client.get("/api/places")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    places = data["data"]
    assert len(places) == 45


@pytest.mark.asyncio
async def test_get_places_goa_filter(client: AsyncClient):
    """2. Goa filter returns only Goa POIs (and both query param forms work)."""
    # Test with ?destination=goa
    res1 = await client.get("/api/places?destination=goa")
    assert res1.status_code == 200
    data1 = res1.json()["data"]
    assert len(data1) == 3
    names1 = {p["name"] for p in data1}
    assert names1 == {"Basilica of Bom Jesus", "Dudhsagar Falls", "Fort Aguada"}
    for p in data1:
        assert "Goa" in p["destination_id"]

    # Test with ?destination_id=Goa
    res2 = await client.get("/api/places?destination_id=Goa")
    assert res2.status_code == 200
    data2 = res2.json()["data"]
    assert len(data2) == 3
    assert {p["name"] for p in data2} == names1


@pytest.mark.asyncio
async def test_get_places_agra_filter(client: AsyncClient):
    """3. Agra filter returns only Agra POIs."""
    response = await client.get("/api/places?destination=Agra")
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 3
    names = {p["name"] for p in data}
    assert names == {"Taj Mahal", "Agra Fort", "Mehtab Bagh"}
    for p in data:
        assert p["destination_id"] == "Agra"


@pytest.mark.asyncio
async def test_get_places_jaipur_filter(client: AsyncClient):
    """4. Jaipur filter returns only Jaipur POIs."""
    response = await client.get("/api/places?destination=jaipur")
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 3
    names = {p["name"] for p in data}
    assert names == {"Amer Fort", "Jantar Mantar", "Hawa Mahal"}
    for p in data:
        assert p["destination_id"] == "Jaipur"


@pytest.mark.asyncio
async def test_get_places_mumbai_filter(client: AsyncClient):
    """5. Mumbai filter returns only Mumbai POIs."""
    response = await client.get("/api/places?destination=mumbai")
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 2
    names = {p["name"] for p in data}
    assert names == {"Chhatrapati Shivaji Terminus", "Gateway of India"}
    for p in data:
        assert p["destination_id"] == "Mumbai"


@pytest.mark.asyncio
async def test_get_places_new_delhi_filter(client: AsyncClient):
    """6. New Delhi filter returns only New Delhi POIs (including slug handling)."""
    # Test with exact city name
    res1 = await client.get("/api/places?destination=New Delhi")
    assert res1.status_code == 200
    data1 = res1.json()["data"]
    assert len(data1) == 4
    names1 = {p["name"] for p in data1}
    assert names1 == {"Humayun's Tomb", "Lodhi Garden", "Qutub Minar", "Red Fort"}

    # Test with slug
    res2 = await client.get("/api/places?destination=new-delhi")
    assert res2.status_code == 200
    data2 = res2.json()["data"]
    assert len(data2) == 4
    assert {p["name"] for p in data2} == names1


@pytest.mark.asyncio
async def test_get_places_unknown_destination(client: AsyncClient):
    """7. Unknown destination returns controlled empty result, NOT all POIs."""
    response = await client.get("/api/places?destination=AtlantisCityXYZ")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"] == []


@pytest.mark.asyncio
async def test_get_places_destination_plus_category(client: AsyncClient):
    """8. Destination + category works together without cross-destination leaks."""
    # First get categories to find Nature category ID or slug
    cat_res = await client.get("/api/categories")
    assert cat_res.status_code == 200
    categories = cat_res.json()["data"]
    nature_cat = next((c for c in categories if "nature" in c["name"].lower()), None)
    assert nature_cat is not None

    # In Goa, Dudhsagar Falls is Nature
    response = await client.get(f"/api/places?destination=Goa&category_id={nature_cat['id']}")
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) >= 1
    # Must only be Goa POIs
    for p in data:
        assert "Goa" in p["destination_id"]
        assert p["name"] == "Dudhsagar Falls"


@pytest.mark.asyncio
async def test_get_places_destination_plus_search(client: AsyncClient):
    """9. Destination + search works together."""
    # Search for "Fort" inside Goa
    res_goa = await client.get("/api/places?destination=Goa&q=fort")
    assert res_goa.status_code == 200
    data_goa = res_goa.json()["data"]
    assert len(data_goa) == 1
    assert data_goa[0]["name"] == "Fort Aguada"
    assert "Goa" in data_goa[0]["destination_id"]

    # Search for "Fort" inside Agra
    res_agra = await client.get("/api/places?destination=Agra&q=fort")
    assert res_agra.status_code == 200
    data_agra = res_agra.json()["data"]
    assert len(data_agra) == 1
    assert data_agra[0]["name"] == "Agra Fort"
    assert data_agra[0]["destination_id"] == "Agra"


@pytest.mark.asyncio
async def test_get_places_destination_category_search(client: AsyncClient):
    """10. Destination + category + search works together."""
    res = await client.get("/api/places?destination=Jaipur&category=history&q=Amer")
    assert res.status_code == 200
    data = res.json()["data"]
    assert len(data) == 1
    assert data[0]["name"] == "Amer Fort"
    assert data[0]["destination_id"] == "Jaipur"


@pytest.mark.asyncio
async def test_destination_isolation_no_cross_leakage(client: AsyncClient):
    """11 & 12. Strict destination isolation across all 15 supported destinations."""
    dest_res = await client.get("/api/destinations")
    assert dest_res.status_code == 200
    destinations = dest_res.json()["data"]
    assert len(destinations) >= 15

    for d in destinations:
        dest_name = d["name"]
        res = await client.get(f"/api/places?destination={dest_name}")
        assert res.status_code == 200
        places = res.json()["data"]
        assert len(places) > 0, f"Expected places for destination {dest_name}"
        for p in places:
            assert p["destination_id"].lower() == dest_name.lower(), (
                f"Cross destination leakage: POI '{p['name']}' with destination '{p['destination_id']}' "
                f"appeared under '{dest_name}'"
            )
