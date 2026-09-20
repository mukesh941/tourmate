"""
Anchored Traveling Salesperson Problem (TSP) Optimization Service.
Implements:
1. Anchored Cheapest Insertion algorithm with deterministic tie-breaking.
2. Anchored 2-opt tour refinement respecting directed asymmetric road costs.
3. Tour opening-hour feasibility checking.
4. Second-best alternative tour extraction without fabricated claims.
"""
from datetime import datetime, time as dt_time, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

from app.services.graph_service import InternalRouteGraph


def calculate_tour_duration(graph: InternalRouteGraph, tour: List[str]) -> float:
    """Calculates total road transit time for a tour in minutes."""
    if len(tour) < 2:
        return 0.0
    total = 0.0
    for i in range(len(tour) - 1):
        edge = graph.get_edge(tour[i], tour[i + 1])
        total += edge.road_duration_minutes
    return total


def calculate_tour_distance(graph: InternalRouteGraph, tour: List[str]) -> float:
    """Calculates total road distance for a tour in km."""
    if len(tour) < 2:
        return 0.0
    total = 0.0
    for i in range(len(tour) - 1):
        edge = graph.get_edge(tour[i], tour[i + 1])
        total += edge.road_distance_km
    return total


def anchored_cheapest_insertion(
    graph: InternalRouteGraph,
    anchor_id: str,
    candidate_poi_ids: List[str],
) -> List[str]:
    """
    Constructs an initial anchored tour visiting all candidate POIs and returning
    to the accommodation anchor.
    Initial cycle: [A, P_1, A] where P_1 minimizes cost(A, P) + cost(P, A).
    Iteratively inserts remaining POI k into edge (i, j) that minimizes insertion delta:
      delta = cost(i, k) + cost(k, j) - cost(i, j)
    Deterministic tie-breaking: (delta, str(poi_id)).
    """
    valid_pois = [pid for pid in candidate_poi_ids if pid in graph.nodes and pid != anchor_id]
    if not valid_pois:
        return [anchor_id, anchor_id]

    if len(valid_pois) == 1:
        return [anchor_id, valid_pois[0], anchor_id]

    # Select initial P_1 minimizing cycle cost with anchor
    best_p1 = None
    best_p1_cost = float("inf")

    for pid in sorted(valid_pois):
        c_a_p = graph.get_edge(anchor_id, pid).road_duration_minutes
        c_p_a = graph.get_edge(pid, anchor_id).road_duration_minutes
        total_cycle = c_a_p + c_p_a
        if total_cycle < best_p1_cost:
            best_p1_cost = total_cycle
            best_p1 = pid

    tour = [anchor_id, best_p1, anchor_id]
    unvisited = set(valid_pois) - {best_p1}

    # Iterative Cheapest Insertion
    while unvisited:
        best_delta = float("inf")
        best_k = None
        best_insert_pos = -1

        for k in sorted(unvisited):
            for i in range(len(tour) - 1):
                node_i = tour[i]
                node_j = tour[i + 1]

                c_i_k = graph.get_edge(node_i, k).road_duration_minutes
                c_k_j = graph.get_edge(k, node_j).road_duration_minutes
                c_i_j = graph.get_edge(node_i, node_j).road_duration_minutes

                delta = c_i_k + c_k_j - c_i_j

                if delta < best_delta - 1e-9:
                    best_delta = delta
                    best_k = k
                    best_insert_pos = i + 1
                elif abs(delta - best_delta) <= 1e-9:
                    # Deterministic tie-break by POI UUID string
                    if best_k is None or k < best_k:
                        best_delta = delta
                        best_k = k
                        best_insert_pos = i + 1

        tour.insert(best_insert_pos, best_k)
        unvisited.remove(best_k)

    return tour


def anchored_two_opt(
    graph: InternalRouteGraph,
    initial_tour: List[str],
    max_iterations: int = 150,
) -> List[str]:
    """
    Improves an anchored tour using 2-opt edge reversals on directed road durations.
    Tour format: [A, P_1, P_2, ..., P_n, A]
    Anchor constraints: index 0 and index -1 remain fixed at A.
    Only internal POI segments [i ... j] (1 <= i < j <= n) are reversed.
    Directed edge costs are recomputed accurately without assuming symmetry.
    """
    tour = list(initial_tour)
    n = len(tour)
    if n <= 3:
        return tour

    improved = True
    iteration = 0

    while improved and iteration < max_iterations:
        improved = False
        iteration += 1

        # We can reverse any sub-segment of POIs from index i to index j
        # where 1 <= i < j <= n - 2 (since index n-1 is the return anchor A)
        for i in range(1, n - 2):
            for j in range(i + 1, n - 1):
                # Calculate old directed cost of the segment being replaced
                # 1. Edge entering sub-segment: tour[i-1] -> tour[i]
                # 2. Internal edges of sub-segment: tour[k] -> tour[k+1] for k in [i..j-1]
                # 3. Edge exiting sub-segment: tour[j] -> tour[j+1]
                old_cost = graph.get_edge(tour[i - 1], tour[i]).road_duration_minutes
                for k in range(i, j):
                    old_cost += graph.get_edge(tour[k], tour[k + 1]).road_duration_minutes
                old_cost += graph.get_edge(tour[j], tour[j + 1]).road_duration_minutes

                # Calculate new directed cost after reversing sub-segment
                # Sub-segment reversed: tour[j], tour[j-1], ..., tour[i]
                # 1. Edge entering reversed: tour[i-1] -> tour[j]
                # 2. Internal edges reversed: tour[k] -> tour[k-1] for k in [j..i+1]
                # 3. Edge exiting reversed: tour[i] -> tour[j+1]
                new_cost = graph.get_edge(tour[i - 1], tour[j]).road_duration_minutes
                for k in range(j, i, -1):
                    new_cost += graph.get_edge(tour[k], tour[k - 1]).road_duration_minutes
                new_cost += graph.get_edge(tour[i], tour[j + 1]).road_duration_minutes

                if new_cost < old_cost - 1e-6:
                    # Apply reversal
                    tour[i : j + 1] = reversed(tour[i : j + 1])
                    improved = True
                    break
            if improved:
                break

    return tour


def validate_tour_opening_hours(
    graph: InternalRouteGraph,
    tour: List[str],
    daily_start_time: dt_time = dt_time(9, 0),
) -> Tuple[bool, List[str], List[Dict[str, Any]]]:
    """
    Simulates tour progression and validates arrival times against opening hours.
    Returns: (is_feasible, warnings, schedule_timeline)
    """
    is_feasible = True
    warnings: List[str] = []
    timeline: List[Dict[str, Any]] = []

    # Simulation base datetime
    today = datetime.now().date()
    current_dt = datetime.combine(today, daily_start_time)

    for i in range(len(tour) - 1):
        from_id = tour[i]
        to_id = tour[i + 1]

        leg_edge = graph.get_edge(from_id, to_id)
        travel_mins = leg_edge.road_duration_minutes

        arrival_dt = current_dt + timedelta(minutes=travel_mins)
        to_node = graph.get_node(to_id)

        if to_node.is_anchor:
            # Reached anchor at end of day
            timeline.append({
                "node_id": to_id,
                "name": to_node.name,
                "arrival_time": arrival_dt.time().strftime("%H:%M"),
                "departure_time": arrival_dt.time().strftime("%H:%M"),
                "is_anchor": True,
            })
            break

        # Check opening hours for sightseeing POI
        arr_time = arrival_dt.time()
        visit_duration = to_node.visit_duration_minutes

        if to_node.is_closed:
            is_feasible = False
            warnings.append(f"{to_node.name} is closed today.")

        if to_node.open_time and to_node.close_time:
            if arr_time < to_node.open_time:
                # Arrived early: wait until open
                arrival_dt = datetime.combine(today, to_node.open_time)
                arr_time = arrival_dt.time()
            elif arr_time > to_node.close_time:
                is_feasible = False
                warnings.append(
                    f"Late arrival: arrived at {to_node.name} at {arr_time.strftime('%H:%M')}, but it closes at {to_node.close_time.strftime('%H:%M')}."
                )

        departure_dt = arrival_dt + timedelta(minutes=visit_duration)

        timeline.append({
            "node_id": to_id,
            "name": to_node.name,
            "arrival_time": arr_time.strftime("%H:%M"),
            "departure_time": departure_dt.time().strftime("%H:%M"),
            "visit_duration_minutes": visit_duration,
            "is_anchor": False,
        })

        current_dt = departure_dt

    return is_feasible, warnings, timeline


def get_alternative_tour(
    graph: InternalRouteGraph,
    primary_tour: List[str],
    daily_start_time: dt_time = dt_time(9, 0),
) -> Optional[List[str]]:
    """
    Identifies a second valid, distinct optimization candidate with the same
    accommodation anchor, POIs, and transport mode.
    Does NOT fabricate descriptions. If no genuinely distinct feasible tour exists, returns None.
    """
    n = len(primary_tour)
    if n <= 3:
        return None

    # Candidate 1: Reverse of internal POI sequence
    reversed_candidate = [primary_tour[0]] + list(reversed(primary_tour[1:-1])) + [primary_tour[-1]]
    if reversed_candidate != primary_tour:
        feasible, _, _ = validate_tour_opening_hours(graph, reversed_candidate, daily_start_time)
        if feasible:
            return reversed_candidate

    # Candidate 2: Next best single 2-opt swap
    anchor = primary_tour[0]
    pois = primary_tour[1:-1]
    best_alt = None
    best_alt_cost = float("inf")
    primary_cost = calculate_tour_duration(graph, primary_tour)

    for i in range(len(pois) - 1):
        for j in range(i + 1, len(pois)):
            swapped = pois[:i] + list(reversed(pois[i : j + 1])) + pois[j + 1 :]
            candidate = [anchor] + swapped + [anchor]
            if candidate != primary_tour and candidate != reversed_candidate:
                cost = calculate_tour_duration(graph, candidate)
                if cost >= primary_cost - 1e-6 and cost < best_alt_cost:
                    feasible, _, _ = validate_tour_opening_hours(graph, candidate, daily_start_time)
                    if feasible:
                        best_alt_cost = cost
                        best_alt = candidate

    return best_alt
