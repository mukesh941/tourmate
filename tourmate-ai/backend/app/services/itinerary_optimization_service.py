"""
Phase 4 Itinerary Optimization Service.
Orchestration layer implementing the complete approved Phase 4 pipeline:
1. Trip & Accommodation resolution (Accommodation = strict daily tour anchor; HTTP 400 if missing).
2. Canonical POI & opening-hour resolution (filter closed attractions, respect daily max candidate POIs).
3. Authoritative OSRM directed pairwise routing (no fabricated fallbacks, exponential backoff, caching).
4. Internal directed route graph construction (A* admissible heuristic).
5. Anchored Cheapest Insertion & Anchored 2-opt tour refinement (directed road durations).
6. Opening-hour feasibility verification.
7. Second-best alternative tour discovery (no fabricated descriptions).
8. A* vs Dijkstra pathfinding benchmark.
9. Full PostgreSQL persistence (itineraries, itinerary_stops, routes with correct NULL anchor semantics).
"""
import logging
import uuid
from datetime import datetime, time as dt_time, timedelta
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.sql.accommodation import Accommodation
from app.models.sql.itinerary import AlternativeRoute, Itinerary, ItineraryStop, Route
from app.models.sql.location import Location
from app.models.sql.poi import OpeningHours, POI
from app.models.sql.trip import POICluster, Trip, TripAccommodation
from app.schemas.route_optimization import (
    AlternativeTourSummary,
    DayClusterInput,
    DayOptimizationResult,
    ItineraryOptimizePlanRequest,
    ItineraryOptimizePlanResponse,
    PathfindingBenchmarkMetrics,
    RouteLegSchema,
    StopTimelineItem,
)
from app.services.graph_service import DirectedEdge, InternalRouteGraph, RouteNode, haversine
from app.services.osrm_service import RoutingUnavailableError, get_directed_pairwise_matrix
from app.services.pathfinding_service import astar_shortest_path, dijkstra_shortest_path
from app.services.tsp_service import (
    anchored_cheapest_insertion,
    anchored_two_opt,
    calculate_tour_distance,
    calculate_tour_duration,
    get_alternative_tour,
    validate_tour_opening_hours,
)

logger = logging.getLogger(__name__)


async def optimize_and_persist_itinerary(
    payload: ItineraryOptimizePlanRequest,
    db: AsyncSession,
) -> ItineraryOptimizePlanResponse:
    """
    Executes the full Phase 4 itinerary optimization pipeline and persists
    the resulting tour, stops, routes, and alternatives to PostgreSQL.
    """
    # 1. Resolve Trip
    try:
        trip_uuid = uuid.UUID(payload.trip_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid trip_id UUID format: '{payload.trip_id}'",
        )

    trip_stmt = (
        select(Trip)
        .where(Trip.id == trip_uuid)
        .options(
            selectinload(Trip.accommodations).selectinload(TripAccommodation.accommodation).selectinload(Accommodation.location),
            selectinload(Trip.poi_clusters),
        )
    )
    res = await db.execute(trip_stmt)
    trip = res.scalar_one_or_none()
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trip '{payload.trip_id}' not found",
        )

    # 2. Resolve Accommodation (Strict Anchor Rule)
    if not trip.accommodations:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Trip does not have an accommodation configured. "
                "An accommodation is strictly required as the daily tour anchor. "
                "Please assign an accommodation to the trip before optimizing."
            ),
        )

    trip_acc = trip.accommodations[0]
    accommodation = trip_acc.accommodation
    if not accommodation or not accommodation.location:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Configured accommodation lacks physical location coordinates.",
        )

    acc_node_id = str(accommodation.id)
    acc_name = accommodation.name
    acc_lat = accommodation.location.latitude
    acc_lon = accommodation.location.longitude

    # 3. Resolve Day Clusters
    day_clusters_map: Dict[int, List[str]] = {}
    if payload.day_clusters:
        for dc in payload.day_clusters:
            day_clusters_map[dc.day_number] = dc.poi_ids
    elif trip.poi_clusters:
        for pc in trip.poi_clusters:
            day_clusters_map.setdefault(pc.assigned_day, []).append(str(pc.poi_id))
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No day clusters provided and no POI clusters exist for this trip.",
        )

    # Parse daily start time
    try:
        sh, sm = map(int, payload.daily_start_time.split(":"))
        start_time = dt_time(sh, sm)
    except Exception:
        start_time = dt_time(9, 0)

    # Process each day cluster
    day_results: List[DayOptimizationResult] = []
    total_itinerary_distance_km = 0.0
    total_itinerary_duration_minutes = 0.0

    # Persistence accumulator structures
    # (day_number, stop_order, poi_uuid, arrival_time, departure_time, duration_minutes)
    planned_stops: List[Dict[str, Any]] = []
    # (day_number, from_node_id, to_node_id, source_stop_index, target_stop_index, edge)
    planned_legs: List[Dict[str, Any]] = []
    # (day_number, alt_summary)
    planned_alternatives: List[Dict[str, Any]] = []

    for day_num in sorted(day_clusters_map.keys()):
        raw_poi_ids = day_clusters_map[day_num]
        day_warnings: List[str] = []

        # Convert and validate POI UUIDs
        valid_uuids: List[uuid.UUID] = []
        for pid in raw_poi_ids:
            try:
                valid_uuids.append(uuid.UUID(pid))
            except ValueError:
                day_warnings.append(f"Skipping invalid POI UUID: '{pid}'")

        if not valid_uuids:
            # Empty day
            day_results.append(
                DayOptimizationResult(
                    day_number=day_num,
                    tour=[acc_node_id, acc_node_id],
                    timeline=[],
                    legs=[],
                    total_distance_km=0.0,
                    total_duration_minutes=0.0,
                    is_feasible=True,
                    warnings=day_warnings + ["No valid POIs found for this day."],
                )
            )
            continue

        # Fetch POI records with Location and OpeningHours
        pois_stmt = (
            select(POI)
            .where(POI.id.in_(valid_uuids), POI.is_active.is_(True))
            .options(selectinload(POI.location), selectinload(POI.opening_hours))
        )
        poi_res = await db.execute(pois_stmt)
        poi_records = {str(p.id): p for p in poi_res.scalars().all()}

        # Enforce max candidate POIs configuration (Single Source of Truth)
        candidate_pids = [pid for pid in raw_poi_ids if pid in poi_records]
        if len(candidate_pids) > settings.max_daily_candidate_pois:
            day_warnings.append(
                f"Candidate POIs ({len(candidate_pids)}) exceeded daily limit "
                f"({settings.max_daily_candidate_pois}). Truncated to first {settings.max_daily_candidate_pois}."
            )
            candidate_pids = candidate_pids[: settings.max_daily_candidate_pois]

        # Calculate day of week for opening hours validation
        trip_day_date = trip.start_date + timedelta(days=day_num - 1)
        day_of_week = trip_day_date.weekday()

        # Build RouteNode list
        day_nodes: List[RouteNode] = [
            RouteNode(
                id=acc_node_id,
                name=acc_name,
                latitude=acc_lat,
                longitude=acc_lon,
                visit_duration_minutes=0,
                is_anchor=True,
            )
        ]

        active_poi_ids: List[str] = []
        for pid in candidate_pids:
            poi = poi_records[pid]
            # Check opening hours for day_of_week
            oh_match = next((oh for oh in poi.opening_hours if oh.day_of_week == day_of_week), None)
            is_closed = oh_match.is_closed if oh_match else False
            open_time = oh_match.open_time if oh_match else None
            close_time = oh_match.close_time if oh_match else None

            if is_closed:
                day_warnings.append(f"Attraction '{poi.name}' is closed on this day. Excluded from route.")
                continue

            node = RouteNode(
                id=str(poi.id),
                name=poi.name,
                latitude=poi.location.latitude,
                longitude=poi.location.longitude,
                visit_duration_minutes=poi.typical_visit_duration_minutes,
                is_anchor=False,
                open_time=open_time,
                close_time=close_time,
                is_closed=False,
            )
            day_nodes.append(node)
            active_poi_ids.append(str(poi.id))

        if not active_poi_ids:
            day_results.append(
                DayOptimizationResult(
                    day_number=day_num,
                    tour=[acc_node_id, acc_node_id],
                    timeline=[],
                    legs=[],
                    total_distance_km=0.0,
                    total_duration_minutes=0.0,
                    is_feasible=True,
                    warnings=day_warnings + ["All candidate POIs were closed or unavailable."],
                )
            )
            continue

        # Obtain authoritative OSRM directed pairwise routing matrix
        matrix = await get_directed_pairwise_matrix(day_nodes, mode=payload.transport_mode)

        # Construct InternalRouteGraph
        graph = InternalRouteGraph(v_max_kmh=settings.routing_v_max_kmh)
        for node in day_nodes:
            graph.add_node(node)
        for (u, v), edge in matrix.items():
            graph.add_edge(edge)

        # Step 3: Cheapest Insertion
        initial_tour = anchored_cheapest_insertion(graph, acc_node_id, active_poi_ids)

        # Step 4: Anchored 2-opt
        optimized_tour = anchored_two_opt(graph, initial_tour)

        # Opening-hour validation
        is_feasible, oh_warnings, timeline_raw = validate_tour_opening_hours(
            graph, optimized_tour, daily_start_time=start_time
        )
        day_warnings.extend(oh_warnings)

        # Build timeline items and collect stops for persistence
        timeline_items: List[StopTimelineItem] = []
        visited_poi_ids_in_order = [nid for nid in optimized_tour[1:-1] if nid != acc_node_id]

        for order_idx, item in enumerate(timeline_raw):
            if item.get("is_anchor"):
                continue
            poi_id_str = item["node_id"]
            timeline_items.append(
                StopTimelineItem(
                    poi_id=poi_id_str,
                    name=item["name"],
                    arrival_time=item["arrival_time"],
                    departure_time=item["departure_time"],
                    visit_duration_minutes=item.get("visit_duration_minutes", 60),
                    stop_order=order_idx + 1,
                )
            )
            planned_stops.append({
                "day_number": day_num,
                "stop_order": order_idx + 1,
                "poi_uuid": uuid.UUID(poi_id_str),
                "arrival_time": dt_time.fromisoformat(item["arrival_time"]),
                "departure_time": dt_time.fromisoformat(item["departure_time"]),
                "duration_minutes": item.get("visit_duration_minutes", 60),
            })

        # Calculate legs and metrics
        day_dist = calculate_tour_distance(graph, optimized_tour)
        day_dur = calculate_tour_duration(graph, optimized_tour)
        total_itinerary_distance_km += day_dist
        total_itinerary_duration_minutes += day_dur

        legs_schemas: List[RouteLegSchema] = []
        for i in range(len(optimized_tour) - 1):
            u_id = optimized_tour[i]
            v_id = optimized_tour[i + 1]
            edge = graph.get_edge(u_id, v_id)

            legs_schemas.append(
                RouteLegSchema(
                    from_node_id=u_id,
                    to_node_id=v_id,
                    distance_km=edge.road_distance_km,
                    duration_minutes=int(round(edge.road_duration_minutes)),
                    geometry=edge.geometry,
                    is_mock=False,
                )
            )
            planned_legs.append({
                "day_number": day_num,
                "leg_index": i,
                "from_node_id": u_id,
                "to_node_id": v_id,
                "edge": edge,
                "is_first_leg": (i == 0),
                "is_last_leg": (i == len(optimized_tour) - 2),
                "source_poi_id": u_id if u_id != acc_node_id else None,
                "target_poi_id": v_id if v_id != acc_node_id else None,
            })

        # Step 7: Alternative Tour
        alt_tour = get_alternative_tour(graph, optimized_tour, daily_start_time=start_time)
        alt_summary: Optional[AlternativeTourSummary] = None
        if alt_tour and alt_tour != optimized_tour:
            alt_dist = calculate_tour_distance(graph, alt_tour)
            alt_dur = calculate_tour_duration(graph, alt_tour)
            alt_summary = AlternativeTourSummary(
                description="Alternative route ordering with adjusted POI sequence",
                total_distance_km=round(alt_dist, 2),
                total_travel_time_minutes=int(round(alt_dur)),
                tour_node_ids=alt_tour,
            )
            planned_alternatives.append({
                "day_number": day_num,
                "summary": alt_summary,
            })

        # Step 5 & 6: Pathfinding Benchmark (A* vs Dijkstra)
        benchmark: Optional[PathfindingBenchmarkMetrics] = None
        if len(active_poi_ids) >= 2:
            src = active_poi_ids[0]
            dst = active_poi_ids[-1]
            astar_res = astar_shortest_path(graph, src, dst)
            dijkstra_res = dijkstra_shortest_path(graph, src, dst)

            benchmark = PathfindingBenchmarkMetrics(
                source_node_id=src,
                target_node_id=dst,
                astar_cost_minutes=round(astar_res.total_cost, 2),
                dijkstra_cost_minutes=round(dijkstra_res.total_cost, 2),
                cost_difference=round(abs(astar_res.total_cost - dijkstra_res.total_cost), 4),
                astar_nodes_expanded=astar_res.nodes_expanded,
                dijkstra_nodes_expanded=dijkstra_res.nodes_expanded,
                astar_execution_time_ms=round(astar_res.execution_time_ms, 3),
                dijkstra_execution_time_ms=round(dijkstra_res.execution_time_ms, 3),
            )

        day_results.append(
            DayOptimizationResult(
                day_number=day_num,
                tour=optimized_tour,
                timeline=timeline_items,
                legs=legs_schemas,
                total_distance_km=round(day_dist, 2),
                total_duration_minutes=round(day_dur, 2),
                is_feasible=is_feasible,
                warnings=day_warnings,
                alternative_tour=alt_summary,
                benchmark=benchmark,
            )
        )

    # Step 9: PostgreSQL Persistence
    itinerary_title = payload.title or f"{trip.title} - Optimized Plan"
    itinerary = Itinerary(
        trip_id=trip.id,
        name=itinerary_title,
        is_primary=True,
        total_distance_km=round(total_itinerary_distance_km, 2),
        total_travel_time_minutes=int(round(total_itinerary_duration_minutes)),
    )
    db.add(itinerary)
    await db.flush()

    # Map (day_number, poi_uuid) -> ItineraryStop
    stop_map: Dict[Tuple[int, uuid.UUID], ItineraryStop] = {}
    stops_to_add: List[ItineraryStop] = []

    for ps in planned_stops:
        stop = ItineraryStop(
            itinerary_id=itinerary.id,
            poi_id=ps["poi_uuid"],
            day_number=ps["day_number"],
            stop_order=ps["stop_order"],
            arrival_time=ps["arrival_time"],
            departure_time=ps["departure_time"],
            duration_minutes=ps["duration_minutes"],
        )
        stops_to_add.append(stop)
        stop_map[(ps["day_number"], ps["poi_uuid"])] = stop

    db.add_all(stops_to_add)
    await db.flush()

    # Update timeline_items with the newly generated stop_id
    for dr in day_results:
        for t_item in dr.timeline:
            st = stop_map.get((dr.day_number, uuid.UUID(t_item.poi_id)))
            if st:
                t_item.stop_id = str(st.id)

    # Persist Route legs with strict NULL anchor semantics
    routes_to_add: List[Route] = []
    for leg in planned_legs:
        day_num = leg["day_number"]
        edge: DirectedEdge = leg["edge"]

        source_stop_id: Optional[uuid.UUID] = None
        target_stop_id: Optional[uuid.UUID] = None

        if leg["is_first_leg"]:
            # Accommodation -> First POI
            source_stop_id = None
            target_stop_uuid = uuid.UUID(leg["target_poi_id"])
            target_stop = stop_map.get((day_num, target_stop_uuid))
            target_stop_id = target_stop.id if target_stop else None
        elif leg["is_last_leg"]:
            # Last POI -> Accommodation
            source_stop_uuid = uuid.UUID(leg["source_poi_id"])
            source_stop = stop_map.get((day_num, source_stop_uuid))
            source_stop_id = source_stop.id if source_stop else None
            target_stop_id = None
        else:
            # POI -> POI
            source_stop_uuid = uuid.UUID(leg["source_poi_id"])
            source_stop = stop_map.get((day_num, source_stop_uuid))
            source_stop_id = source_stop.id if source_stop else None

            target_stop_uuid = uuid.UUID(leg["target_poi_id"])
            target_stop = stop_map.get((day_num, target_stop_uuid))
            target_stop_id = target_stop.id if target_stop else None

        route_obj = Route(
            itinerary_id=itinerary.id,
            source_stop_id=source_stop_id,
            target_stop_id=target_stop_id,
            distance=round(edge.road_distance_km, 2),
            duration=int(round(edge.road_duration_minutes)),
            geometry=edge.geometry,
            mode=payload.transport_mode,
            is_mock=False,
        )
        routes_to_add.append(route_obj)

    db.add_all(routes_to_add)
    await db.flush()

    # If alternative tour was found, attach AlternativeRoute entry to first route
    if planned_alternatives and routes_to_add:
        alt_records: List[AlternativeRoute] = []
        for alt in planned_alternatives:
            s = alt["summary"]
            alt_rec = AlternativeRoute(
                route_id=routes_to_add[0].id,
                distance=s.total_distance_km,
                duration=s.total_travel_time_minutes,
                description=s.description,
            )
            alt_records.append(alt_rec)
        db.add_all(alt_records)

    await db.commit()

    return ItineraryOptimizePlanResponse(
        itinerary_id=str(itinerary.id),
        trip_id=str(trip.id),
        name=itinerary.name,
        total_distance_km=round(total_itinerary_distance_km, 2),
        total_travel_time_minutes=int(round(total_itinerary_duration_minutes)),
        days=day_results,
    )
