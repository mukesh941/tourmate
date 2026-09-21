"""
Phase 4 Routing & Itinerary Optimization Comprehensive Test Suite.
Verifies all 22 required operational requirements against real PostgreSQL + pgvector:
1. OSRM adapter
2. retry behavior
3. provider failure
4. graph construction
5. directed edges
6. cheapest insertion
7. deterministic tie-breaking
8. anchored 2-opt
9. directed 2-opt correctness
10. A*
11. Dijkstra
12. A* cost == Dijkstra cost
13. heuristic admissibility
14. missing accommodation
15. closed POI
16. zero POI day
17. one POI day
18. multi-day isolation
19. alternative tour
20. PostgreSQL persistence
21. route anchor semantics
22. preserved /locations/route endpoint
"""
import asyncio
import math
import uuid
from datetime import date, datetime, time as dt_time, timedelta, timezone
from typing import Any, Dict, List
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.db import AsyncSessionLocal
from app.main import app
from app.models.sql.accommodation import Accommodation
from app.models.sql.category import Category
from app.models.sql.itinerary import AlternativeRoute, Itinerary, ItineraryStop, Route
from app.models.sql.location import Location
from app.models.sql.poi import OpeningHours, POI
from app.models.sql.trip import POICluster, Trip, TripAccommodation
from app.models.sql.user import User
from app.schemas.route_optimization import (
    DayClusterInput,
    ItineraryOptimizePlanRequest,
)
from app.services.auth_service import create_access_token
from app.services.graph_service import DirectedEdge, InternalRouteGraph, RouteNode, haversine
from app.services.itinerary_optimization_service import optimize_and_persist_itinerary
from app.services.osrm_service import (
    OSRM_CACHE,
    RoutingUnavailableError,
    calculate_route,
    get_directed_pairwise_matrix,
    get_osrm_directed_route,
)
from app.services.pathfinding_service import astar_shortest_path, dijkstra_shortest_path
from app.services.tsp_service import (
    anchored_cheapest_insertion,
    anchored_two_opt,
    calculate_tour_distance,
    calculate_tour_duration,
    get_alternative_tour,
    validate_tour_opening_hours,
)


@pytest.fixture
async def db_session():
    async with AsyncSessionLocal() as session:
        yield session


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture(autouse=True)
async def cleanup_test_records():
    yield
    async with AsyncSessionLocal() as session:
        from app.db.seeds.canonical_seed_data import PILOT_POIS, PILOT_ACCOMMODATIONS
        from app.db.seeds.canonical_expanded_data import EXPANDED_POIS, EXPANDED_ACCOMMODATIONS
        all_pois = PILOT_POIS + EXPANDED_POIS
        all_accs = PILOT_ACCOMMODATIONS + EXPANDED_ACCOMMODATIONS
        poi_ids = [f"'{p['id']}'" for p in all_pois]
        acc_ids = [f"'{a['id']}'" for a in all_accs]
        await session.execute(text("DELETE FROM alternative_routes;"))
        await session.execute(text("DELETE FROM routes;"))
        await session.execute(text("DELETE FROM itinerary_stops;"))
        await session.execute(text("DELETE FROM itineraries;"))
        await session.execute(text(f"DELETE FROM opening_hours WHERE poi_id NOT IN ({','.join(poi_ids)});"))
        await session.execute(text(f"DELETE FROM pois WHERE id NOT IN ({','.join(poi_ids)});"))
        await session.execute(text(f"DELETE FROM trip_accommodations WHERE accommodation_id NOT IN ({','.join(acc_ids)});"))
        await session.execute(text(f"DELETE FROM accommodations WHERE id NOT IN ({','.join(acc_ids)});"))
        await session.execute(text("DELETE FROM categories WHERE name NOT IN ('History', 'Nature', 'Culture', 'Adventure', 'Food', 'Shopping', 'Architecture');"))
        await session.commit()



# --------------------------------------------------------------------------
# 1. OSRM Adapter: Returns directed edges with real distance, duration, GeoJSON
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_osrm_adapter_authoritative_routing():
    u = RouteNode(id="A", name="Start", latitude=27.1751, longitude=78.0421)
    v = RouteNode(id="B", name="End", latitude=27.1795, longitude=78.0211)

    # Test with mock OSRM response to ensure deterministic schema validation
    mock_resp = {
        "code": "Ok",
        "routes": [
            {
                "distance": 3200.0,
                "duration": 480.0,
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[78.0421, 27.1751], [78.0211, 27.1795]],
                },
                "legs": [],
            }
        ],
    }

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = AsyncMock(status_code=200, json=lambda: mock_resp)
        edge = await get_osrm_directed_route(u, v, mode="driving")

        assert edge.from_id == "A"
        assert edge.to_id == "B"
        assert edge.road_distance_km == 3.2
        assert edge.road_duration_minutes == 8.0
        assert edge.geometry is not None
        assert edge.geometry["type"] == "LineString"
        assert edge.haversine_distance_km > 0.0


# --------------------------------------------------------------------------
# 2. Retry Behavior: 3 attempts with 0.5s, 1.0s, 2.0s backoff
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_osrm_retry_behavior():
    u = RouteNode(id="node_u", name="U", latitude=27.1, longitude=78.0)
    v = RouteNode(id="node_v", name="V", latitude=27.2, longitude=78.1)

    # Clear cache
    OSRM_CACHE.clear()

    call_count = 0

    async def flaky_get(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise Exception("Transient network timeout")
        return AsyncMock(
            status_code=200,
            json=lambda: {
                "code": "Ok",
                "routes": [
                    {
                        "distance": 15000.0,
                        "duration": 1200.0,
                        "geometry": {"type": "LineString", "coordinates": []},
                    }
                ],
            },
        )

    with patch("httpx.AsyncClient.get", side_effect=flaky_get):
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            edge = await get_osrm_directed_route(u, v, max_retries=3)
            assert call_count == 3
            assert edge.road_distance_km == 15.0
            # Backoff was called with 0.5 then 1.0
            assert mock_sleep.call_count == 2
            mock_sleep.assert_any_call(0.5)
            mock_sleep.assert_any_call(1.0)


# --------------------------------------------------------------------------
# 3. Provider Failure: Raises RoutingUnavailableError, NEVER fabricated fallback
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_osrm_provider_failure_no_fallback():
    u = RouteNode(id="fail_u", name="U", latitude=27.1, longitude=78.0)
    v = RouteNode(id="fail_v", name="V", latitude=27.2, longitude=78.1)

    OSRM_CACHE.clear()

    with patch("httpx.AsyncClient.get", side_effect=Exception("Connection refused")):
        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(RoutingUnavailableError) as exc_info:
                await get_osrm_directed_route(u, v, max_retries=3)
            assert "unavailable" in str(exc_info.value).lower()


# --------------------------------------------------------------------------
# 4. Graph Construction: Nodes, edges, heuristic
# --------------------------------------------------------------------------
def test_graph_construction():
    graph = InternalRouteGraph(v_max_kmh=80.0)
    n1 = RouteNode(id="A", name="Hotel", latitude=27.17, longitude=78.04, is_anchor=True)
    n2 = RouteNode(id="P1", name="Taj", latitude=27.18, longitude=78.02)
    graph.add_node(n1)
    graph.add_node(n2)

    e1 = DirectedEdge(from_id="A", to_id="P1", road_distance_km=4.0, road_duration_minutes=10.0)
    e2 = DirectedEdge(from_id="P1", to_id="A", road_distance_km=4.5, road_duration_minutes=12.0)
    graph.add_edge(e1)
    graph.add_edge(e2)

    assert graph.node_count == 2
    assert graph.edge_count == 2
    assert graph.has_edge("A", "P1")
    assert graph.has_edge("P1", "A")
    assert graph.get_edge("A", "P1").road_duration_minutes == 10.0
    assert graph.heuristic("A", "P1") > 0.0
    assert graph.heuristic("A", "A") == 0.0


# --------------------------------------------------------------------------
# 5. Directed Edges: Asymmetric Edge Costs
# --------------------------------------------------------------------------
def test_directed_edges_asymmetry():
    graph = InternalRouteGraph(v_max_kmh=100.0)
    graph.add_node(RouteNode(id="A", name="A", latitude=27.0, longitude=78.0))
    graph.add_node(RouteNode(id="B", name="B", latitude=27.1, longitude=78.1))

    # Real one-way system / traffic duration difference
    graph.add_edge(DirectedEdge(from_id="A", to_id="B", road_distance_km=5.0, road_duration_minutes=10.0))
    graph.add_edge(DirectedEdge(from_id="B", to_id="A", road_distance_km=7.5, road_duration_minutes=22.0))

    assert graph.get_edge("A", "B").road_duration_minutes == 10.0
    assert graph.get_edge("B", "A").road_duration_minutes == 22.0
    assert graph.get_edge("A", "B").road_distance_km != graph.get_edge("B", "A").road_distance_km


# --------------------------------------------------------------------------
# 6. Cheapest Insertion: Includes all POIs, starts and ends at accommodation
# --------------------------------------------------------------------------
def test_cheapest_insertion_completeness():
    graph = InternalRouteGraph(v_max_kmh=100.0)
    nodes = ["ACC", "P1", "P2", "P3"]
    for nid in nodes:
        graph.add_node(RouteNode(id=nid, name=nid, latitude=27.0 + hash(nid) % 10 * 0.01, longitude=78.0, is_anchor=(nid == "ACC")))

    # Fully connect
    for u in nodes:
        for v in nodes:
            if u != v:
                cost = 10.0 if (u, v) in [("ACC", "P1"), ("P1", "P2"), ("P2", "P3"), ("P3", "ACC")] else 25.0
                graph.add_edge(DirectedEdge(from_id=u, to_id=v, road_distance_km=cost, road_duration_minutes=cost))

    tour = anchored_cheapest_insertion(graph, "ACC", ["P1", "P2", "P3"])

    assert tour[0] == "ACC"
    assert tour[-1] == "ACC"
    assert set(tour[1:-1]) == {"P1", "P2", "P3"}
    assert len(tour) == 5  # ACC, 3 POIs, ACC


# --------------------------------------------------------------------------
# 7. Deterministic Tie-Breaking
# --------------------------------------------------------------------------
def test_cheapest_insertion_deterministic_tie_breaking():
    graph = InternalRouteGraph(v_max_kmh=100.0)
    pois = [str(uuid.uuid4()) for _ in range(4)]
    all_nodes = ["ACC"] + pois

    for nid in all_nodes:
        graph.add_node(RouteNode(id=nid, name=nid, latitude=27.0, longitude=78.0, is_anchor=(nid == "ACC")))

    # Symmetric uniform costs -> forces tie breaking on every insertion
    for u in all_nodes:
        for v in all_nodes:
            if u != v:
                graph.add_edge(DirectedEdge(from_id=u, to_id=v, road_distance_km=10.0, road_duration_minutes=10.0))

    tour1 = anchored_cheapest_insertion(graph, "ACC", list(reversed(pois)))
    tour2 = anchored_cheapest_insertion(graph, "ACC", list(pois))

    assert tour1 == tour2, "Cheapest insertion must be deterministic regardless of input list permutation"


# --------------------------------------------------------------------------
# 8. Anchored 2-opt: Optimized cost <= Initial cost, anchor fixed
# --------------------------------------------------------------------------
def test_anchored_two_opt_improvement():
    graph = InternalRouteGraph(v_max_kmh=100.0)
    nodes = ["ACC", "P1", "P2", "P3", "P4"]
    for nid in nodes:
        graph.add_node(RouteNode(id=nid, name=nid, latitude=27.0, longitude=78.0, is_anchor=(nid == "ACC")))

    # Setup matrix where reversing P3 and P2 gives huge improvement
    for u in nodes:
        for v in nodes:
            if u != v:
                graph.add_edge(DirectedEdge(from_id=u, to_id=v, road_distance_km=20.0, road_duration_minutes=20.0))

    # Substantially lower duration on the reversed path
    graph.edges[("P1", "P3")].road_duration_minutes = 2.0
    graph.edges[("P3", "P2")].road_duration_minutes = 2.0
    graph.edges[("P2", "P4")].road_duration_minutes = 2.0

    initial_tour = ["ACC", "P1", "P2", "P3", "P4", "ACC"]
    init_dur = calculate_tour_duration(graph, initial_tour)

    opt_tour = anchored_two_opt(graph, initial_tour)
    opt_dur = calculate_tour_duration(graph, opt_tour)

    assert opt_dur <= init_dur
    assert opt_tour[0] == "ACC"
    assert opt_tour[-1] == "ACC"
    assert set(opt_tour[1:-1]) == {"P1", "P2", "P3", "P4"}


# --------------------------------------------------------------------------
# 9. Directed 2-opt Correctness: Asymmetric penalties respected
# --------------------------------------------------------------------------
def test_directed_two_opt_asymmetry_respect():
    graph = InternalRouteGraph(v_max_kmh=100.0)
    nodes = ["ACC", "P1", "P2", "ACC"]
    for nid in set(nodes):
        graph.add_node(RouteNode(id=nid, name=nid, latitude=27.0, longitude=78.0, is_anchor=(nid == "ACC")))

    for u in set(nodes):
        for v in set(nodes):
            if u != v:
                graph.add_edge(DirectedEdge(from_id=u, to_id=v, road_distance_km=10.0, road_duration_minutes=10.0))

    # Forward: P1 -> P2 = 5 min. Backward: P2 -> P1 = 100 min (e.g. steep mountain one-way)
    graph.edges[("P1", "P2")].road_duration_minutes = 5.0
    graph.edges[("P2", "P1")].road_duration_minutes = 100.0

    initial_tour = ["ACC", "P1", "P2", "ACC"]
    # If 2-opt incorrectly assumed symmetry, it might reverse P1-P2. Directed 2-opt must NOT reverse this.
    opt_tour = anchored_two_opt(graph, initial_tour)
    assert opt_tour == ["ACC", "P1", "P2", "ACC"]


# --------------------------------------------------------------------------
# 10. A* Pathfinding
# --------------------------------------------------------------------------
def test_astar_pathfinding():
    graph = InternalRouteGraph(v_max_kmh=60.0)
    # 3 nodes in a line: A (lat 0, lon 0) -> B (lat 0.1, lon 0) -> C (lat 0.2, lon 0)
    graph.add_node(RouteNode(id="A", name="A", latitude=0.0, longitude=0.0))
    graph.add_node(RouteNode(id="B", name="B", latitude=0.1, longitude=0.0))
    graph.add_node(RouteNode(id="C", name="C", latitude=0.2, longitude=0.0))

    graph.add_edge(DirectedEdge(from_id="A", to_id="B", road_distance_km=11.1, road_duration_minutes=15.0))
    graph.add_edge(DirectedEdge(from_id="B", to_id="C", road_distance_km=11.1, road_duration_minutes=15.0))
    graph.add_edge(DirectedEdge(from_id="A", to_id="C", road_distance_km=22.2, road_duration_minutes=40.0))

    res = astar_shortest_path(graph, "A", "C")
    assert res.path == ["A", "B", "C"]
    assert res.total_cost == 30.0
    assert res.nodes_expanded >= 1
    assert res.execution_time_ms >= 0.0


# --------------------------------------------------------------------------
# 11. Dijkstra Pathfinding
# --------------------------------------------------------------------------
def test_dijkstra_pathfinding():
    graph = InternalRouteGraph(v_max_kmh=60.0)
    graph.add_node(RouteNode(id="A", name="A", latitude=0.0, longitude=0.0))
    graph.add_node(RouteNode(id="B", name="B", latitude=0.1, longitude=0.0))
    graph.add_node(RouteNode(id="C", name="C", latitude=0.2, longitude=0.0))

    graph.add_edge(DirectedEdge(from_id="A", to_id="B", road_distance_km=11.1, road_duration_minutes=15.0))
    graph.add_edge(DirectedEdge(from_id="B", to_id="C", road_distance_km=11.1, road_duration_minutes=15.0))
    graph.add_edge(DirectedEdge(from_id="A", to_id="C", road_distance_km=22.2, road_duration_minutes=40.0))

    res = dijkstra_shortest_path(graph, "A", "C")
    assert res.path == ["A", "B", "C"]
    assert res.total_cost == 30.0
    assert res.nodes_expanded >= 1


# --------------------------------------------------------------------------
# 12. A* Cost == Dijkstra Cost (Floating point tolerance)
# --------------------------------------------------------------------------
def test_astar_cost_equals_dijkstra_cost():
    graph = InternalRouteGraph(v_max_kmh=100.0)
    # Create 6-node grid graph with non-trivial road paths
    nodes = [f"N{i}" for i in range(6)]
    coords = [
        (27.170, 78.040), (27.175, 78.045), (27.180, 78.030),
        (27.185, 78.020), (27.190, 78.010), (27.195, 78.005),
    ]
    for nid, (lat, lon) in zip(nodes, coords):
        graph.add_node(RouteNode(id=nid, name=nid, latitude=lat, longitude=lon))

    import random
    rng = random.Random(42)
    for i in range(len(nodes)):
        for j in range(len(nodes)):
            if i != j:
                u, v = nodes[i], nodes[j]
                h_dist = haversine(coords[i][0], coords[i][1], coords[j][0], coords[j][1])
                road_dist = h_dist * rng.uniform(1.1, 1.4)
                duration = (road_dist / rng.uniform(30.0, 60.0)) * 60.0
                graph.add_edge(DirectedEdge(from_id=u, to_id=v, road_distance_km=road_dist, road_duration_minutes=duration))

    for src in ["N0", "N1"]:
        for dst in ["N4", "N5"]:
            astar = astar_shortest_path(graph, src, dst)
            dijk = dijkstra_shortest_path(graph, src, dst)
            assert abs(astar.total_cost - dijk.total_cost) < 1e-4, f"Mismatch: A*={astar.total_cost}, Dijk={dijk.total_cost}"


# --------------------------------------------------------------------------
# 13. Heuristic Admissibility: h(u, goal) <= g*(u, goal)
# --------------------------------------------------------------------------
def test_heuristic_admissibility():
    graph = InternalRouteGraph(v_max_kmh=100.0)
    nodes = [f"P_{i}" for i in range(5)]
    coords = [(27.10 + i * 0.05, 78.00 + i * 0.04) for i in range(5)]
    for nid, (lat, lon) in zip(nodes, coords):
        graph.add_node(RouteNode(id=nid, name=nid, latitude=lat, longitude=lon))

    # Connect with realistic road speeds <= 100 km/h
    for i in range(5):
        for j in range(5):
            if i != j:
                u, v = nodes[i], nodes[j]
                h_dist = haversine(coords[i][0], coords[i][1], coords[j][0], coords[j][1])
                # Speed 40 km/h
                duration = (h_dist * 1.2 / 40.0) * 60.0
                graph.add_edge(DirectedEdge(from_id=u, to_id=v, road_distance_km=h_dist * 1.2, road_duration_minutes=duration))

    goal = "P_4"
    for u in nodes:
        h = graph.heuristic(u, goal)
        opt_path = dijkstra_shortest_path(graph, u, goal)
        assert h <= opt_path.total_cost + 1e-6, f"Heuristic not admissible for {u}: h={h}, g*={opt_path.total_cost}"


# --------------------------------------------------------------------------
# 14. Missing Accommodation: HTTP 400 domain error
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_missing_accommodation_raises_400(db_session: AsyncSession):
    # Create user & location
    user = User(email=f"no_acc_{uuid.uuid4().hex[:6]}@test.com", hashed_password="pw", full_name="Tester")
    loc = Location(name="City Center", latitude=27.17, longitude=78.04, city="Agra", country="India")
    db_session.add_all([user, loc])
    await db_session.flush()

    # Create trip WITHOUT accommodation
    trip = Trip(
        user_id=user.id,
        location_id=loc.id,
        title="Orphan Trip",
        start_date=date(2026, 10, 1),
        end_date=date(2026, 10, 2),
        total_days=2,
    )
    db_session.add(trip)
    await db_session.commit()

    req = ItineraryOptimizePlanRequest(
        trip_id=str(trip.id),
        day_clusters=[DayClusterInput(day_number=1, poi_ids=[str(uuid.uuid4())])],
    )

    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await optimize_and_persist_itinerary(req, db=db_session)

    assert exc_info.value.status_code == 400
    assert "accommodation" in exc_info.value.detail.lower()


# --------------------------------------------------------------------------
# 15. Closed POI: Excluded from route on that day of week
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_closed_poi_handling(db_session: AsyncSession):
    # Friday test: 2026-10-02 is a Friday (weekday = 4)
    target_date = date(2026, 10, 2)
    assert target_date.weekday() == 4  # Friday

    user = User(email=f"friday_{uuid.uuid4().hex[:6]}@test.com", hashed_password="pw", full_name="Friday Tester")
    loc = Location(name="Hotel Loc", latitude=27.17, longitude=78.04, city="Agra", country="India")
    loc_poi = Location(name="Monument Loc", latitude=27.18, longitude=78.02, city="Agra", country="India")
    cat = Category(name=f"Heritage_{uuid.uuid4().hex[:4]}", slug=f"heritage-{uuid.uuid4().hex[:6]}")
    db_session.add_all([user, loc, loc_poi, cat])
    await db_session.flush()

    acc = Accommodation(location_id=loc.id, name="Taj View Hotel")
    poi = POI(
        location_id=loc_poi.id,
        category_id=cat.id,
        name="Closed on Friday Monument",
        typical_visit_duration_minutes=60,
    )
    db_session.add_all([acc, poi])
    await db_session.flush()

    # Opening hours: closed on Friday (day_of_week = 4)
    oh = OpeningHours(
        poi_id=poi.id,
        day_of_week=4,
        open_time=dt_time(9, 0),
        close_time=dt_time(17, 0),
        is_closed=True,
    )
    trip = Trip(
        user_id=user.id,
        location_id=loc.id,
        title="Friday Trip",
        start_date=target_date,
        end_date=target_date,
        total_days=1,
    )
    db_session.add_all([oh, trip])
    await db_session.flush()

    trip_acc = TripAccommodation(
        trip_id=trip.id,
        accommodation_id=acc.id,
        check_in_date=target_date,
        check_out_date=target_date,
    )
    db_session.add(trip_acc)
    await db_session.commit()

    req = ItineraryOptimizePlanRequest(
        trip_id=str(trip.id),
        day_clusters=[DayClusterInput(day_number=1, poi_ids=[str(poi.id)])],
    )

    resp = await optimize_and_persist_itinerary(req, db=db_session)
    assert len(resp.days) == 1
    day1 = resp.days[0]
    # Since only POI was closed, timeline has no visited POIs
    assert len(day1.timeline) == 0
    assert any("closed on this day" in w.lower() for w in day1.warnings)


# --------------------------------------------------------------------------
# 16. Zero POI Day: Clean handling
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_zero_poi_day(db_session: AsyncSession):
    user = User(email=f"zero_poi_{uuid.uuid4().hex[:6]}@test.com", hashed_password="pw", full_name="Zero Tester")
    loc = Location(name="Hotel Loc", latitude=27.17, longitude=78.04, city="Agra", country="India")
    db_session.add_all([user, loc])
    await db_session.flush()

    acc = Accommodation(location_id=loc.id, name="Zero POI Hotel")
    trip = Trip(
        user_id=user.id,
        location_id=loc.id,
        title="Empty Day Trip",
        start_date=date(2026, 11, 1),
        end_date=date(2026, 11, 1),
        total_days=1,
    )
    db_session.add_all([acc, trip])
    await db_session.flush()

    trip_acc = TripAccommodation(
        trip_id=trip.id,
        accommodation_id=acc.id,
        check_in_date=date(2026, 11, 1),
        check_out_date=date(2026, 11, 1),
    )
    db_session.add(trip_acc)
    await db_session.commit()

    # Pass non-existent UUIDs
    req = ItineraryOptimizePlanRequest(
        trip_id=str(trip.id),
        day_clusters=[DayClusterInput(day_number=1, poi_ids=[str(uuid.uuid4())])],
    )

    resp = await optimize_and_persist_itinerary(req, db=db_session)
    assert len(resp.days) == 1
    assert resp.days[0].total_distance_km == 0.0
    assert resp.days[0].total_duration_minutes == 0.0


# --------------------------------------------------------------------------
# 17. One POI Day: Tour is [Anchor, POI, Anchor]
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_one_poi_day(db_session: AsyncSession):
    user = User(email=f"one_poi_{uuid.uuid4().hex[:6]}@test.com", hashed_password="pw", full_name="One Tester")
    loc = Location(name="Hotel Loc", latitude=27.17, longitude=78.04, city="Agra", country="India")
    loc_poi = Location(name="Fort Loc", latitude=27.18, longitude=78.02, city="Agra", country="India")
    cat = Category(name=f"Fort_{uuid.uuid4().hex[:4]}", slug=f"fort-{uuid.uuid4().hex[:6]}")
    db_session.add_all([user, loc, loc_poi, cat])
    await db_session.flush()

    acc = Accommodation(location_id=loc.id, name="Base Hotel")
    poi = POI(location_id=loc_poi.id, category_id=cat.id, name="Agra Fort", typical_visit_duration_minutes=90)
    trip = Trip(
        user_id=user.id,
        location_id=loc.id,
        title="Single POI Trip",
        start_date=date(2026, 10, 10),
        end_date=date(2026, 10, 10),
        total_days=1,
    )
    db_session.add_all([acc, poi, trip])
    await db_session.flush()

    trip_acc = TripAccommodation(
        trip_id=trip.id,
        accommodation_id=acc.id,
        check_in_date=date(2026, 10, 10),
        check_out_date=date(2026, 10, 10),
    )
    db_session.add(trip_acc)
    await db_session.commit()

    # Mock OSRM to return 5km / 10min for every pair
    mock_edge_resp = {
        "code": "Ok",
        "routes": [{"distance": 5000.0, "duration": 600.0, "geometry": {"type": "LineString", "coordinates": []}}],
    }
    with patch("httpx.AsyncClient.get", return_value=AsyncMock(status_code=200, json=lambda: mock_edge_resp)):
        req = ItineraryOptimizePlanRequest(
            trip_id=str(trip.id),
            day_clusters=[DayClusterInput(day_number=1, poi_ids=[str(poi.id)])],
        )
        resp = await optimize_and_persist_itinerary(req, db=db_session)
        day1 = resp.days[0]
        assert day1.tour == [str(acc.id), str(poi.id), str(acc.id)]
        assert len(day1.timeline) == 1
        assert len(day1.legs) == 2  # Acc -> POI, POI -> Acc


# --------------------------------------------------------------------------
# 18. Multi-Day Isolation: Distinct days, independent anchored cycles
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_multi_day_isolation(db_session: AsyncSession):
    user = User(email=f"multi_{uuid.uuid4().hex[:6]}@test.com", hashed_password="pw", full_name="Multi Tester")
    loc = Location(name="Hotel Loc", latitude=27.17, longitude=78.04, city="Agra", country="India")
    loc_p1 = Location(name="P1 Loc", latitude=27.18, longitude=78.02, city="Agra", country="India")
    loc_p2 = Location(name="P2 Loc", latitude=27.19, longitude=78.01, city="Agra", country="India")
    cat = Category(name=f"Cat_{uuid.uuid4().hex[:4]}", slug=f"cat-{uuid.uuid4().hex[:6]}")
    db_session.add_all([user, loc, loc_p1, loc_p2, cat])
    await db_session.flush()

    acc = Accommodation(location_id=loc.id, name="Hub Hotel")
    p1 = POI(location_id=loc_p1.id, category_id=cat.id, name="Day 1 Sight")
    p2 = POI(location_id=loc_p2.id, category_id=cat.id, name="Day 2 Sight")
    trip = Trip(
        user_id=user.id,
        location_id=loc.id,
        title="2-Day Trip",
        start_date=date(2026, 10, 10),
        end_date=date(2026, 10, 11),
        total_days=2,
    )
    db_session.add_all([acc, p1, p2, trip])
    await db_session.flush()

    trip_acc = TripAccommodation(
        trip_id=trip.id,
        accommodation_id=acc.id,
        check_in_date=date(2026, 10, 10),
        check_out_date=date(2026, 10, 11),
    )
    db_session.add(trip_acc)
    await db_session.commit()

    mock_resp = {
        "code": "Ok",
        "routes": [{"distance": 3000.0, "duration": 300.0, "geometry": {"type": "LineString", "coordinates": []}}],
    }
    with patch("httpx.AsyncClient.get", return_value=AsyncMock(status_code=200, json=lambda: mock_resp)):
        req = ItineraryOptimizePlanRequest(
            trip_id=str(trip.id),
            day_clusters=[
                DayClusterInput(day_number=1, poi_ids=[str(p1.id)]),
                DayClusterInput(day_number=2, poi_ids=[str(p2.id)]),
            ],
        )
        resp = await optimize_and_persist_itinerary(req, db=db_session)
        assert len(resp.days) == 2
        assert resp.days[0].day_number == 1
        assert resp.days[0].tour == [str(acc.id), str(p1.id), str(acc.id)]
        assert resp.days[1].day_number == 2
        assert resp.days[1].tour == [str(acc.id), str(p2.id), str(acc.id)]


# --------------------------------------------------------------------------
# 19. Alternative Tour: Genuine distinct alternative without fabricated text
# --------------------------------------------------------------------------
def test_alternative_tour_validity():
    graph = InternalRouteGraph(v_max_kmh=100.0)
    nodes = ["ACC", "P1", "P2", "P3"]
    for nid in nodes:
        graph.add_node(
            RouteNode(
                id=nid,
                name=nid,
                latitude=27.0,
                longitude=78.0,
                is_anchor=(nid == "ACC"),
                open_time=dt_time(8, 0),
                close_time=dt_time(20, 0),
            )
        )

    for u in nodes:
        for v in nodes:
            if u != v:
                graph.add_edge(DirectedEdge(from_id=u, to_id=v, road_distance_km=10.0, road_duration_minutes=15.0))

    primary = ["ACC", "P1", "P2", "P3", "ACC"]
    alt = get_alternative_tour(graph, primary)

    assert alt is not None
    assert alt != primary
    assert alt[0] == "ACC"
    assert alt[-1] == "ACC"
    assert set(alt[1:-1]) == {"P1", "P2", "P3"}


# --------------------------------------------------------------------------
# 20. PostgreSQL Persistence & 21. Route Anchor Semantics
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_postgresql_persistence_and_route_anchor_semantics(db_session: AsyncSession):
    user = User(email=f"persist_{uuid.uuid4().hex[:6]}@test.com", hashed_password="pw", full_name="Persist Tester")
    loc = Location(name="Hotel Loc", latitude=27.17, longitude=78.04, city="Agra", country="India")
    loc_p1 = Location(name="P1 Loc", latitude=27.18, longitude=78.02, city="Agra", country="India")
    loc_p2 = Location(name="P2 Loc", latitude=27.19, longitude=78.01, city="Agra", country="India")
    cat = Category(name=f"Persist_{uuid.uuid4().hex[:4]}", slug=f"persist-{uuid.uuid4().hex[:6]}")
    db_session.add_all([user, loc, loc_p1, loc_p2, cat])
    await db_session.flush()

    acc = Accommodation(location_id=loc.id, name="Persist Hotel")
    p1 = POI(location_id=loc_p1.id, category_id=cat.id, name="Sight A", typical_visit_duration_minutes=45)
    p2 = POI(location_id=loc_p2.id, category_id=cat.id, name="Sight B", typical_visit_duration_minutes=60)
    trip = Trip(
        user_id=user.id,
        location_id=loc.id,
        title="Persist Trip",
        start_date=date(2026, 12, 1),
        end_date=date(2026, 12, 1),
        total_days=1,
    )
    db_session.add_all([acc, p1, p2, trip])
    await db_session.flush()

    trip_acc = TripAccommodation(
        trip_id=trip.id,
        accommodation_id=acc.id,
        check_in_date=date(2026, 12, 1),
        check_out_date=date(2026, 12, 1),
    )
    db_session.add(trip_acc)
    await db_session.commit()

    mock_resp = {
        "code": "Ok",
        "routes": [{"distance": 4000.0, "duration": 400.0, "geometry": {"type": "LineString", "coordinates": []}}],
    }
    with patch("httpx.AsyncClient.get", return_value=AsyncMock(status_code=200, json=lambda: mock_resp)):
        req = ItineraryOptimizePlanRequest(
            trip_id=str(trip.id),
            day_clusters=[DayClusterInput(day_number=1, poi_ids=[str(p1.id), str(p2.id)])],
        )
        resp = await optimize_and_persist_itinerary(req, db=db_session)
        itin_id = uuid.UUID(resp.itinerary_id)

        # Verify DB records
        itin_stmt = (
            select(Itinerary)
            .where(Itinerary.id == itin_id)
            .options(selectinload(Itinerary.stops), selectinload(Itinerary.routes))
        )
        db_res = await db_session.execute(itin_stmt)
        saved_itin = db_res.scalar_one()

        assert saved_itin is not None
        assert saved_itin.is_primary is True

        # Stops: exactly 2 POIs, accommodation NEVER an itinerary_stop
        assert len(saved_itin.stops) == 2
        stop_poi_ids = {s.poi_id for s in saved_itin.stops}
        assert stop_poi_ids == {p1.id, p2.id}
        assert acc.id not in stop_poi_ids

        # Routes: 3 legs: Acc -> Stop1, Stop1 -> Stop2, Stop2 -> Acc
        assert len(saved_itin.routes) == 3

        # Leg 0: Acc -> Stop 1 (source_stop_id = NULL)
        first_route = saved_itin.routes[0]
        assert first_route.source_stop_id is None
        assert first_route.target_stop_id == saved_itin.stops[0].id
        assert first_route.is_mock is False

        # Leg 1: Stop 1 -> Stop 2
        mid_route = saved_itin.routes[1]
        assert mid_route.source_stop_id == saved_itin.stops[0].id
        assert mid_route.target_stop_id == saved_itin.stops[1].id
        assert mid_route.is_mock is False

        # Leg 2: Stop 2 -> Acc (target_stop_id = NULL)
        last_route = saved_itin.routes[2]
        assert last_route.source_stop_id == saved_itin.stops[1].id
        assert last_route.target_stop_id is None
        assert last_route.is_mock is False


# --------------------------------------------------------------------------
# 22. Preserved /locations/route endpoint
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_preserved_locations_route_endpoint(client: AsyncClient):
    coords = [
        {"latitude": 27.1751, "longitude": 78.0421},
        {"latitude": 27.1795, "longitude": 78.0211},
    ]

    mock_resp = {
        "code": "Ok",
        "routes": [
            {
                "distance": 3500.0,
                "duration": 500.0,
                "geometry": {"type": "LineString", "coordinates": [[78.0421, 27.1751], [78.0211, 27.1795]]},
                "legs": [{"steps": [{"maneuver": {"type": "depart"}, "name": "Fatehabad Rd"}]}],
            }
        ],
    }

    with patch("httpx.AsyncClient.get", return_value=AsyncMock(status_code=200, json=lambda: mock_resp)):
        res = await client.post("/api/locations/route", json={"coordinates": coords, "mode": "driving"})
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["data"]["distance"] == 3.5
        assert data["data"]["duration"] == 8.33
        assert "geometry" in data["data"]


# --------------------------------------------------------------------------
# 23. Live API endpoint: POST /api/itineraries/optimize-plan
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_api_itineraries_optimize_plan_endpoint(client: AsyncClient, db_session: AsyncSession):
    user = User(email=f"api_test_{uuid.uuid4().hex[:6]}@test.com", hashed_password="pw", full_name="API Tester")
    loc = Location(name="Hotel Loc", latitude=27.17, longitude=78.04, city="Agra", country="India")
    loc_poi = Location(name="POI Loc", latitude=27.18, longitude=78.02, city="Agra", country="India")
    cat = Category(name=f"Cat_{uuid.uuid4().hex[:4]}", slug=f"cat-{uuid.uuid4().hex[:6]}")
    db_session.add_all([user, loc, loc_poi, cat])
    await db_session.flush()

    acc = Accommodation(location_id=loc.id, name="Taj View Hotel")
    poi = POI(location_id=loc_poi.id, category_id=cat.id, name="Taj Mahal", typical_visit_duration_minutes=90)
    trip = Trip(
        user_id=user.id,
        location_id=loc.id,
        title="API Plan Trip",
        start_date=date(2026, 10, 15),
        end_date=date(2026, 10, 15),
        total_days=1,
    )
    db_session.add_all([acc, poi, trip])
    await db_session.flush()

    trip_acc = TripAccommodation(
        trip_id=trip.id,
        accommodation_id=acc.id,
        check_in_date=date(2026, 10, 15),
        check_out_date=date(2026, 10, 15),
    )
    db_session.add(trip_acc)
    await db_session.commit()

    token = create_access_token(str(user.id))
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "trip_id": str(trip.id),
        "day_clusters": [{"day_number": 1, "poi_ids": [str(poi.id)]}],
        "transport_mode": "driving",
        "daily_start_time": "09:00",
        "title": "API Test Itinerary",
    }

    mock_resp = {
        "code": "Ok",
        "routes": [{"distance": 4200.0, "duration": 420.0, "geometry": {"type": "LineString", "coordinates": []}}],
    }
    with patch("httpx.AsyncClient.get", return_value=AsyncMock(status_code=200, json=lambda: mock_resp)):
        res = await client.post("/api/itineraries/optimize-plan", json=payload, headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        itin_data = data["data"]
        assert itin_data["trip_id"] == str(trip.id)
        assert itin_data["name"] == "API Test Itinerary"
        assert len(itin_data["days"]) == 1
        assert itin_data["days"][0]["tour"] == [str(acc.id), str(poi.id), str(acc.id)]
