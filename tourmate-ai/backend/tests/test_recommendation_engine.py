"""
Phase 3 Recommendation Engine Test Suite.
Verifies all 23+ operational requirements against real PostgreSQL + pgvector:
1. Query embedding = 384 dimensions.
2. Query embedding is normalized (L2 norm ≈ 1.0).
3. Canonical embedding text is deterministic.
4. pgvector cosine ordering works in PostgreSQL.
5. Semantic ranking works.
6. Inactive POIs excluded.
7. NULL embeddings excluded.
8. Candidate limit enforced.
9. Destination filtering works.
10. Budget filtering works.
11. One-day behavior (bypasses KMeans).
12. Multi-day KMeans behavior.
13. Candidate count < requested days.
14. Distinct-coordinate count < requested days.
15. Duplicate coordinates handled safely.
16. Empty results handled cleanly.
17. Opening hours using actual calendar start_date.
18. Friday Taj Mahal closure behavior verified.
19. Deterministic KMeans results across runs.
20. Authenticated personalized recommendation.
21. Missing-interest fallback query.
22. POST /api/places/recommendations/plan contract.
23. GET /api/places/recommendations contract.
"""
import math
import uuid
from datetime import date, datetime, timezone
import numpy as np
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import AsyncSessionLocal
from app.main import app
from app.models.sql.category import Category
from app.models.sql.location import Location
from app.models.sql.poi import POI, OpeningHours
from app.models.sql.user import Preference, User, UserInterest
from app.schemas.recommendation import (
    RecommendationPlanRequest,
    RecommendationPlanResponse,
)
from app.services.auth_service import create_access_token
from app.services.embedding_service import get_embedding
from app.services.recommendation_service import (
    _sync_kmeans,
    construct_poi_embedding_text,
    construct_recommendation_query_text,
    date_to_db_day_of_week,
    get_personalized_recommendations,
    plan_trip_recommendations,
)


@pytest.fixture(scope="module")
def sync_engine():
    engine = create_engine(settings.sync_database_url)
    yield engine
    engine.dispose()


@pytest.fixture
async def db_session():
    async with AsyncSessionLocal() as session:
        yield session


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


# --------------------------------------------------------------------------
# 1. Query Embedding Dimension = 384
# --------------------------------------------------------------------------
def test_query_embedding_dimension():
    vec = get_embedding("Agra Historical Mughal Architecture")
    assert isinstance(vec, list)
    assert len(vec) == 384, f"Expected 384 dimensions, got {len(vec)}"


# --------------------------------------------------------------------------
# 2. Query Embedding Normalized (L2 norm ≈ 1.0)
# --------------------------------------------------------------------------
def test_query_embedding_is_normalized():
    vec = get_embedding("Agra Heritage Taj Mahal Monuments")
    norm = math.sqrt(sum(x * x for x in vec))
    assert abs(norm - 1.0) < 1e-4, f"Vector is not unit normalized: L2 norm = {norm}"


# --------------------------------------------------------------------------
# 3. Canonical Query-Text Construction is Deterministic
# --------------------------------------------------------------------------
def test_canonical_query_text_deterministic():
    text1 = construct_recommendation_query_text(
        destination="Agra",
        interests=["Architecture", "History"],
        travel_style="cultural",
        weights={"Architecture": 2.0, "History": 1.0},
    )
    text2 = construct_recommendation_query_text(
        destination="Agra",
        interests=["Architecture", "History"],
        travel_style="cultural",
        weights={"Architecture": 2.0, "History": 1.0},
    )
    assert text1 == text2
    assert "Agra" in text1
    assert "Architecture Architecture" in text1
    assert "History" in text1
    assert "cultural" in text1

    poi_text = construct_poi_embedding_text("Taj Mahal", "History", "Iconic white marble mausoleum")
    assert poi_text == "Taj Mahal History Iconic white marble mausoleum"


# --------------------------------------------------------------------------
# 4. PostgreSQL pgvector Cosine Distance Ordering Works
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_pgvector_cosine_ordering(db_session: AsyncSession):
    query_vec = get_embedding("Taj Mahal marble dome monument in Agra")
    stmt = (
        select(POI.name, POI.embedding.cosine_distance(query_vec).label("distance"))
        .where(POI.is_active.is_(True), POI.embedding.is_not(None))
        .order_by("distance")
        .limit(3)
    )
    res = (await db_session.execute(stmt)).all()
    assert len(res) >= 1
    top_poi_name, top_distance = res[0]
    assert "Taj Mahal" in top_poi_name
    assert top_distance < 0.5, f"Expected close distance for Taj Mahal, got {top_distance}"


# --------------------------------------------------------------------------
# 5. Semantic Ranking Works (Architecture vs Nature)
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_semantic_ranking_nature_vs_history(db_session: AsyncSession):
    # Search for nature/parks
    nature_vec = get_embedding("nature parks green gardens trees scenic outdoors")
    stmt = (
        select(POI.name)
        .where(POI.is_active.is_(True), POI.embedding.is_not(None))
        .order_by(POI.embedding.cosine_distance(nature_vec))
        .limit(1)
    )
    top_nature = (await db_session.execute(stmt)).scalar_one()
    assert ("Lodhi Garden" in top_nature) or ("Mehtab Bagh" in top_nature)

    # Search for Mughal architecture
    mughal_vec = get_embedding("Mughal architecture mausoleum emperor Agra")
    stmt = (
        select(POI.name)
        .where(POI.is_active.is_(True), POI.embedding.is_not(None))
        .order_by(POI.embedding.cosine_distance(mughal_vec))
        .limit(1)
    )
    top_mughal = (await db_session.execute(stmt)).scalar_one()
    assert ("Taj Mahal" in top_mughal) or ("Agra Fort" in top_mughal) or ("Itmad-ud-Daulah" in top_mughal)


# --------------------------------------------------------------------------
# 6. Inactive POIs Excluded
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_inactive_pois_excluded(db_session: AsyncSession):
    # Temporarily insert an inactive POI
    loc_id = (await db_session.execute(select(Location.id).limit(1))).scalar_one()
    cat_id = (await db_session.execute(select(Category.id).limit(1))).scalar_one()
    dummy_id = uuid.uuid4()

    dummy_vec = get_embedding("Super Secret Hidden Inactive Monument")
    inactive_poi = POI(
        id=dummy_id,
        location_id=loc_id,
        category_id=cat_id,
        name="ZZZ Inactive Ghost Attraction",
        description="Ghost",
        rating=5.0,
        price_tier=1,
        typical_visit_duration_minutes=60,
        is_active=False,
        embedding=dummy_vec,
    )
    db_session.add(inactive_poi)
    await db_session.commit()

    try:
        req = RecommendationPlanRequest(
            destination="Agra",
            start_date=date(2026, 10, 5),
            days=2,
            interests=["History"],
            max_candidates=50,
        )
        plan = await plan_trip_recommendations(req, db=db_session)
        for cluster in plan.clusters:
            for p in cluster.places:
                assert p.name != "ZZZ Inactive Ghost Attraction"
    finally:
        await db_session.execute(text(f"DELETE FROM pois WHERE id = '{dummy_id}';"))
        await db_session.commit()


# --------------------------------------------------------------------------
# 7. NULL Embeddings Excluded
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_null_embeddings_excluded(db_session: AsyncSession):
    loc_id = (await db_session.execute(select(Location.id).limit(1))).scalar_one()
    cat_id = (await db_session.execute(select(Category.id).limit(1))).scalar_one()
    dummy_id = uuid.uuid4()

    no_emb_poi = POI(
        id=dummy_id,
        location_id=loc_id,
        category_id=cat_id,
        name="ZZZ Null Embedding Attraction",
        description="No vector",
        rating=5.0,
        price_tier=1,
        typical_visit_duration_minutes=60,
        is_active=True,
        embedding=None,
    )
    db_session.add(no_emb_poi)
    await db_session.commit()

    try:
        req = RecommendationPlanRequest(
            destination="Agra",
            start_date=date(2026, 10, 5),
            days=2,
            interests=["History"],
            max_candidates=50,
        )
        plan = await plan_trip_recommendations(req, db=db_session)
        for cluster in plan.clusters:
            for p in cluster.places:
                assert p.name != "ZZZ Null Embedding Attraction"
    finally:
        await db_session.execute(text(f"DELETE FROM pois WHERE id = '{dummy_id}';"))
        await db_session.commit()


# --------------------------------------------------------------------------
# 8. Candidate Limit Enforced (Bounded <= 50)
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_candidate_limit_enforced(db_session: AsyncSession):
    req = RecommendationPlanRequest(
        destination="Agra",
        start_date=date(2026, 10, 5),
        days=2,
        max_candidates=3,
    )
    plan = await plan_trip_recommendations(req, db=db_session)
    total_assigned = sum(len(c.places) for c in plan.clusters)
    assert total_assigned <= 3
    assert plan.total_candidates <= 3


# --------------------------------------------------------------------------
# 9. Destination Filtering Works
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_destination_filtering(db_session: AsyncSession):
    req = RecommendationPlanRequest(
        destination="Jaipur",
        start_date=date(2026, 10, 5),
        days=2,
        max_candidates=10,
    )
    plan = await plan_trip_recommendations(req, db=db_session)
    assert plan.total_candidates > 0
    # In Jaipur, we should have Amber Palace, Hawa Mahal, City Palace, Jantar Mantar
    for cluster in plan.clusters:
        for p in cluster.places:
            assert p.name != "Taj Mahal"
            assert p.name != "Mehtab Bagh"


# --------------------------------------------------------------------------
# 10. Budget Filtering Works
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_budget_filtering(db_session: AsyncSession):
    # Budget tier: price_tier <= 2
    req = RecommendationPlanRequest(
        destination="Agra",
        start_date=date(2026, 10, 5),
        days=2,
        budget="budget",
        max_candidates=20,
    )
    plan = await plan_trip_recommendations(req, db=db_session)
    for cluster in plan.clusters:
        for p in cluster.places:
            assert p.price_level <= 2, f"{p.name} exceeds budget tier: {p.price_level}"


# --------------------------------------------------------------------------
# 11. One-Day Behavior (Bypasses KMeans)
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_one_day_behavior_bypasses_kmeans(db_session: AsyncSession):
    req = RecommendationPlanRequest(
        destination="Agra",
        start_date=date(2026, 10, 5),
        days=1,
        max_candidates=5,
    )
    plan = await plan_trip_recommendations(req, db=db_session)
    assert plan.total_days == 1
    assert len(plan.clusters) == 1
    assert len(plan.clusters[0].places) > 0
    assert plan.clusters[0].day == 1
    assert plan.clusters[0].date == "2026-10-05"


# --------------------------------------------------------------------------
# 12. Multi-Day KMeans Behavior
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_multi_day_kmeans_behavior(db_session: AsyncSession):
    req = RecommendationPlanRequest(
        destination="Agra",
        start_date=date(2026, 10, 5),
        days=3,
        max_candidates=10,
    )
    plan = await plan_trip_recommendations(req, db=db_session)
    assert plan.total_days == 3
    assert len(plan.clusters) == 3
    dates = [c.date for c in plan.clusters]
    assert dates == ["2026-10-05", "2026-10-06", "2026-10-07"]


# --------------------------------------------------------------------------
# 13. Candidate Count < Requested Days
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_candidate_count_less_than_requested_days(db_session: AsyncSession):
    req = RecommendationPlanRequest(
        destination="Agra",
        start_date=date(2026, 10, 5),
        days=5,
        max_candidates=2,  # Only 2 candidates requested for 5 days
    )
    plan = await plan_trip_recommendations(req, db=db_session)
    assert plan.total_days == 5
    assert len(plan.clusters) == 5
    # First 2 days should have places, later days should be empty with warning
    assert len(plan.clusters[0].places) >= 1
    assert len(plan.clusters[1].places) >= 1
    assert len(plan.clusters[2].places) == 0
    assert any("No remaining distinct attractions" in w for w in plan.clusters[2].warnings)


# --------------------------------------------------------------------------
# 14. Distinct-Coordinate Count < Requested Days Safety
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_distinct_coordinate_count_safety():
    # Coords with duplicate points (only 2 distinct coordinates for 4 requested days)
    coords = [[27.175, 78.042], [27.175, 78.042], [26.912, 75.787], [26.912, 75.787]]
    distinct_count = len({(round(lat, 5), round(lng, 5)) for lat, lng in coords})
    assert distinct_count == 2
    requested_days = 4
    effective_k = min(requested_days, len(coords), distinct_count)
    assert effective_k == 2

    # Should safely compute KMeans with k=2 without throwing ValueError
    labels, centroids = _sync_kmeans(coords, effective_k)
    assert len(labels) == 4
    assert len(centroids) == 2


# --------------------------------------------------------------------------
# 15. Duplicate Coordinates Handled Safely in Database
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_duplicate_coordinates_handled(db_session: AsyncSession):
    loc_id = (await db_session.execute(select(Location.id).limit(1))).scalar_one()
    cat_id = (await db_session.execute(select(Category.id).limit(1))).scalar_one()
    id1, id2 = uuid.uuid4(), uuid.uuid4()

    dummy_vec = get_embedding("Duplicate Coordinate Test Attraction")
    poi1 = POI(
        id=id1,
        location_id=loc_id,
        category_id=cat_id,
        name="Duplicate Coord A",
        description="A",
        rating=4.5,
        price_tier=1,
        typical_visit_duration_minutes=60,
        is_active=True,
        embedding=dummy_vec,
    )
    poi2 = POI(
        id=id2,
        location_id=loc_id,
        category_id=cat_id,
        name="Duplicate Coord B",
        description="B",
        rating=4.5,
        price_tier=1,
        typical_visit_duration_minutes=60,
        is_active=True,
        embedding=dummy_vec,
    )
    db_session.add_all([poi1, poi2])
    await db_session.commit()

    try:
        req = RecommendationPlanRequest(
            destination="Agra",
            start_date=date(2026, 10, 5),
            days=3,
            max_candidates=10,
        )
        plan = await plan_trip_recommendations(req, db=db_session)
        assert len(plan.clusters) == 3
    finally:
        await db_session.execute(text(f"DELETE FROM pois WHERE id IN ('{id1}', '{id2}');"))
        await db_session.commit()


# --------------------------------------------------------------------------
# 16. Empty Results
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_empty_results_handling(db_session: AsyncSession):
    req = RecommendationPlanRequest(
        destination="NonexistentAtlantisCity12345",
        start_date=date(2026, 10, 5),
        days=2,
    )
    plan = await plan_trip_recommendations(req, db=db_session)
    assert plan.total_candidates == 0
    assert plan.clusters == []
    assert "No attractions matched" in (plan.message or "")


# --------------------------------------------------------------------------
# 17. Opening Hours Using Actual Start Date
# --------------------------------------------------------------------------
def test_date_to_db_day_of_week():
    # 2026-10-02 is a Friday
    friday = date(2026, 10, 2)
    assert friday.weekday() == 4  # Python Monday=0 .. Friday=4
    db_dow = date_to_db_day_of_week(friday)
    assert db_dow == 5  # DB Sunday=0, Monday=1 .. Friday=5

    # 2026-10-04 is a Sunday
    sunday = date(2026, 10, 4)
    assert sunday.weekday() == 6  # Python Sunday=6
    db_dow_sun = date_to_db_day_of_week(sunday)
    assert db_dow_sun == 0  # DB Sunday=0


# --------------------------------------------------------------------------
# 18. Friday Taj Mahal Closure Warning
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_friday_taj_mahal_closure_behavior(db_session: AsyncSession):
    # 2026-10-02 is Friday (Taj Mahal is closed every Friday for prayers)
    friday_req = RecommendationPlanRequest(
        destination="Agra",
        start_date=date(2026, 10, 2),
        days=1,
        interests=["History"],
        max_candidates=5,
    )
    plan = await plan_trip_recommendations(friday_req, db=db_session)
    assert len(plan.clusters) == 1
    cluster = plan.clusters[0]
    assert cluster.day_of_week_name == "Friday"

    # Find Taj Mahal in places
    taj = next((p for p in cluster.places if "Taj Mahal" in p.name), None)
    assert taj is not None
    assert taj.opening_status is not None
    assert taj.opening_status.is_closed is True
    assert any("Taj Mahal is closed on Friday" in w for w in cluster.warnings)


# --------------------------------------------------------------------------
# 19. Deterministic KMeans Results Across Runs
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_deterministic_kmeans_results(db_session: AsyncSession):
    req = RecommendationPlanRequest(
        destination="Agra",
        start_date=date(2026, 10, 5),
        days=2,
        interests=["Architecture", "History"],
        max_candidates=8,
    )
    plan1 = await plan_trip_recommendations(req, db=db_session)
    plan2 = await plan_trip_recommendations(req, db=db_session)

    names1 = [[p.name for p in c.places] for c in plan1.clusters]
    names2 = [[p.name for p in c.places] for c in plan2.clusters]
    assert names1 == names2


# --------------------------------------------------------------------------
# 20. Authenticated Personalized Recommendation
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_authenticated_personalized_recommendation(db_session: AsyncSession):
    # Create test user with preferences in DB
    user_id = uuid.uuid4()
    cat_nature = (
        await db_session.execute(select(Category).where(Category.name == "Nature"))
    ).scalar_one()

    test_user = User(
        id=user_id,
        email=f"tester_{user_id.hex[:8]}@example.com",
        password_hash="fake_hash",
        name="Nature Lover",
        is_active=True,
    )
    db_session.add(test_user)
    await db_session.flush()

    interest = UserInterest(
        user_id=user_id,
        category_id=cat_nature.id,
        weight=3.0,
    )
    pref = Preference(
        user_id=user_id,
        budget_tier="moderate",
        travel_style="nature and wilderness explorer",
    )
    db_session.add_all([interest, pref])
    await db_session.commit()

    try:
        recs = await get_personalized_recommendations(
            user_id=str(user_id),
            limit=5,
            db=db_session,
        )
        assert len(recs) >= 1
        # Top recommendation should include a nature POI
        names = [r.name for r in recs]
        assert any(("Lodhi Garden" in n) or ("Mehtab Bagh" in n) for n in names)
    finally:
        await db_session.execute(text(f"DELETE FROM user_interests WHERE user_id = '{user_id}';"))
        await db_session.execute(text(f"DELETE FROM preferences WHERE user_id = '{user_id}';"))
        await db_session.execute(text(f"DELETE FROM users WHERE id = '{user_id}';"))
        await db_session.commit()


# --------------------------------------------------------------------------
# 21. Missing-Interest Fallback Query
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_missing_interest_fallback(db_session: AsyncSession):
    # No user_id, no destination, no interests -> general tourism query
    recs = await get_personalized_recommendations(
        user_id=None,
        destination=None,
        limit=5,
        db=db_session,
    )
    assert len(recs) == 5
    for r in recs:
        assert r.id is not None
        assert r.name is not None
        assert r.rating > 0


# --------------------------------------------------------------------------
# 22. POST /api/places/recommendations/plan Contract
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_plan_endpoint_contract(client: AsyncClient, db_session: AsyncSession):
    # Create valid user in DB for JWT
    test_uid = uuid.uuid4()
    test_user = User(
        id=test_uid,
        email=f"plan_{test_uid.hex[:8]}@example.com",
        name="Plan Tester",
        password_hash="fake_hash",
        role="user",
        is_active=True,
    )
    db_session.add(test_user)
    await db_session.commit()

    token = create_access_token(str(test_uid))

    payload = {
        "destination": "Agra",
        "start_date": "2026-10-05",
        "days": 2,
        "budget": "moderate",
        "interests": ["Architecture", "History"],
        "max_candidates": 8,
    }

    try:
        response = await client.post(
            "/api/places/recommendations/plan",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        plan_data = data["data"]
        assert plan_data["destination"] == "Agra"
        assert plan_data["start_date"] == "2026-10-05"
        assert plan_data["total_days"] == 2
        assert len(plan_data["clusters"]) == 2

        # Check day 1
        d1 = plan_data["clusters"][0]
        assert d1["day"] == 1
        assert d1["date"] == "2026-10-05"
        assert len(d1["centroid"]) == 2
        assert isinstance(d1["places"], list)
        assert isinstance(d1["total_visit_duration_minutes"], int)
    finally:
        await db_session.execute(text(f"DELETE FROM users WHERE id = '{test_uid}';"))
        await db_session.commit()


# --------------------------------------------------------------------------
# 23. Existing GET /api/places/recommendations Contract
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_recommendations_contract(client: AsyncClient, db_session: AsyncSession):
    test_uid = uuid.uuid4()
    test_user = User(
        id=test_uid,
        email=f"get_rec_{test_uid.hex[:8]}@example.com",
        name="Get Rec Tester",
        password_hash="fake_hash",
        role="user",
        is_active=True,
    )
    db_session.add(test_user)
    await db_session.commit()

    token = create_access_token(str(test_uid))

    try:
        response = await client.get(
            "/api/places/recommendations?destination=Agra&limit=5",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert len(data["data"]) <= 5
        for item in data["data"]:
            assert "id" in item
            assert "name" in item
            assert "category_id" in item
            assert "location" in item
            assert item["location"]["type"] == "Point"
    finally:
        await db_session.execute(text(f"DELETE FROM users WHERE id = '{test_uid}';"))
        await db_session.commit()
