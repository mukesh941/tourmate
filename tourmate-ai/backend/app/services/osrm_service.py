"""
OSRM (Open Source Routing Machine) Service.
Provides authoritative real-world road routing, distances, durations, and GeoJSON geometries.
Features:
- Bounded retry with exponential backoff (0.5s, 1.0s, 2.0s; max 3 attempts).
- In-memory TTL caching for pairwise directed routes.
- Directed pairwise matrix collection for TSP / graph pathfinding.
- Explicit RoutingUnavailableError on failure (NEVER fabricates Haversine distance/time).
- Preserves backwards-compatible calculate_route() for /locations/route.
"""
import asyncio
import hashlib
import json
import time
from typing import Any, Dict, List, Optional, Tuple
import httpx

OSRM_BASE_URL = "http://router.project-osrm.org/route/v1"
NOMINATIM_BASE_URL = "https://nominatim.openstreetmap.org"
USER_AGENT = "TourMateAI/1.0"

# In-memory TTL cache for route queries (10 minutes)
_route_cache: Dict[str, Dict[str, Any]] = {}
OSRM_CACHE = _route_cache
CACHE_TTL_SECONDS = 600


class RoutingUnavailableError(Exception):
    """Raised when the routing provider is unreachable or fails after retries."""
    pass


def _cache_key(mode: str, coords: List[Tuple[float, float]]) -> str:
    rounded = [(round(lat, 5), round(lon, 5)) for lat, lon in coords]
    raw = json.dumps({"mode": mode, "coords": rounded})
    return hashlib.md5(raw.encode()).hexdigest()


def _get_cached_route(key: str) -> Optional[Dict[str, Any]]:
    entry = _route_cache.get(key)
    if entry and (time.time() - entry["ts"]) < CACHE_TTL_SECONDS:
        return entry["data"]
    return None


def _set_cached_route(key: str, data: Dict[str, Any]) -> None:
    _route_cache[key] = {"ts": time.time(), "data": data}


def _resolve_profile(mode: str) -> str:
    mode_lower = (mode or "driving").lower()
    if mode_lower in ("car", "driving"):
        return "driving"
    elif mode_lower in ("bike", "cycling"):
        return "cycling"
    elif mode_lower in ("walk", "walking", "foot"):
        return "foot"
    return "driving"


async def geocode(query: str) -> Optional[Dict[str, float]]:
    """
    Search for a location string and return its latitude/longitude using Nominatim.
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(
                f"{NOMINATIM_BASE_URL}/search",
                params={"q": query, "format": "json", "limit": 1},
                headers={"User-Agent": USER_AGENT},
            )
            response.raise_for_status()
            data = response.json()
            if data and len(data) > 0:
                return {
                    "latitude": float(data[0]["lat"]),
                    "longitude": float(data[0]["lon"]),
                    "display_name": data[0]["display_name"],
                }
            return None
        except Exception as e:
            print(f"Geocoding error: {e}")
            return None


async def reverse_geocode(lat: float, lon: float) -> Optional[str]:
    """
    Reverse geocode a coordinate into a human-readable address/city.
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(
                f"{NOMINATIM_BASE_URL}/reverse",
                params={"lat": lat, "lon": lon, "format": "json"},
                headers={"User-Agent": USER_AGENT},
            )
            response.raise_for_status()
            data = response.json()
            if data and "display_name" in data:
                addr = data.get("address", {})
                city = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("county")
                state = addr.get("state")
                if city and state:
                    return f"{city}, {state}"
                return data["display_name"]
            return None
        except Exception as e:
            print(f"Reverse geocoding error: {e}")
            return None


from app.services.graph_service import DirectedEdge, RouteNode, haversine


def _extract_node_info(node: Any) -> Tuple[str, float, float]:
    """Extracts (id, lat, lon) whether node is a RouteNode object or dict."""
    if isinstance(node, RouteNode):
        return node.id, node.latitude, node.longitude
    if isinstance(node, dict):
        lat = node.get("latitude") if "latitude" in node else node.get("lat")
        lon = node.get("longitude") if "longitude" in node else node.get("lon")
        return str(node["id"]), float(lat), float(lon)
    return str(getattr(node, "id")), float(getattr(node, "latitude")), float(getattr(node, "longitude"))


async def calculate_directed_route(
    origin_lat: float,
    origin_lon: float,
    dest_lat: float,
    dest_lon: float,
    mode: str = "driving",
    max_retries: int = 3,
) -> Dict[str, Any]:
    """
    Calculate an authoritative real-world road route between two coordinates.
    Applies bounded retry with exponential backoff (0.5s, 1.0s, 2.0s).
    Raises RoutingUnavailableError on persistent failure.
    NEVER falls back to fabricated or estimated Haversine values.
    """
    cache_k = _cache_key(mode, [(origin_lat, origin_lon), (dest_lat, dest_lon)])
    cached = _get_cached_route(cache_k)
    if cached:
        return cached

    profile = _resolve_profile(mode)
    coords_str = f"{origin_lon},{origin_lat};{dest_lon},{dest_lat}"
    url = f"{OSRM_BASE_URL}/{profile}/{coords_str}"

    backoff_delays = [0.5, 1.0, 2.0][:max_retries]
    last_error: Optional[Exception] = None

    async with httpx.AsyncClient(timeout=10.0) as client:
        for attempt, delay in enumerate(backoff_delays, start=1):
            try:
                response = await client.get(
                    url,
                    params={
                        "overview": "full",
                        "geometries": "geojson",
                        "steps": "true",
                    },
                    headers={"User-Agent": USER_AGENT},
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("code") == "Ok" and data.get("routes"):
                        route = data["routes"][0]
                        steps = []
                        for leg in route.get("legs", []):
                            for step in leg.get("steps", []):
                                inst = step.get("maneuver", {}).get("type", "")
                                mod = step.get("maneuver", {}).get("modifier", "")
                                name = step.get("name", "")
                                if inst == "turn":
                                    text = f"Turn {mod} onto {name}" if name else f"Turn {mod}"
                                elif inst == "depart":
                                    text = f"Head {mod} on {name}" if name else f"Head {mod}"
                                elif inst == "arrive":
                                    text = "Arrive at destination"
                                else:
                                    text = f"Continue on {name}" if name else "Continue"

                                steps.append({
                                    "instruction": text,
                                    "distance_m": step.get("distance", 0.0),
                                    "duration_s": step.get("duration", 0.0),
                                    "location": step.get("maneuver", {}).get("location", []),
                                })

                        result = {
                            "distance_km": round(route["distance"] / 1000.0, 3),
                            "duration_minutes": round(route["duration"] / 60.0, 2),
                            "duration_seconds": float(route["duration"]),
                            "transport_mode": profile,
                            "geometry": route["geometry"],
                            "steps": steps,
                            "origin": {"latitude": origin_lat, "longitude": origin_lon},
                            "destination": {"latitude": dest_lat, "longitude": dest_lon},
                        }
                        _set_cached_route(cache_k, result)
                        return result
                    else:
                        raise RoutingUnavailableError(
                            f"OSRM returned non-OK status: {data.get('code')}"
                        )
                else:
                    raise RoutingUnavailableError(
                        f"OSRM returned HTTP {response.status_code}: {response.text[:100]}"
                    )
            except Exception as exc:
                last_error = exc
                if attempt < len(backoff_delays):
                    await asyncio.sleep(delay)

    raise RoutingUnavailableError(
        f"Routing service is unavailable after {max_retries} attempts ({origin_lat},{origin_lon} -> {dest_lat},{dest_lon}): {last_error}"
    )


async def get_osrm_directed_route(
    u: Any,
    v: Any,
    mode: str = "driving",
    max_retries: int = 3,
) -> DirectedEdge:
    """
    Computes an authoritative DirectedEdge between node u and node v.
    """
    u_id, u_lat, u_lon = _extract_node_info(u)
    v_id, v_lat, v_lon = _extract_node_info(v)

    raw = await calculate_directed_route(
        origin_lat=u_lat,
        origin_lon=u_lon,
        dest_lat=v_lat,
        dest_lon=v_lon,
        mode=mode,
        max_retries=max_retries,
    )

    h_dist = haversine(u_lat, u_lon, v_lat, v_lon)

    return DirectedEdge(
        from_id=u_id,
        to_id=v_id,
        road_distance_km=float(raw["distance_km"]),
        road_duration_minutes=float(raw["duration_minutes"]),
        geometry=raw.get("geometry"),
        haversine_distance_km=h_dist,
        steps=raw.get("steps", []),
    )


async def get_directed_pairwise_matrix(
    nodes: List[Any],
    mode: str = "driving",
) -> Dict[Tuple[str, str], DirectedEdge]:
    """
    Computes directed pairwise road routes between all unique pairs in nodes list.
    Accepts list of RouteNode objects or dicts.
    Returns mapping: (u_id, v_id) -> DirectedEdge
    """
    matrix: Dict[Tuple[str, str], DirectedEdge] = {}
    n = len(nodes)

    tasks = []
    keys = []

    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            u = nodes[i]
            v = nodes[j]
            u_id, _, _ = _extract_node_info(u)
            v_id, _, _ = _extract_node_info(v)
            keys.append((u_id, v_id))
            tasks.append(get_osrm_directed_route(u, v, mode=mode))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    for (u_id, v_id), res in zip(keys, results):
        if isinstance(res, Exception):
            raise RoutingUnavailableError(
                f"Failed to calculate directed route between '{u_id}' and '{v_id}': {res}"
            )
        matrix[(u_id, v_id)] = res

    return matrix



async def calculate_route(
    coordinates: List[Dict[str, float]],
    mode: str = "driving",
) -> Optional[Dict[str, Any]]:
    """
    Backwards-compatible wrapper preserving existing POST /locations/route contract
    for RoutePlannerView.jsx.
    """
    if len(coordinates) < 2:
        return None

    try:
        profile = _resolve_profile(mode)
        coords_str = ";".join([f"{c['longitude']},{c['latitude']}" for c in coordinates])
        url = f"{OSRM_BASE_URL}/{profile}/{coords_str}"

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                url,
                params={"overview": "full", "geometries": "geojson", "steps": "true"},
                headers={"User-Agent": USER_AGENT},
            )
            if response.status_code != 200:
                return None
            data = response.json()
            if data.get("code") != "Ok" or not data.get("routes"):
                return None

            route = data["routes"][0]
            steps = []
            for leg in route.get("legs", []):
                for step in leg.get("steps", []):
                    inst = step.get("maneuver", {}).get("type", "")
                    mod = step.get("maneuver", {}).get("modifier", "")
                    name = step.get("name", "")
                    if inst == "turn":
                        text = f"Turn {mod} onto {name}" if name else f"Turn {mod}"
                    elif inst == "depart":
                        text = f"Head {mod} on {name}" if name else f"Head {mod}"
                    elif inst == "arrive":
                        text = "Arrive at destination"
                    else:
                        text = f"Continue on {name}" if name else "Continue"

                    steps.append({
                        "instruction": text,
                        "distance_m": step.get("distance", 0.0),
                        "duration_s": step.get("duration", 0.0),
                        "location": step.get("maneuver", {}).get("location", []),
                    })

            return {
                "distance": round(route["distance"] / 1000.0, 2),
                "distance_km": round(route["distance"] / 1000.0, 2),
                "duration": round(route["duration"] / 60.0, 2),
                "duration_minutes": round(route["duration"] / 60.0, 2),
                "transport_mode": mode,
                "geometry": route["geometry"],
                "steps": steps,
                "origin": coordinates[0],
                "destination": coordinates[-1],
                "stops": coordinates[1:-1] if len(coordinates) > 2 else [],
            }
    except Exception as e:
        print(f"OSRM Routing error: {e}")
        return None
