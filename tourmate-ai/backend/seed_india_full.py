import asyncio
import logging
import uuid
from sqlalchemy import select
from app.core.db import AsyncSessionLocal
from app.models.sql.location import Location

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Complete List of 28 States and 8 Union Territories with their capitals/major cities
INDIA_STATES_UTS = {
    # States
    "Andhra Pradesh": ["Visakhapatnam", "Amaravati", "Vijayawada"],
    "Arunachal Pradesh": ["Tawang", "Itanagar"],
    "Assam": ["Guwahati", "Dispur", "Kaziranga"],
    "Bihar": ["Patna", "Bodh Gaya"],
    "Chhattisgarh": ["Raipur", "Bhilai"],
    "Goa": ["Panaji", "Vasco da Gama", "Margao", "Goa"],
    "Gujarat": ["Ahmedabad", "Surat", "Vadodara", "Gandhinagar"],
    "Haryana": ["Gurugram", "Chandigarh", "Faridabad"],
    "Himachal Pradesh": ["Shimla", "Manali", "Dharamshala", "Dalhousie"],
    "Jharkhand": ["Ranchi", "Jamshedpur"],
    "Karnataka": ["Bengaluru", "Mysuru", "Mangaluru", "Hampi", "Gokarna", "Coorg"],
    "Kerala": ["Thiruvananthapuram", "Kochi", "Kozhikode", "Munnar", "Alleppey", "Varkala"],
    "Madhya Pradesh": ["Bhopal", "Indore", "Gwalior", "Ujjain"],
    "Maharashtra": ["Mumbai", "Pune", "Nagpur", "Nashik", "Aurangabad"],
    "Manipur": ["Imphal"],
    "Meghalaya": ["Shillong", "Cherrapunji"],
    "Mizoram": ["Aizawl"],
    "Nagaland": ["Kohima", "Dimapur"],
    "Odisha": ["Bhubaneswar", "Puri", "Cuttack"],
    "Punjab": ["Amritsar", "Ludhiana", "Jalandhar", "Chandigarh"],
    "Rajasthan": ["Jaipur", "Udaipur", "Jodhpur", "Jaisalmer", "Pushkar"],
    "Sikkim": ["Gangtok", "Pelling"],
    "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai", "Ooty", "Kodaikanal"],
    "Telangana": ["Hyderabad", "Warangal"],
    "Tripura": ["Agartala"],
    "Uttar Pradesh": ["Lucknow", "Kanpur", "Varanasi", "Agra", "Prayagraj", "Rishikesh"], 
    "Uttarakhand": ["Dehradun", "Rishikesh", "Haridwar", "Nainital", "Mussoorie", "Auli"],
    "West Bengal": ["Kolkata", "Darjeeling", "Siliguri"],
    
    # Union Territories
    "Andaman and Nicobar Islands": ["Port Blair", "Havelock"],
    "Chandigarh": ["Chandigarh"],
    "Dadra and Nagar Haveli and Daman and Diu": ["Daman", "Diu", "Silvassa"],
    "Delhi": ["New Delhi", "Delhi"],
    "Jammu and Kashmir": ["Srinagar", "Jammu", "Gulmarg", "Pahalgam"],
    "Ladakh": ["Leh", "Kargil", "Zanskar"],
    "Lakshadweep": ["Kavaratti", "Agatti"],
    "Puducherry": ["Puducherry", "Auroville"]
}

# Extensive Alias map (Alias -> Canonical Name)
ALIASES = {
    "dehli": "Delhi",
    "new delhi": "Delhi",
    "banglore": "Bengaluru",
    "bangalore": "Bengaluru",
    "bombay": "Mumbai",
    "calcutta": "Kolkata",
    "madras": "Chennai",
    "poona": "Pune",
    "mysore": "Mysuru",
    "pondicherry": "Puducherry",
    "gurgaon": "Gurugram",
    "cochin": "Kochi",
    "trivandrum": "Thiruvananthapuram",
    "benaras": "Varanasi",
    "banaras": "Varanasi",
    "kashi": "Varanasi",
    "baroda": "Vadodara",
    "mangalore": "Mangaluru",
    "panjim": "Panaji"
}

# For simple geocoding approximations if we don't call an external API
APPROX_GEO = {
    "Delhi": (28.6139, 77.2090),
    "Mumbai": (19.0760, 72.8777),
    "Bengaluru": (12.9716, 77.5946),
    "Chennai": (13.0827, 80.2707),
    "Kolkata": (22.5726, 88.3639),
    "Hyderabad": (17.3850, 78.4867),
    "Pune": (18.5204, 73.8567),
    "Ahmedabad": (23.0225, 72.5714),
    "Jaipur": (26.9124, 75.7873),
    "Kochi": (9.9312, 76.2673),
    "Chandigarh": (30.7333, 76.7794),
    "Lucknow": (26.8467, 80.9462),
    "Bhopal": (23.2599, 77.4126),
    "Patna": (25.5941, 85.1376),
    "Bhubaneswar": (20.2961, 85.8245),
    "Guwahati": (26.1445, 91.7362),
    "Srinagar": (34.0837, 74.7973),
    "Mysuru": (12.2958, 76.6394),
    "Thiruvananthapuram": (8.5241, 76.9366),
    "Varanasi": (25.3176, 82.9739),
    "Vadodara": (22.3072, 73.1812),
    "Mangaluru": (12.9141, 74.8560),
    "Panaji": (15.4909, 73.8278),
    "Goa": (15.2993, 74.1240),
    "Rishikesh": (30.0869, 78.2676),
    "Manali": (32.2396, 77.1887),
    "Ooty": (11.4102, 76.6950),
    "Udaipur": (24.5854, 73.7125),
    "Amritsar": (31.6340, 74.8723),
    "Darjeeling": (27.0410, 88.2663),
    "Agra": (27.1767, 78.0081),
    "Andaman and Nicobar Islands": (11.7401, 92.6586),
    "Ladakh": (34.1526, 77.5771),
}


async def seed_india_full():
    async with AsyncSessionLocal() as session:
        inserted = 0
        skipped = 0
        
        # 1. Seed Main Locations (States and their Cities)
        for state_or_ut, cities in INDIA_STATES_UTS.items():
            for city in cities:
                # Check if it exists
                stmt = select(Location).where(Location.name == city)
                existing = (await session.execute(stmt)).scalars().first()
                if existing:
                    skipped += 1
                    continue
                
                lat, lng = APPROX_GEO.get(city, (20.0, 77.0))
                
                loc = Location(
                    id=uuid.uuid4(),
                    name=city,
                    canonical_name=city,
                    state=state_or_ut,
                    union_territory="" if state_or_ut in INDIA_STATES_UTS and state_or_ut not in ["Delhi", "Chandigarh", "Ladakh", "Puducherry", "Lakshadweep", "Andaman and Nicobar Islands", "Dadra and Nagar Haveli and Daman and Diu", "Jammu and Kashmir"] else state_or_ut,
                    district=city,
                    country="India",
                    city=city,
                    latitude=lat,
                    longitude=lng,
                    category="City",
                    subcategories=["Tourism", "Major City"],
                    description=f"Major destination in {state_or_ut}, India",
                    best_time_to_visit="October to March",
                    image="",
                    is_active=True
                )
                session.add(loc)
                inserted += 1

        # 2. Seed Aliases
        for alias, canonical in ALIASES.items():
            stmt = select(Location).where(Location.name == alias)
            existing = (await session.execute(stmt)).scalars().first()
            if existing:
                skipped += 1
                continue
            
            lat, lng = APPROX_GEO.get(canonical, (20.0, 77.0))
            
            # Find the canonical state
            canonical_state = ""
            for state, cities in INDIA_STATES_UTS.items():
                if canonical in cities:
                    canonical_state = state
                    break
                    
            loc = Location(
                id=uuid.uuid4(),
                name=alias,
                canonical_name=canonical,
                state=canonical_state,
                union_territory="",
                district=canonical,
                country="India",
                city=canonical,
                latitude=lat,
                longitude=lng,
                category="Alias",
                subcategories=["Alias"],
                description=f"Alias for {canonical}",
                best_time_to_visit="",
                image="",
                is_active=True
            )
            session.add(loc)
            inserted += 1

        await session.commit()
        logger.info(f"Seed complete: {inserted} inserted, {skipped} skipped/duplicates prevented.")

if __name__ == "__main__":
    asyncio.run(seed_india_full())
