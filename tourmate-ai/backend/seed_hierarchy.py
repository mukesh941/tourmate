import asyncio
import json
import logging
import uuid
import httpx
from sqlalchemy import select
from app.core.db import AsyncSessionLocal
from app.models.sql.location import Location

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def geocode_nominatim(name, state=""):
    query = f"{name}, {state}, India" if state else f"{name}, India"
    logger.info(f"Geocoding {query}")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": query, "format": "json", "limit": 1},
                headers={"User-Agent": "TourMate-Seeder/1.0"}
            )
            data = resp.json()
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception as e:
        logger.error(f"Failed to geocode {query}: {e}")
    return None, None

async def run_seed():
    with open("indian_districts.json", "r", encoding="utf-8") as f:
        districts_data = json.load(f)["states"]
    
    with open("world_cities.json", "r", encoding="utf-8") as f:
        world_cities = json.load(f)
    
    # Filter Indian cities and map by lowercase name
    indian_cities = {}
    for c in world_cities:
        if c.get("country") == "IN":
            name = c["name"].lower()
            if name not in indian_cities:
                indian_cities[name] = []
            indian_cities[name].append({
                "name": c["name"],
                "lat": float(c["lat"]),
                "lng": float(c["lng"])
            })

    async with AsyncSessionLocal() as session:
        # Load existing locations
        existing_locs = (await session.execute(select(Location))).scalars().all()
        loc_map = {loc.name.lower(): loc for loc in existing_locs}
        
        # Skip states and districts for speed
        """
        # 1. Create States
        logger.info("Processing States...")
        for state_data in districts_data:
            state_name = state_data["state"]
            state_lower = state_name.lower()
            
            if state_lower in loc_map:
                state_loc = loc_map[state_lower]
                state_loc.location_type = "state"
            else:
                lat, lng = await geocode_nominatim(state_name)
                await asyncio.sleep(1.1)
                if lat is None:
                    lat, lng = 20.0, 77.0 # Fallback
                
                state_loc = Location(
                    name=state_name,
                    canonical_name=state_name,
                    city="",
                    state=state_name,
                    country="India",
                    latitude=lat,
                    longitude=lng,
                    location_type="state",
                    category="State"
                )
                session.add(state_loc)
                loc_map[state_lower] = state_loc
        
        await session.commit()
        
        # Reload to get generated IDs
        existing_locs = (await session.execute(select(Location))).scalars().all()
        loc_map = {loc.name.lower(): loc for loc in existing_locs}
        
        # 2. Create Districts
        logger.info("Processing Districts...")
        for state_data in districts_data:
            state_name = state_data["state"]
            state_loc = loc_map.get(state_name.lower())
            
            for district_name in state_data["districts"]:
                dist_lower = district_name.lower()
                
                # Try to find coords from cities matching district name
                lat, lng = None, None
                if dist_lower in indian_cities:
                    lat = indian_cities[dist_lower][0]["lat"]
                    lng = indian_cities[dist_lower][0]["lng"]
                else:
                    lat, lng = await geocode_nominatim(district_name, state_name)
                    await asyncio.sleep(1.1)
                
                if lat is None:
                    continue # Skip if no coords
                
                if dist_lower in loc_map:
                    dist_loc = loc_map[dist_lower]
                    if dist_loc.location_type not in ("state", "city", "tourist_destination"):
                        dist_loc.location_type = "district"
                    dist_loc.parent_id = state_loc.id if state_loc else None
                    dist_loc.district = district_name
                else:
                    dist_loc = Location(
                        name=district_name,
                        canonical_name=district_name,
                        city="",
                        district=district_name,
                        state=state_name,
                        country="India",
                        latitude=lat,
                        longitude=lng,
                        location_type="district",
                        category="District",
                        parent_id=state_loc.id if state_loc else None
                    )
                    session.add(dist_loc)
                    loc_map[dist_lower] = dist_loc
                    
        await session.commit()
        """
        # Reload
        existing_locs = (await session.execute(select(Location))).scalars().all()
        loc_map = {loc.name.lower(): loc for loc in existing_locs}
        
        # 3. Create Cities
        logger.info("Processing Cities...")
        city_count = 0
        for city_lower, city_list in indian_cities.items():
            for cdata in city_list:
                name = cdata["name"]
                lat = cdata["lat"]
                lng = cdata["lng"]
                
                # Check if exists
                if city_lower not in loc_map:
                    # Find a state parent (world_cities doesn't give us clear state names easily, but we can try)
                    # For simplicity, we just add the city. The user can search it by coords.
                    city_loc = Location(
                        name=name,
                        canonical_name=name,
                        city=name,
                        country="India",
                        latitude=lat,
                        longitude=lng,
                        location_type="city",
                        category="City"
                    )
                    session.add(city_loc)
                    loc_map[city_lower] = city_loc
                    city_count += 1
                    
        await session.commit()
        logger.info(f"Added {city_count} new cities.")
        
        # Reload
        existing_locs = (await session.execute(select(Location))).scalars().all()
        loc_map = {loc.name.lower(): loc for loc in existing_locs}
        
        # 4. Process existing 247 tourist destinations and set their parent_id
        logger.info("Updating existing POIs/Destinations...")
        for loc in existing_locs:
            if loc.location_type == "poi" or not loc.location_type:
                # Determine if it's a known city
                if loc.name.lower() in indian_cities and loc.city:
                    loc.location_type = "city"
                    # Parent is district or state
                    dist_key = loc.district.lower() if loc.district else ""
                    state_key = loc.state.lower() if loc.state else ""
                    
                    if dist_key and dist_key in loc_map and loc_map[dist_key].location_type == "district":
                        loc.parent_id = loc_map[dist_key].id
                    elif state_key and state_key in loc_map:
                        loc.parent_id = loc_map[state_key].id
                else:
                    loc.location_type = "tourist_destination"
                    # Parent is city
                    city_key = loc.city.lower() if loc.city else ""
                    if city_key and city_key in loc_map:
                        loc.parent_id = loc_map[city_key].id
        
        await session.commit()
        logger.info("Hierarchy seeding complete!")

if __name__ == "__main__":
    asyncio.run(run_seed())
