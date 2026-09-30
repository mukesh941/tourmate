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

        corrected = _apply_typomap(loc_name)

        # 1. Try PostgreSQL TourMate DB
        db_locs = await search_postgres_locations(corrected, db, exact_only=True)
        if not db_locs and corrected != loc_name:
            db_locs = await search_postgres_locations(loc_name, db, exact_only=True)

        if db_locs:
            loc = db_locs[0]
            canonical = loc.get("canonical_name") or loc.get("name") if isinstance(loc, dict) else (getattr(loc, 'canonical_name', None) or getattr(loc, 'name', None))
            return {
                "query": loc_name,
                "resolved": True,
                "source": "tourmate_database",
                "name": canonical,
                "location_type": loc.get("location_type", "poi") if isinstance(loc, dict) else getattr(loc, "location_type", "poi"),
                "city": loc.get("city") if isinstance(loc, dict) else getattr(loc, 'city', None),
                "state": loc.get("state") if isinstance(loc, dict) else getattr(loc, 'state', None),
                "country": loc.get("country") if isinstance(loc, dict) else getattr(loc, 'country', None),
                "latitude": loc.get("lat") if isinstance(loc, dict) else getattr(loc, 'latitude', None),
                "longitude": loc.get("lng") if isinstance(loc, dict) else getattr(loc, 'longitude', None),
                "location_id": str(loc.get("id")) if isinstance(loc, dict) else str(getattr(loc, 'id', None))
            }

        # 2. Try Nominatim Fallback
        osm_result = await self.geocode(corrected)
        if osm_result:
            return {
                "query": loc_name,
                "resolved": True,
                "source": "openstreetmap",
                "name": osm_result["name"] or corrected,
                "display_name": osm_result.get("display_name"),
                "latitude": osm_result["lat"],
                "longitude": osm_result["lng"],
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
