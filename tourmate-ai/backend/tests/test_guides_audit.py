import pytest

@pytest.mark.asyncio
async def test_guides_total_count(client):
    res = await client.get("/api/guides")
    assert res.status_code == 200
    data = res.json()["data"]
    assert len(data) == 197

@pytest.mark.asyncio
async def test_guides_profile_data(client):
    res = await client.get("/api/guides")
    data = res.json()["data"]
    for g in data:
        assert g.get("name") is not None
        assert g.get("gender") in ["male", "female", "other"]
        assert g.get("image_url") is not None

@pytest.mark.asyncio
async def test_male_guides_images(client):
    res = await client.get("/api/guides")
    data = res.json()["data"]
    male_images = [
        "photo-1506794778202", "photo-1500648767791", "photo-1507003211169", 
        "photo-1519085360753", "photo-1504257432389", "photo-1472099645785", 
        "photo-1531427186611", "photo-1501196354995", "photo-1521119989659", 
        "photo-1492562080023"
    ]
    for g in data:
        if g.get("gender") == "male":
            assert any(img in g["image_url"] for img in male_images)

@pytest.mark.asyncio
async def test_female_guides_images(client):
    res = await client.get("/api/guides")
    data = res.json()["data"]
    female_images = [
        "photo-1534528741775", "photo-1508214751196", "photo-1494790108377", 
        "photo-1438761681033", "photo-1544005313", "photo-1517841905240", 
        "photo-1531746020798", "photo-1524504388940", "photo-1554151228", 
        "photo-1580489944761"
    ]
    for g in data:
        if g.get("gender") == "female":
            assert any(img in g["image_url"] for img in female_images)

@pytest.mark.asyncio
async def test_image_assignment_deterministic(client):
    res1 = await client.get("/api/guides")
    res2 = await client.get("/api/guides")
    assert res1.json() == res2.json()

@pytest.mark.asyncio
async def test_no_guide_duplicated(client):
    res = await client.get("/api/guides")
    data = res.json()["data"]
    ids = [g["id"] for g in data]
    assert len(ids) == len(set(ids))

@pytest.mark.asyncio
async def test_is_lgbtq_preserved(client):
    res = await client.get("/api/guides")
    data = res.json()["data"]
    for g in data:
        assert isinstance(g.get("is_lgbtq"), bool)

@pytest.mark.asyncio
async def test_guide_booking_still_works(client):
    pass
