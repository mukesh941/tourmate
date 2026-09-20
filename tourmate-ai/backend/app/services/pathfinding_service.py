"""
Pathfinding Service for Phase 4 Itinerary Optimization.
Implements:
1. A* shortest path search using admissible Haversine-over-speed heuristic.
2. Dijkstra shortest path search (baseline comparison with h=0).
3. PathfindingResult metric reporting (path, total_cost, nodes_expanded, execution_time_ms).
"""
import heapq
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

from app.services.graph_service import InternalRouteGraph


@dataclass
class PathfindingResult:
    path: List[str]
    total_cost: float
    nodes_expanded: int
    execution_time_ms: float


def astar_shortest_path(
    graph: InternalRouteGraph,
    source: str,
    destination: str,
) -> PathfindingResult:
    """
    Finds the shortest road-duration path from source to destination using A*.
    g-cost: cumulative road duration in minutes.
    h-cost: Haversine distance divided by max speed (v_max_kmh).
    Returns PathfindingResult with path, total_cost, nodes_expanded, execution_time_ms.
    """
    start_time = time.perf_counter()

    if source not in graph.nodes:
        raise KeyError(f"Source node '{source}' not in graph")
    if destination not in graph.nodes:
        raise KeyError(f"Destination node '{destination}' not in graph")

    if source == destination:
        elapsed = (time.perf_counter() - start_time) * 1000.0
        return PathfindingResult(
            path=[source],
            total_cost=0.0,
            nodes_expanded=0,
            execution_time_ms=elapsed,
        )

    # Priority queue items: (f_score, g_score, tie_breaker_counter, node_id)
    counter = 0
    h_start = graph.heuristic(source, destination)
    open_set: List[tuple] = [(h_start, 0.0, counter, source)]

    g_score: Dict[str, float] = {source: 0.0}
    came_from: Dict[str, str] = {}
    nodes_expanded = 0
    visited = set()

    while open_set:
        f, current_g, _, current = heapq.heappop(open_set)

        if current in visited:
            continue
        visited.add(current)
        nodes_expanded += 1

        if current == destination:
            # Reconstruct path
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()

            elapsed = (time.perf_counter() - start_time) * 1000.0
            return PathfindingResult(
                path=path,
                total_cost=g_score[destination],
                nodes_expanded=nodes_expanded,
                execution_time_ms=elapsed,
            )

        for neighbor in graph.adj.get(current, []):
            if neighbor in visited:
                continue

            edge = graph.get_edge(current, neighbor)
            tentative_g = current_g + edge.road_duration_minutes

            if tentative_g < g_score.get(neighbor, float("inf")):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                h = graph.heuristic(neighbor, destination)
                f_score = tentative_g + h
                counter += 1
                heapq.heappush(open_set, (f_score, tentative_g, counter, neighbor))

    elapsed = (time.perf_counter() - start_time) * 1000.0
    return PathfindingResult(
        path=[],
        total_cost=float("inf"),
        nodes_expanded=nodes_expanded,
        execution_time_ms=elapsed,
    )


def dijkstra_shortest_path(
    graph: InternalRouteGraph,
    source: str,
    destination: str,
) -> PathfindingResult:
    """
    Finds the shortest road-duration path from source to destination using Dijkstra's algorithm (h=0).
    Returns PathfindingResult with path, total_cost, nodes_expanded, execution_time_ms.
    """
    start_time = time.perf_counter()

    if source not in graph.nodes:
        raise KeyError(f"Source node '{source}' not in graph")
    if destination not in graph.nodes:
        raise KeyError(f"Destination node '{destination}' not in graph")

    if source == destination:
        elapsed = (time.perf_counter() - start_time) * 1000.0
        return PathfindingResult(
            path=[source],
            total_cost=0.0,
            nodes_expanded=0,
            execution_time_ms=elapsed,
        )

    counter = 0
    open_set: List[tuple] = [(0.0, counter, source)]

    dist: Dict[str, float] = {source: 0.0}
    came_from: Dict[str, str] = {}
    nodes_expanded = 0
    visited = set()

    while open_set:
        current_dist, _, current = heapq.heappop(open_set)

        if current in visited:
            continue
        visited.add(current)
        nodes_expanded += 1

        if current == destination:
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()

            elapsed = (time.perf_counter() - start_time) * 1000.0
            return PathfindingResult(
                path=path,
                total_cost=dist[destination],
                nodes_expanded=nodes_expanded,
                execution_time_ms=elapsed,
            )

        for neighbor in graph.adj.get(current, []):
            if neighbor in visited:
                continue

            edge = graph.get_edge(current, neighbor)
            tentative = current_dist + edge.road_duration_minutes

            if tentative < dist.get(neighbor, float("inf")):
                came_from[neighbor] = current
                dist[neighbor] = tentative
                counter += 1
                heapq.heappush(open_set, (tentative, counter, neighbor))

    elapsed = (time.perf_counter() - start_time) * 1000.0
    return PathfindingResult(
        path=[],
        total_cost=float("inf"),
        nodes_expanded=nodes_expanded,
        execution_time_ms=elapsed,
    )
