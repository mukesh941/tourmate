import pytest
import uuid
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch

from app.schemas.destination import DestinationCreate, DestinationUpdate
from app.schemas.place import TouristPlaceCreate, TouristPlaceUpdate
from app.models.sql.location import Location
from app.models.sql.poi import POI
from app.models.sql.category import Category
from app.services import destination_service, place_service


@pytest.mark.asyncio
async def test_destination_crud_service():
    """Verify destination_service create, update, delete, get with mock/live AsyncSession."""
    mock_session = AsyncMock()

    # 1. Create Destination
    payload = DestinationCreate(
        name="TestCityDestination",
        state="TestState",
        country="India",
        description="A beautiful test city in India",
        cover_image="https://example.com/test.jpg",
        popularity_score=4.8
    )

    # Mock no existing location
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = None
    mock_execute_res = MagicMock()
    mock_execute_res.scalars.return_value = mock_scalars
    mock_session.execute.return_value = mock_execute_res

    res = await destination_service.create_destination(payload, db=mock_session)
    assert res.name == "TestCityDestination"
    assert res.state == "TestState"
    assert res.country == "India"
    assert res.cover_image == "https://example.com/test.jpg"
    assert mock_session.commit.called
    assert mock_session.refresh.called

    # 2. Update Destination
    update_payload = DestinationUpdate(
        state="UpdatedState",
        description="Updated description"
    )
    existing_loc = Location(
        id=uuid.uuid4(),
        name="TestCityDestination",
        city="TestCityDestination",
        state="TestState",
        country="India",
        description="Old description",
        is_active=True
    )
    mock_session.scalar_one_or_none = MagicMock(return_value=existing_loc)
    mock_execute_res.scalar_one_or_none.return_value = existing_loc
    mock_execute_res.scalars.return_value.first.return_value = existing_loc

    updated_res = await destination_service.update_destination(str(existing_loc.id), update_payload, db=mock_session)
    assert updated_res is not None
    assert existing_loc.state == "UpdatedState"
    assert existing_loc.description == "Updated description"

    # 3. Delete Destination (Soft Delete)
    del_res = await destination_service.delete_destination(str(existing_loc.id), db=mock_session)
    assert del_res is True
    assert existing_loc.is_active is False


@pytest.mark.asyncio
async def test_place_crud_service():
    """Verify place_service create, update, delete with PostgreSQL models."""
    mock_session = AsyncMock()

    cat_id = uuid.uuid4()
    loc_id = uuid.uuid4()
    poi_id = uuid.uuid4()

    mock_cat = Category(id=cat_id, name="Sightseeing", slug="sightseeing")
    mock_loc = Location(id=loc_id, name="Agra", city="Agra", is_active=True)

    # Setup execute mocks for category and location resolution
    def mock_execute_side_effect(stmt):
        mock_res = MagicMock()
        stmt_str = str(stmt)
        if "categories" in stmt_str:
            mock_res.scalar_one_or_none.return_value = mock_cat
        elif "locations" in stmt_str:
            mock_res.scalar_one_or_none.return_value = mock_loc
            mock_scalars = MagicMock()
            mock_scalars.first.return_value = mock_loc
            mock_res.scalars.return_value = mock_scalars
        elif "pois" in stmt_str:
            created_poi = POI(
                id=poi_id,
                name="Taj Mahal Replica",
                description="Iconic monument",
                location_id=loc_id,
                category_id=cat_id,
                rating=4.9,
                price_tier=2,
                is_active=True
            )
            created_poi.location = mock_loc
            created_poi.category = mock_cat
            created_poi.poi_images = []
            mock_res.scalar_one_or_none.return_value = created_poi
        return mock_res

    mock_session.execute.side_effect = mock_execute_side_effect

    create_payload = TouristPlaceCreate(
        name="Taj Mahal Replica",
        destination_id=str(loc_id),
        category_id=str(cat_id),
        description="Iconic monument",
        price_level=2,
        rating=4.9,
        images=["https://example.com/taj.jpg"]
    )

    with patch("app.services.poi_service.get_poi_by_id") as mock_get_poi:
        from app.schemas.place import TouristPlaceResponse
        mock_get_poi.return_value = TouristPlaceResponse(
            id=str(poi_id),
            name="Taj Mahal Replica",
            destination_id=str(loc_id),
            category_id=str(cat_id),
            description="Iconic monument",
            price_level=2,
            rating=4.9,
            images=["https://example.com/taj.jpg"]
        )

        # 1. Create Place
        created_res = await place_service.create_place(create_payload, db=mock_session)
        assert created_res.id == str(poi_id)
        assert created_res.name == "Taj Mahal Replica"
        assert mock_session.commit.called

        # 2. Update Place
        update_payload = TouristPlaceUpdate(
            name="Taj Mahal Replica Updated",
            rating=5.0
        )
        updated_res = await place_service.update_place(str(poi_id), update_payload, db=mock_session)
        assert updated_res is not None

        # 3. Delete Place
        del_res = await place_service.delete_place(str(poi_id), db=mock_session)
        assert del_res is True
        assert mock_session.commit.called


@pytest.mark.asyncio
async def test_uuid_validation_and_rejection():
    """Verify that delete_place and update_place handle non-UUID gracefully without Mongo ObjectId errors."""
    mock_session = AsyncMock()

    # Invalid UUID string
    invalid_id = "non-existent-or-invalid-uuid"
    res_update = await place_service.update_place(invalid_id, TouristPlaceUpdate(name="Test"), db=mock_session)
    assert res_update is None

    res_del = await place_service.delete_place(invalid_id, db=mock_session)
    assert res_del is False


@pytest.mark.asyncio
async def test_admin_destination_endpoints(client: AsyncClient, admin_user):
    """Test POST, PUT, DELETE on /api/destinations with admin auth."""
    from app.main import app
    from app.api.deps import require_admin
    app.dependency_overrides[require_admin] = lambda: admin_user

    try:
        with patch("app.api.routes.destinations.create_destination") as mock_create, \
             patch("app.api.routes.destinations.update_destination") as mock_update, \
             patch("app.api.routes.destinations.delete_destination") as mock_del:

            from app.schemas.destination import DestinationResponse
            mock_dest = DestinationResponse(
                id="TestCity",
                name="TestCity",
                state="TestState",
                country="India",
                description="Test Description",
                cover_image="https://example.com/test.jpg",
                popularity_score=4.9
            )
            mock_create.return_value = mock_dest
            mock_update.return_value = mock_dest
            mock_del.return_value = True

            # 1. POST /api/destinations
            create_resp = await client.post(
                "/api/destinations",
                json={
                    "name": "TestCity",
                    "state": "TestState",
                    "country": "India",
                    "description": "Test Description",
                    "cover_image": "https://example.com/test.jpg",
                }
            )
            assert create_resp.status_code == 200
            assert create_resp.json()["data"]["name"] == "TestCity"

            # 2. PUT /api/destinations/TestCity
            update_resp = await client.put(
                "/api/destinations/TestCity",
                json={"description": "Updated Description"}
            )
            assert update_resp.status_code == 200
            assert update_resp.json()["data"]["name"] == "TestCity"

            # 3. DELETE /api/destinations/TestCity
            del_resp = await client.delete("/api/destinations/TestCity")
            assert del_resp.status_code == 200
            assert del_resp.json()["data"] is True
    finally:
        app.dependency_overrides.pop(require_admin, None)


@pytest.mark.asyncio
async def test_admin_place_endpoints(client: AsyncClient, admin_user):
    """Test POST, PUT, DELETE on /api/places with admin auth."""
    from app.main import app
    from app.api.deps import require_admin
    app.dependency_overrides[require_admin] = lambda: admin_user

    place_id = str(uuid.uuid4())
    try:
        with patch("app.api.routes.places.create_place") as mock_create, \
             patch("app.api.routes.places.update_place") as mock_update, \
             patch("app.api.routes.places.delete_place") as mock_del:

            from app.schemas.place import TouristPlaceResponse
            mock_place = TouristPlaceResponse(
                id=place_id,
                name="Test Monument",
                destination_id="Agra",
                category_id="sightseeing",
                description="Test Monument Description",
                price_level=2,
                rating=4.8,
                images=["https://example.com/monument.jpg"]
            )
            mock_create.return_value = mock_place
            mock_update.return_value = mock_place
            mock_del.return_value = True

            # 1. POST /api/places
            create_resp = await client.post(
                "/api/places",
                json={
                    "name": "Test Monument",
                    "destination_id": "Agra",
                    "category_id": "sightseeing",
                    "description": "Test Monument Description",
                    "price_level": 2,
                    "rating": 4.8,
                    "images": ["https://example.com/monument.jpg"]
                }
            )
            assert create_resp.status_code == 200
            assert create_resp.json()["data"]["id"] == place_id

            # 2. PUT /api/places/{place_id}
            update_resp = await client.put(
                f"/api/places/{place_id}",
                json={"name": "Test Monument Updated"}
            )
            assert update_resp.status_code == 200
            assert update_resp.json()["data"]["id"] == place_id

            # 3. DELETE /api/places/{place_id}
            del_resp = await client.delete(f"/api/places/{place_id}")
            assert del_resp.status_code == 200
            assert del_resp.json()["data"] is True
    finally:
        app.dependency_overrides.pop(require_admin, None)

