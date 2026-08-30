import math
import heapq
from typing import List, Tuple
from app.schemas.place import TouristPlaceResponse

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0 # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def optimize_route(places: List[TouristPlaceResponse]) -> Tuple[List[TouristPlaceResponse], float]:
    """
    Uses Nearest Neighbor followed by 2-opt to find a short path visiting all given places exactly once.
    Assumes the first place in the list is the starting point.
    Scales efficiently for large datasets without capping.
    """
    if not places or len(places) <= 1:
        return places, 0.0

    n = len(places)
    
    # Extract coordinates
    coords = []
    for p in places:
        if p.location and p.location.coordinates and len(p.location.coordinates) >= 2:
            coords.append((p.location.coordinates[1], p.location.coordinates[0])) # lat, lng
        else:
            coords.append((0.0, 0.0))
            
    # Precompute distance matrix
    dist = [[0.0 for _ in range(n)] for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                dist[i][j] = haversine(coords[i][0], coords[i][1], coords[j][0], coords[j][1])

    # 1. Nearest Neighbor heuristic
    unvisited = set(range(1, n))
    route = [0]
    current = 0
    total_dist = 0.0
    
    while unvisited:
        next_node = min(unvisited, key=lambda x: dist[current][x])
        total_dist += dist[current][next_node]
        route.append(next_node)
        unvisited.remove(next_node)
        current = next_node

    # 2. 2-opt optimization
    improved = True
    while improved:
        improved = False
        for i in range(1, n - 1):
            for j in range(i + 1, n):
                if j - i == 1: continue
                # Calculate current distance of edges (i-1, i) and (j, j+1 if j+1 < n)
                # If j is the last node, there is no edge (j, j+1)
                
                # Edges to remove: (i-1, i) and (j, j+1)
                d1 = dist[route[i-1]][route[i]]
                d2 = dist[route[j]][route[j+1]] if j+1 < n else 0
                
                # Edges to add: (i-1, j) and (i, j+1)
                new_d1 = dist[route[i-1]][route[j]]
                new_d2 = dist[route[i]][route[j+1]] if j+1 < n else 0
                
                if d1 + d2 > new_d1 + new_d2:
                    # Reverse the segment between i and j
                    route[i:j+1] = reversed(route[i:j+1])
                    improved = True

    # Recalculate total distance after 2-opt
    final_dist = 0.0
    for i in range(n - 1):
        final_dist += dist[route[i]][route[i+1]]

    optimized_places = [places[i] for i in route]
    return optimized_places, final_dist
