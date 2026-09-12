import pytest
from app.schemas.place import TouristPlaceResponse, FeatureScoresSchema, GeoJSONPointSchema
from app.services.ml_service import generate_place_clusters, get_knn_recommendations
from app.services.route_service import optimize_route, haversine


def create_mock_place(
    id: str,
    name: str,
    lat: float,
    lng: float,
    history: float = 0.0,
    nature: float = 0.0,
    culture: float = 0.0,
    adventure: float = 0.0,
    food: float = 0.0,
    shopping: float = 0.0,
    architecture: float = 0.0,
) -> TouristPlaceResponse:
    return TouristPlaceResponse(
        id=id,
        name=name,
        description=f"Description of {name}",
        destination_id="dest_india_1",
        category_id="cat_1",
        images=[],
        rating=4.5,
        location=GeoJSONPointSchema(type="Point", coordinates=[lng, lat]),
        feature_scores=FeatureScoresSchema(
            history=history,
            nature=nature,
            culture=culture,
            adventure=adventure,
            food=food,
            shopping=shopping,
            architecture=architecture,
        ),
        visit_duration_minutes=60,
    )


@pytest.mark.asyncio
async def test_kmeans_empty_places():
    res = await generate_place_clusters([], k=3)
    assert res == {"clusters": [], "centroids": []}


@pytest.mark.asyncio
async def test_kmeans_clustering():
    places = [
        # North cluster (e.g. Delhi)
        create_mock_place("p1", "Place Delhi 1", 28.6139, 77.2090),
        create_mock_place("p2", "Place Delhi 2", 28.6200, 77.2150),
        create_mock_place("p3", "Place Delhi 3", 28.6100, 77.2000),
        # South cluster (e.g. Bengaluru)
        create_mock_place("p4", "Place Blr 1", 12.9716, 77.5946),
        create_mock_place("p5", "Place Blr 2", 12.9750, 77.5980),
        create_mock_place("p6", "Place Blr 3", 12.9680, 77.5900),
    ]

    res = await generate_place_clusters(places, k=2)
    assert res["k"] == 2
    assert len(res["centroids"]) == 2
    assert len(res["clusters"]) == 2

    # Verify all 6 places are partitioned across clusters
    total_clustered = sum(len(c["places"]) for c in res["clusters"])
    assert total_clustered == 6


@pytest.mark.asyncio
async def test_knn_empty_places():
    res = await get_knn_recommendations([], ["history"], k=5)
    assert res == []


@pytest.mark.asyncio
async def test_knn_recommendations_ranking():
    # Historical place
    historical = create_mock_place("p_hist", "Taj Mahal", 27.1751, 78.0421, history=10.0, architecture=9.5)
    # Adventure/nature place
    nature = create_mock_place("p_nat", "Jim Corbett", 29.5300, 78.7747, nature=10.0, adventure=9.0)
    # Food/shopping place
    food = create_mock_place("p_food", "Chandni Chowk", 28.6506, 77.2303, food=10.0, shopping=9.0)

    places = [nature, food, historical]

    # User interested in history and architecture
    recs = await get_knn_recommendations(places, user_interests=["history", "architecture"], k=3)
    assert len(recs) == 3
    # Top recommendation should be the historical place
    assert recs[0].id == "p_hist"


def test_haversine_distance():
    # Distance between Delhi (28.6139, 77.2090) and Agra (27.1751, 78.0421) is ~180-200 km
    dist = haversine(28.6139, 77.2090, 27.1751, 78.0421)
    assert 170.0 < dist < 210.0


def test_route_optimization_single_place():
    p1 = create_mock_place("p1", "India Gate", 28.6129, 77.2295)
    opt_places, dist = optimize_route([p1])
    assert opt_places == [p1]
    assert dist == 0.0


def test_route_optimization_multiple_stops():
    # Three stops in Delhi
    p1 = create_mock_place("p1", "India Gate", 28.6129, 77.2295)
    p2 = create_mock_place("p2", "Red Fort", 28.6562, 77.2410)
    p3 = create_mock_place("p3", "Humayun's Tomb", 28.5933, 77.2507)

    # Scrambled input order
    input_places = [p1, p2, p3]
    opt_places, total_distance = optimize_route(input_places)

    assert len(opt_places) == 3
    assert opt_places[0].id == "p1"  # First stop is the origin
    assert total_distance > 0.0
    # Every place visited exactly once
    assert {p.id for p in opt_places} == {"p1", "p2", "p3"}


def test_astar_route_optimization():
    from app.services.route_service import astar_route_optimization, astar_search

    p1 = create_mock_place("p1", "India Gate", 28.6129, 77.2295)
    p2 = create_mock_place("p2", "Red Fort", 28.6562, 77.2410)
    p3 = create_mock_place("p3", "Humayun's Tomb", 28.5933, 77.2507)

    res = astar_route_optimization([p1, p2, p3])
    assert len(res["optimized_places"]) == 3
    assert res["total_distance_km"] > 0.0
    assert "A* Pathfinding" in res["algorithm_used"]
    assert "f(n) = g(n) + h(n)" in res["evaluation_function"]
    assert len(res["segments"]) == 2
    assert "from_name" in res["segments"][0]
    assert "estimated_time_mins" in res["segments"][0]

    # Test direct A* node search
    coords = [(28.6129, 77.2295), (28.6562, 77.2410), (28.5933, 77.2507)]
    path = astar_search(0, 2, coords, allowed_indices={1, 2})
    assert len(path) >= 2
    assert path[0] == 0
    assert path[-1] == 2


def test_sentiment_analysis():
    from app.services.sentiment_service import analyze_sentiment

    # Positive review
    pos_res = analyze_sentiment("The architecture is breathtaking and stunning, exceptionally peaceful experience!", 5)
    assert pos_res["sentiment_label"] == "Positive"
    assert pos_res["sentiment_score"] > 0.70
    assert pos_res["sentiment_emoji"] == "😊"

    # Negative review with negation
    neg_res = analyze_sentiment("Extremely dirty and overcrowded, rude staff and total scam!", 1)
    assert neg_res["sentiment_label"] == "Negative"
    assert neg_res["sentiment_emoji"] == "🙁"

    # Negated positive word -> negative
    not_good_res = analyze_sentiment("The place was not clean and not pleasant.", 2)
    assert not_good_res["sentiment_label"] in ["Negative", "Neutral"]
