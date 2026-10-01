import logging
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.location_service import (
    search_postgres_locations,
    geocode_with_nominatim as nominatim_geocode,
    _apply_typomap
)
from app.services.osrm_service import reverse_geocode as nominatim_reverse_geocode

logger = logging.getLogger(__name__)

class GeocodingProvider:
    async def resolve_location(self, loc_name: str, db: AsyncSession) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    async def geocode(self, query: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError
        
    async def reverse_geocode(self, lat: float, lng: float) -> Optional[str]:
        raise NotImplementedError

class TourmateGeocodingProvider(GeocodingProvider):
    async def resolve_location(self, loc_name: str, db: AsyncSession) -> Optional[Dict[str, Any]]:
        if not loc_name or loc_name.lower().strip() == "me":
            return None

        from app.services.destination_resolver import resolve_destination
        resolved = await resolve_destination(loc_name, db)
        
        if resolved and resolved.get("latitude") and resolved.get("longitude"):
            return {
                "query": loc_name,
                "resolved": True,
                "source": "tourmate_database",
                "name": resolved.get("name"),
                "display_name": f"{resolved.get('name')}, {resolved.get('state', '')}".strip(', '),
                "location_type": resolved.get("location_type", "poi"),
                "city": resolved.get("city"),
                "state": resolved.get("state"),
                "country": resolved.get("country"),
                "latitude": resolved.get("latitude"),
                "longitude": resolved.get("longitude"),
                "location_id": str(resolved.get("id")) if resolved.get("id") else None,
            }

        # 2. Try Nominatim Fallback
        osm_result = await self.geocode(loc_name)
        if osm_result:
            return {
                "query": loc_name,
                "resolved": True,
                "source": "openstreetmap",
                "name": osm_result.get("name") or loc_name,
                "display_name": osm_result.get("display_name"),
                "latitude": osm_result.get("lat"),
                "longitude": osm_result.get("lng"),
                "city": osm_result.get("city"),
                "state": osm_result.get("state"),
                "country": osm_result.get("country"),
            }
            
        logger.info("Could not resolve location '%s' from any provider", loc_name)
        return None

    async def geocode(self, query: str) -> Optional[Dict[str, Any]]:
        return await nominatim_geocode(query, country_bias="")
        
    async def reverse_geocode(self, lat: float, lng: float) -> Optional[str]:
        return await nominatim_reverse_geocode(lat, lng)

geocoder = TourmateGeocodingProvider()

async def resolve_location(loc_name: str, db: AsyncSession) -> Optional[Dict[str, Any]]:
    return await geocoder.resolve_location(loc_name, db)

async def geocode(query: str) -> Optional[Dict[str, Any]]:
    return await geocoder.geocode(query)

async def reverse_geocode(lat: float, lng: float) -> Optional[str]:
    return await geocoder.reverse_geocode(lat, lng)
