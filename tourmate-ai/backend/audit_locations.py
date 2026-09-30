import asyncio
import uuid
import json
from sqlalchemy import select, func
from app.core.db import AsyncSessionLocal
from app.models.sql.location import Location
from app.models.sql.poi import POI
from app.models.sql.category import Category

async def audit():
    async with AsyncSessionLocal() as session:
        # 1. Total locations
        total_locs = await session.scalar(select(func.count()).select_from(Location))
        
        # States and UTs predefined
        indian_states = {
            "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", 
            "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", 
            "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram", 
            "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", 
            "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal"
        }
        indian_uts = {
            "Andaman and Nicobar Islands", "Chandigarh", "Dadra and Nagar Haveli and Daman and Diu",
            "Lakshadweep", "Delhi", "Puducherry", "Ladakh", "Jammu and Kashmir"
        }
        
        # Fetch all locations
        locs = (await session.execute(select(Location))).scalars().all()
        pois = (await session.execute(select(POI))).scalars().all()
        
        # Categories mapping
        locs_by_state = {s: [] for s in indian_states}
        locs_by_ut = {u: [] for u in indian_uts}
        
        districts = set()
        cities = {}
        towns = 0
        tourist_destinations = {}
        hill_stations = 0
        beaches = 0
        pilgrimage = 0
        missing_coords = []
        valid_coords = 0
        duplicate_names = {}
        
        # Categorize
        for loc in locs:
            # Check coords
            if not loc.latitude or not loc.longitude or (loc.latitude == 0 and loc.longitude == 0):
                missing_coords.append(loc.name)
            else:
                valid_coords += 1
                
            # State/UT assignments
            s_name = loc.state.strip()
            ut_name = loc.union_territory.strip()
            assigned = False
            for s in indian_states:
                if s.lower() in s_name.lower():
                    locs_by_state[s].append(loc)
                    assigned = True
                    break
            if not assigned:
                for u in indian_uts:
                    if u.lower() in s_name.lower() or u.lower() in ut_name.lower() or u.lower() in loc.city.lower():
                        locs_by_ut[u].append(loc)
                        assigned = True
                        break
            
            # Duplicates
            duplicate_names[loc.name.lower()] = duplicate_names.get(loc.name.lower(), 0) + 1
            
            # Districts
            if loc.district:
                districts.add(loc.district.lower())
                
            cat = loc.category.lower() if loc.category else ""
            if "city" in cat or loc.city:
                state_key = loc.state or loc.union_territory or "Unknown"
                if state_key not in cities: cities[state_key] = set()
                cities[state_key].add(loc.city if loc.city else loc.name)
                
            if "town" in cat: towns += 1
            if "hill" in cat: hill_stations += 1
            if "beach" in cat: beaches += 1
            if "pilgrimage" in cat or "temple" in cat: pilgrimage += 1
            
            # Tourist Destination tracking
            state_key = loc.state or loc.union_territory or "Unknown"
            if state_key not in tourist_destinations: tourist_destinations[state_key] = set()
            tourist_destinations[state_key].add(loc.name)
        
        # POIs
        total_pois = len(pois)
        
        # Build Report
        with open("location_audit_report.md", "w", encoding="utf-8") as f:
            f.write("# TourMate India Location Database Audit\n\n")
            
            f.write("## 1. Overview\n")
            f.write(f"- **Total number of locations**: {total_locs}\n")
            f.write(f"- **Number of states covered**: {sum(1 for v in locs_by_state.values() if v)}/28\n")
            f.write(f"- **Number of UTs covered**: {sum(1 for v in locs_by_ut.values() if v)}/8\n")
            f.write(f"- **Number of districts**: {len(districts)}\n")
            f.write(f"- **Number of distinct cities**: {sum(len(c) for c in cities.values())}\n")
            f.write(f"- **Number of towns**: {towns}\n")
            f.write(f"- **Number of tourist destinations**: {total_locs}\n")
            f.write(f"- **Number of hill stations**: {hill_stations}\n")
            f.write(f"- **Number of beaches**: {beaches}\n")
            f.write(f"- **Number of pilgrimage destinations**: {pilgrimage}\n")
            f.write(f"- **Number of POIs/attractions**: {total_pois}\n")
            f.write(f"- **Locations with coordinates**: {valid_coords}\n")
            f.write(f"- **Locations missing coordinates**: {len(missing_coords)}\n\n")
            
            f.write("## 2. State Coverage\n")
            f.write("| State | Covered | Number of Locations |\n")
            f.write("|---|---|---|\n")
            for state in sorted(indian_states):
                count = len(locs_by_state[state])
                f.write(f"| {state} | {'Yes' if count > 0 else 'No'} | {count} |\n")
            f.write("\n")
            
            f.write("## 3. Union Territory Coverage\n")
            f.write("| UT | Covered | Number of Locations |\n")
            f.write("|---|---|---|\n")
            for ut in sorted(indian_uts):
                count = len(locs_by_ut[ut])
                f.write(f"| {ut} | {'Yes' if count > 0 else 'No'} | {count} |\n")
            f.write("\n")
            
            f.write("## 4. City Coverage\n")
            for state, c_list in sorted(cities.items()):
                f.write(f"**{state}**\n")
                f.write(f"- {', '.join(sorted(c_list))}\n\n")
                
            f.write("## 5. Tourist Destination Coverage\n")
            for state, d_list in sorted(tourist_destinations.items()):
                f.write(f"**{state}**\n")
                f.write(f"- {', '.join(sorted(d_list))}\n\n")
                
            f.write("## 6. Data Quality & Anomalies\n")
            dups = [name for name, c in duplicate_names.items() if c > 1]
            f.write(f"**Duplicates**: {len(dups)}\n")
            if dups:
                f.write(f"- {', '.join(dups)}\n")
            f.write(f"\n**Missing Coordinates**: {len(missing_coords)}\n")
            if missing_coords:
                f.write(f"- {', '.join(missing_coords)}\n")
            
if __name__ == '__main__':
    asyncio.run(audit())
