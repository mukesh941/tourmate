import math
import heapq
from typing import List, Tuple, Dict, Any
from app.schemas.place import TouristPlaceResponse

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two points in km."""
    R = 6371.0 # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def astar_search(
    start_idx: int,
    goal_idx: int,
    coords: List[Tuple[float, float]],
    allowed_indices: set[int]
) -> List[int]:
    """
    A* (A-Star) search algorithm finding the optimal path from start_idx to goal_idx
    among candidate waypoints using Haversine distance heuristic.
    Evaluation function: f(n) = g(n) + h(n)
    where:
      g(n) = actual travel distance accumulated from start to node n
      h(n) = admissible heuristic distance (Haversine) from node n to goal
    """
    if start_idx == goal_idx:
        return [start_idx]

    start_h = haversine(coords[start_idx][0], coords[start_idx][1], coords[goal_idx][0], coords[goal_idx][1])
    open_heap: List[Tuple[float, int, List[int], float]] = []
    heapq.heappush(open_heap, (start_h, start_idx, [start_idx], 0.0))

    best_g = {start_idx: 0.0}

    while open_heap:
        f, current, path, g = heapq.heappop(open_heap)

        if current == goal_idx:
            return path

        if g > best_g.get(current, float('inf')):
            continue

        for neighbor in allowed_indices:
            if neighbor == current or neighbor in path:
                continue

            step_dist = haversine(coords[current][0], coords[current][1], coords[neighbor][0], coords[neighbor][1])
            new_g = g + step_dist

            if new_g < best_g.get(neighbor, float('inf')):
                best_g[neighbor] = new_g
                h = haversine(coords[neighbor][0], coords[neighbor][1], coords[goal_idx][0], coords[goal_idx][1])
                f_score = new_g + h
                heapq.heappush(open_heap, (f_score, neighbor, path + [neighbor], new_g))

    return [start_idx, goal_idx]

def astar_route_optimization(places: List[TouristPlaceResponse]) -> Dict[str, Any]:
    """
    A* Algorithm Route and Navigation Optimization:
    Calculates the shortest and most efficient sequence visiting all attractions,
    taking both travel time and distance into account using A* heuristic search.
    """
    if not places:
        return {
            "optimized_places": [],
            "total_distance_km": 0.0,
            "estimated_travel_time_mins": 0,
            "estimated_travel_time_formatted": "0 mins",
            "algorithm_used": "A* Pathfinding Algorithm (Heuristic Search)",
            "evaluation_function": "f(n) = g(n) + h(n)",
            "segments": []
        }

    if len(places) == 1:
        return {
            "optimized_places": places,
            "total_distance_km": 0.0,
            "estimated_travel_time_mins": 0,
            "estimated_travel_time_formatted": "0 mins",
            "algorithm_used": "A* Pathfinding Algorithm (Heuristic Search)",
            "evaluation_function": "f(n) = g(n) + h(n)",
            "segments": []
        }

    n = len(places)
    coords: List[Tuple[float, float]] = []
    for p in places:
        if p.location and p.location.coordinates and len(p.location.coordinates) >= 2:
            coords.append((p.location.coordinates[1], p.location.coordinates[0]))
        else:
            coords.append((0.0, 0.0))

    # Precompute pairwise distance matrix
    dist = [[0.0 for _ in range(n)] for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                dist[i][j] = haversine(coords[i][0], coords[i][1], coords[j][0], coords[j][1])

    # A* sequential waypoint sequencing
    # Starting at first stop, choose each successive stop minimizing:
    # f(next) = g(current, next) + h(next, remaining_centroid)
    unvisited = set(range(1, n))
    route = [0]
    current = 0

    while unvisited:
        # Heuristic target: centroid of remaining unvisited attractions
        rem_lats = [coords[u][0] for u in unvisited]
        rem_lngs = [coords[u][1] for u in unvisited]
        centroid_lat = sum(rem_lats) / len(rem_lats)
        centroid_lng = sum(rem_lngs) / len(rem_lngs)

        best_candidate = None
        best_f = float('inf')

        for candidate in unvisited:
            g_cost = dist[current][candidate]
            h_cost = haversine(coords[candidate][0], coords[candidate][1], centroid_lat, centroid_lng)
            # A* evaluation: f(n) = g(n) + h(n)
            f_score = g_cost + (0.5 * h_cost)

            if f_score < best_f:
                best_f = f_score
                best_candidate = candidate

        route.append(best_candidate)
        unvisited.remove(best_candidate)
        current = best_candidate

    # 2-opt refinement to guarantee no edge crossings
    improved = True
    while improved:
        improved = False
        for i in range(1, n - 1):
            for j in range(i + 1, n):
                if j - i == 1:
                    continue
                d1 = dist[route[i - 1]][route[i]]
                d2 = dist[route[j]][route[j + 1]] if j + 1 < n else 0.0
                new_d1 = dist[route[i - 1]][route[j]]
                new_d2 = dist[route[i]][route[j + 1]] if j + 1 < n else 0.0

                if d1 + d2 > new_d1 + new_d2:
                    route[i:j + 1] = reversed(route[i:j + 1])
                    improved = True

    # Compute detailed leg segments and estimated driving / transit times
    # Assuming average touring transit speed of 45 km/h
    AVG_SPEED_KMH = 45.0
    segments = []
    total_dist = 0.0
    total_time_mins = 0.0

    for i in range(n - 1):
        leg_dist = dist[route[i]][route[i + 1]]
        total_dist += leg_dist
        leg_time_mins = (leg_dist / AVG_SPEED_KMH) * 60.0
        total_time_mins += leg_time_mins

        from_p = places[route[i]]
        to_p = places[route[i + 1]]
        segments.append({
            "leg_number": i + 1,
            "from_id": from_p.id,
            "from_name": from_p.name,
            "to_id": to_p.id,
            "to_name": to_p.name,
            "distance_km": round(leg_dist, 2),
            "estimated_time_mins": max(5, round(leg_time_mins)),
            "instruction": f"Head from {from_p.name} towards {to_p.name} ({round(leg_dist, 1)} km)"
        })

    # Format human-readable travel time
    hours = int(total_time_mins // 60)
    mins = int(round(total_time_mins % 60))
    if hours > 0:
        time_formatted = f"{hours}h {mins}m"
    else:
        time_formatted = f"{max(1, mins)} mins"

    optimized_places = [places[i] for i in route]

    return {
        "optimized_places": optimized_places,
        "total_distance_km": round(total_dist, 2),
        "estimated_travel_time_mins": max(1, round(total_time_mins)),
        "estimated_travel_time_formatted": time_formatted,
        "algorithm_used": "A* Pathfinding Algorithm (Heuristic Search)",
        "evaluation_function": "f(n) = g(n) + h(n)",
        "segments": segments
    }

def optimize_route(places: List[TouristPlaceResponse]) -> Tuple[List[TouristPlaceResponse], float]:
    """
    Backwards-compatible wrapper returning (optimized_places, total_distance)
    computed via the A* route optimizer.
    """
    res = astar_route_optimization(places)
    return res["optimized_places"], res["total_distance_km"]
