"""
Pydantic schemas for Phase 4 Routing & Itinerary Optimization.
Strictly conforms to the locked 23-table PostgreSQL schema contracts.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DayClusterInput(BaseModel):
    day_number: int = Field(..., ge=1, le=30, description="1-indexed day of the trip")
    poi_ids: List[str] = Field(..., min_items=1, description="List of POI UUIDs assigned to this day")


class ItineraryOptimizePlanRequest(BaseModel):
    trip_id: str = Field(..., description="UUID of the Trip")
    day_clusters: Optional[List[DayClusterInput]] = Field(
        default=None,
        description="Optional explicit day-to-POIs mapping. If omitted, fetched from database poi_clusters.",
    )
    transport_mode: str = Field(
        default="driving",
        description="Transport mode: driving, walking, or cycling",
    )
    daily_start_time: str = Field(
        default="09:00",
        pattern=r"^\d{2}:\d{2}$",
        description="Daily tour start time in HH:MM format",
    )
    title: Optional[str] = Field(
        default=None,
        description="Optional custom title for the generated itinerary plan",
    )


class StopTimelineItem(BaseModel):
    stop_id: Optional[str] = None
    poi_id: str
    name: str
    arrival_time: str
    departure_time: str
    visit_duration_minutes: int
    stop_order: int


class RouteLegSchema(BaseModel):
    route_id: Optional[str] = None
    from_node_id: str
    to_node_id: str
    source_stop_id: Optional[str] = None
    target_stop_id: Optional[str] = None
    distance_km: float
    duration_minutes: int
    geometry: Optional[Dict[str, Any]] = None
    is_mock: bool = False


class AlternativeTourSummary(BaseModel):
    description: str
    total_distance_km: float
    total_travel_time_minutes: int
    tour_node_ids: List[str]


class PathfindingBenchmarkMetrics(BaseModel):
    source_node_id: str
    target_node_id: str
    astar_cost_minutes: float
    dijkstra_cost_minutes: float
    cost_difference: float
    astar_nodes_expanded: int
    dijkstra_nodes_expanded: int
    astar_execution_time_ms: float
    dijkstra_execution_time_ms: float


class DayOptimizationResult(BaseModel):
    day_number: int
    tour: List[str]
    timeline: List[StopTimelineItem]
    legs: List[RouteLegSchema]
    total_distance_km: float
    total_duration_minutes: float
    is_feasible: bool
    warnings: List[str]
    alternative_tour: Optional[AlternativeTourSummary] = None
    benchmark: Optional[PathfindingBenchmarkMetrics] = None


class ItineraryOptimizePlanResponse(BaseModel):
    itinerary_id: str
    trip_id: str
    name: str
    total_distance_km: float
    total_travel_time_minutes: int
    days: List[DayOptimizationResult]
