"""
Internal Directed Route Graph for Phase 4 Itinerary Optimization.
Maintains nodes (Accommodation Anchor + Day POIs) and directed edges (authoritative road costs).
Provides admissible Haversine-over-speed heuristic for A* pathfinding.
Zero external graph library dependencies (pure Python).
"""
import math
from dataclasses import dataclass, field
from datetime import time as dt_time
from typing import Any, Dict, List, Optional, Set, Tuple

from app.core.config import settings


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two geographic coordinates in km."""
    R = 6371.0  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


@dataclass
class RouteNode:
    id: str
    name: str
    latitude: float
    longitude: float
    visit_duration_minutes: int = 60
    is_anchor: bool = False
    open_time: Optional[dt_time] = None
    close_time: Optional[dt_time] = None
    is_closed: bool = False


@dataclass
class DirectedEdge:
    from_id: str
    to_id: str
    road_distance_km: float
    road_duration_minutes: float
    geometry: Optional[Dict[str, Any]] = None
    haversine_distance_km: float = 0.0
    steps: List[Dict[str, Any]] = field(default_factory=list)


class InternalRouteGraph:
    """
    Lightweight in-memory directed graph representing a single day's tour problem.
    Nodes: Accommodation Anchor (A) + Day Sightseeing POIs (P_1 .. P_m).
    Edges: Authoritative directed OSRM road routes between pairs.
    """

    def __init__(self, v_max_kmh: Optional[float] = None):
        self.nodes: Dict[str, RouteNode] = {}
        self.edges: Dict[Tuple[str, str], DirectedEdge] = {}
        self.adj: Dict[str, List[str]] = {}
        # Authoritative configured maximum road speed in km/h
        self.v_max_kmh: float = (
            v_max_kmh if v_max_kmh is not None else settings.routing_v_max_kmh
        )

    def add_node(self, node: RouteNode) -> None:
        self.nodes[node.id] = node
        if node.id not in self.adj:
            self.adj[node.id] = []

    def add_edge(self, edge: DirectedEdge) -> None:
        if edge.from_id not in self.nodes or edge.to_id not in self.nodes:
            raise ValueError(
                f"Cannot add edge between unregistered nodes: {edge.from_id} -> {edge.to_id}"
            )
        self.edges[(edge.from_id, edge.to_id)] = edge
        if edge.to_id not in self.adj[edge.from_id]:
            self.adj[edge.from_id].append(edge.to_id)

    def get_edge(self, from_id: str, to_id: str) -> DirectedEdge:
        edge = self.edges.get((from_id, to_id))
        if edge is None:
            raise KeyError(f"No directed edge exists from '{from_id}' to '{to_id}'")
        return edge

    def has_edge(self, from_id: str, to_id: str) -> bool:
        return (from_id, to_id) in self.edges

    def get_node(self, node_id: str) -> RouteNode:
        node = self.nodes.get(node_id)
        if node is None:
            raise KeyError(f"No node exists with id '{node_id}'")
        return node

    def heuristic(self, u_id: str, goal_id: str) -> float:
        """
        Admissible heuristic function for A* pathfinding.
        h(u) = Haversine(u, goal) / (v_max_kmh / 60)
        Units: travel time in minutes.
        Guaranteed admissible because:
        1. Road distance >= Haversine distance.
        2. Real road travel speed <= v_max_kmh.
        Therefore h(u) <= actual optimal road duration g*(u, goal).
        """
        if u_id == goal_id:
            return 0.0

        u = self.nodes[u_id]
        goal = self.nodes[goal_id]
        h_dist = haversine(u.latitude, u.longitude, goal.latitude, goal.longitude)
        # Convert km/h to km/min
        speed_km_per_min = max(self.v_max_kmh / 60.0, 1e-4)
        return h_dist / speed_km_per_min

    @property
    def node_count(self) -> int:
        return len(self.nodes)

    @property
    def edge_count(self) -> int:
        return len(self.edges)
