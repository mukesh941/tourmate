import math
from typing import Dict, Any

class RoutingService:
    def __init__(self):
        pass
        
    async def get_route(self, origin_lat: float, origin_lng: float, dest_lat: float, dest_lng: float, mode: str = "DRIVE") -> Dict[str, Any]:
        """
        Retrieves real road routing distance/duration via OSRM.
        Uses geographic Haversine as a fallback simulation if API is unavailable.
        """
        try:
            from app.services.osrm_service import calculate_route
            # OSRM prefers 'driving' as mode
            osrm_mode = "driving" if mode.upper() == "DRIVE" else "driving"
            route_res = await calculate_route(
                [{"lat": origin_lat, "lng": origin_lng}, {"lat": dest_lat, "lng": dest_lng}],
                mode=osrm_mode,
            )
            if route_res and "distance_km" in route_res:
                distance_km = route_res["distance_km"]
                duration_minutes = max(1, round(route_res["duration_minutes"]))
                hours = duration_minutes // 60
                mins = duration_minutes % 60
                duration_text = f"{hours} hr {mins} min" if hours > 0 else f"{mins} min"
                return {
                    "distance_km": round(distance_km, 1),
                    "duration_minutes": duration_minutes,
                    "duration_text": duration_text,
                    "travel_mode": mode,
                    "source": "osrm"
                }
        except Exception as e:
            print(f"OSRM Routing failed: {e}")

        # Haversine distance fallback
        r = 6371
        phi1 = math.radians(origin_lat)
        phi2 = math.radians(dest_lat)
        delta_phi = math.radians(dest_lat - origin_lat)
        delta_lambda = math.radians(dest_lng - origin_lng)
        
        a = math.sin(delta_phi/2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2.0)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance_km = r * c
        
        # Simulate road distance (usually ~1.3x straight line)
        road_distance = distance_km * 1.3
        
        # Simulate driving speed (avg 50 km/h in India)
        duration_hours = road_distance / 50.0
        duration_minutes = int(duration_hours * 60)
        
        hours = duration_minutes // 60
        mins = duration_minutes % 60
        duration_text = f"~{hours} hr {mins} min (Estimate)" if hours > 0 else f"~{mins} min (Estimate)"

        return {
            "distance_km": round(road_distance, 1),
            "duration_minutes": duration_minutes,
            "duration_text": duration_text,
            "travel_mode": mode,
            "source": "estimated fallback"
        }

routing_service = RoutingService()
