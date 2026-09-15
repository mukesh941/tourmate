import asyncio
import random
from app.core.database import get_db
from app.models.place import TouristPlaceInDB, GeoJSONPoint, FeatureScores
from app.models.destination import DestinationInDB

indian_places_data = [
    {"name": "Taj Mahal", "state": "Uttar Pradesh", "city": "Agra", "lat": 27.1751, "lng": 78.0421},
    {"name": "Qutub Minar", "state": "Delhi", "city": "New Delhi", "lat": 28.5245, "lng": 77.1855},
    {"name": "Red Fort", "state": "Delhi", "city": "New Delhi", "lat": 28.6562, "lng": 77.2410},
    {"name": "India Gate", "state": "Delhi", "city": "New Delhi", "lat": 28.6129, "lng": 77.2295},
    {"name": "Lotus Temple", "state": "Delhi", "city": "New Delhi", "lat": 28.5535, "lng": 77.2588},
    {"name": "Gateway of India", "state": "Maharashtra", "city": "Mumbai", "lat": 18.9220, "lng": 72.8347},
    {"name": "Marine Drive", "state": "Maharashtra", "city": "Mumbai", "lat": 18.9440, "lng": 72.8227},
    {"name": "Elephanta Caves", "state": "Maharashtra", "city": "Mumbai", "lat": 18.9633, "lng": 72.9315},
    {"name": "Chhatrapati Shivaji Terminus", "state": "Maharashtra", "city": "Mumbai", "lat": 18.9398, "lng": 72.8354},
    {"name": "Hawa Mahal", "state": "Rajasthan", "city": "Jaipur", "lat": 26.9239, "lng": 75.8267},
    {"name": "Amer Fort", "state": "Rajasthan", "city": "Jaipur", "lat": 26.9855, "lng": 75.8513},
    {"name": "City Palace", "state": "Rajasthan", "city": "Udaipur", "lat": 24.5764, "lng": 73.6835},
    {"name": "Lake Palace", "state": "Rajasthan", "city": "Udaipur", "lat": 24.5753, "lng": 73.6800},
    {"name": "Mehrangarh Fort", "state": "Rajasthan", "city": "Jodhpur", "lat": 26.2978, "lng": 73.0186},
    {"name": "Jaisalmer Fort", "state": "Rajasthan", "city": "Jaisalmer", "lat": 26.9124, "lng": 70.9123},
    {"name": "Victoria Memorial", "state": "West Bengal", "city": "Kolkata", "lat": 22.5448, "lng": 88.3426},
    {"name": "Howrah Bridge", "state": "West Bengal", "city": "Kolkata", "lat": 22.5851, "lng": 88.3468},
    {"name": "Dakshineswar Kali Temple", "state": "West Bengal", "city": "Kolkata", "lat": 22.6534, "lng": 88.3577},
    {"name": "Charminar", "state": "Telangana", "city": "Hyderabad", "lat": 17.3616, "lng": 78.4747},
    {"name": "Golconda Fort", "state": "Telangana", "city": "Hyderabad", "lat": 17.3833, "lng": 78.4011},
    {"name": "Ramoji Film City", "state": "Telangana", "city": "Hyderabad", "lat": 17.2543, "lng": 78.6808},
    {"name": "Hussain Sagar Lake", "state": "Telangana", "city": "Hyderabad", "lat": 17.4239, "lng": 78.4738},
    {"name": "Mysore Palace", "state": "Karnataka", "city": "Mysuru", "lat": 12.3052, "lng": 76.6552},
    {"name": "Lalbagh Botanical Garden", "state": "Karnataka", "city": "Bengaluru", "lat": 12.9507, "lng": 77.5848},
    {"name": "Bangalore Palace", "state": "Karnataka", "city": "Bengaluru", "lat": 12.9988, "lng": 77.5921},
    {"name": "Cubbon Park", "state": "Karnataka", "city": "Bengaluru", "lat": 12.9763, "lng": 77.5929},
    {"name": "Hampi Ruins", "state": "Karnataka", "city": "Hampi", "lat": 15.3350, "lng": 76.4600},
    {"name": "Meenakshi Temple", "state": "Tamil Nadu", "city": "Madurai", "lat": 9.9195, "lng": 78.1193},
    {"name": "Marina Beach", "state": "Tamil Nadu", "city": "Chennai", "lat": 13.0500, "lng": 80.2824},
    {"name": "Brihadeeswarar Temple", "state": "Tamil Nadu", "city": "Thanjavur", "lat": 10.7828, "lng": 79.1318},
    {"name": "Vivekananda Rock Memorial", "state": "Tamil Nadu", "city": "Kanyakumari", "lat": 8.0780, "lng": 77.5553},
    {"name": "Munnar Tea Gardens", "state": "Kerala", "city": "Munnar", "lat": 10.0889, "lng": 77.0595},
    {"name": "Alleppey Backwaters", "state": "Kerala", "city": "Alappuzha", "lat": 9.4981, "lng": 76.3388},
    {"name": "Wayanad Wildlife Sanctuary", "state": "Kerala", "city": "Wayanad", "lat": 11.7371, "lng": 76.3312},
    {"name": "Kovalam Beach", "state": "Kerala", "city": "Thiruvananthapuram", "lat": 8.4004, "lng": 76.9787},
    {"name": "Golden Temple", "state": "Punjab", "city": "Amritsar", "lat": 31.6200, "lng": 74.8765},
    {"name": "Jallianwala Bagh", "state": "Punjab", "city": "Amritsar", "lat": 31.6206, "lng": 74.8801},
    {"name": "Wagah Border", "state": "Punjab", "city": "Amritsar", "lat": 31.6046, "lng": 74.5727},
    {"name": "Rock Garden", "state": "Chandigarh", "city": "Chandigarh", "lat": 30.7525, "lng": 76.8066},
    {"name": "Dal Lake", "state": "Jammu & Kashmir", "city": "Srinagar", "lat": 34.1136, "lng": 74.8741},
    {"name": "Gulmarg Gondola", "state": "Jammu & Kashmir", "city": "Gulmarg", "lat": 34.0484, "lng": 74.3805},
    {"name": "Pangong Tso", "state": "Ladakh", "city": "Leh", "lat": 33.7595, "lng": 78.6674},
    {"name": "Nubra Valley", "state": "Ladakh", "city": "Leh", "lat": 34.6863, "lng": 77.5673},
    {"name": "Magnetic Hill", "state": "Ladakh", "city": "Leh", "lat": 34.1722, "lng": 77.3486},
    {"name": "Khajuraho Temples", "state": "Madhya Pradesh", "city": "Khajuraho", "lat": 24.8318, "lng": 79.9197},
    {"name": "Sanchi Stupa", "state": "Madhya Pradesh", "city": "Sanchi", "lat": 23.4871, "lng": 77.7397},
    {"name": "Gwalior Fort", "state": "Madhya Pradesh", "city": "Gwalior", "lat": 26.2307, "lng": 78.1695},
    {"name": "Bhedaghat Marble Rocks", "state": "Madhya Pradesh", "city": "Jabalpur", "lat": 23.1309, "lng": 79.8023},
    {"name": "Statue of Unity", "state": "Gujarat", "city": "Kevadia", "lat": 21.8380, "lng": 73.7191},
    {"name": "Rann of Kutch", "state": "Gujarat", "city": "Kutch", "lat": 23.8322, "lng": 70.1601},
    {"name": "Somnath Temple", "state": "Gujarat", "city": "Somnath", "lat": 20.8880, "lng": 70.4010},
    {"name": "Gir National Park", "state": "Gujarat", "city": "Talala", "lat": 21.1329, "lng": 70.7963},
    {"name": "Sun Temple Konark", "state": "Odisha", "city": "Konark", "lat": 19.8876, "lng": 86.0945},
    {"name": "Jagannath Temple", "state": "Odisha", "city": "Puri", "lat": 19.8048, "lng": 85.8179},
    {"name": "Chilika Lake", "state": "Odisha", "city": "Puri", "lat": 19.7288, "lng": 85.3188},
    {"name": "Kaziranga National Park", "state": "Assam", "city": "Kaziranga", "lat": 26.5775, "lng": 93.1711},
    {"name": "Kamakhya Temple", "state": "Assam", "city": "Guwahati", "lat": 26.1669, "lng": 91.7056},
    {"name": "Tawang Monastery", "state": "Arunachal Pradesh", "city": "Tawang", "lat": 27.5866, "lng": 91.8590},
    {"name": "Nathu La Pass", "state": "Sikkim", "city": "Gangtok", "lat": 27.3866, "lng": 88.8277},
    {"name": "Tsomgo Lake", "state": "Sikkim", "city": "Gangtok", "lat": 27.3742, "lng": 88.7619},
    {"name": "Rohtang Pass", "state": "Himachal Pradesh", "city": "Manali", "lat": 32.3716, "lng": 77.2466},
    {"name": "Solang Valley", "state": "Himachal Pradesh", "city": "Manali", "lat": 32.3168, "lng": 77.1557},
    {"name": "Triund Hill", "state": "Himachal Pradesh", "city": "Dharamshala", "lat": 32.2612, "lng": 76.3263},
    {"name": "Jim Corbett National Park", "state": "Uttarakhand", "city": "Ramnagar", "lat": 29.5300, "lng": 78.7747},
    {"name": "Naini Lake", "state": "Uttarakhand", "city": "Nainital", "lat": 29.3919, "lng": 79.4542},
    {"name": "Valley of Flowers", "state": "Uttarakhand", "city": "Chamoli", "lat": 30.7280, "lng": 79.6053},
    {"name": "Baga Beach", "state": "Goa", "city": "Baga", "lat": 15.5553, "lng": 73.7517},
    {"name": "Dudhsagar Waterfalls", "state": "Goa", "city": "Sonaulim", "lat": 15.3144, "lng": 74.3143},
    {"name": "Aguada Fort", "state": "Goa", "city": "Candolim", "lat": 15.4988, "lng": 73.7656},
    {"name": "Ajanta Caves", "state": "Maharashtra", "city": "Aurangabad", "lat": 20.5519, "lng": 75.7033},
    {"name": "Ellora Caves", "state": "Maharashtra", "city": "Aurangabad", "lat": 20.0258, "lng": 75.1780},
    {"name": "Mahabaleshwar Viewpoint", "state": "Maharashtra", "city": "Mahabaleshwar", "lat": 17.9307, "lng": 73.6477},
    {"name": "Andaman Cellular Jail", "state": "Andaman & Nicobar", "city": "Port Blair", "lat": 11.6738, "lng": 92.7479},
    {"name": "Radhanagar Beach", "state": "Andaman & Nicobar", "city": "Havelock Island", "lat": 11.9839, "lng": 92.9505},
    {"name": "Bodh Gaya (Mahabodhi Temple)", "state": "Bihar", "city": "Gaya", "lat": 24.6959, "lng": 84.9914},
    {"name": "Nalanda University Ruins", "state": "Bihar", "city": "Nalanda", "lat": 25.1376, "lng": 85.4449},
    {"name": "Rishikesh Ram Jhula", "state": "Uttarakhand", "city": "Rishikesh", "lat": 30.1246, "lng": 78.3117},
    {"name": "Har Ki Pauri", "state": "Uttarakhand", "city": "Haridwar", "lat": 29.9566, "lng": 78.1700},
]

async def seed_more_india():
    db = get_db()
    
    # 1. Fetch a category to assign to places (e.g. Nature, History, or random)
    cats = await db.categories.find().to_list(100)
    cat_ids = [str(c["_id"]) for c in cats]
    if not cat_ids:
        print("No categories found. Run seed_db.py first.")
        return
        
    print(f"Adding {len(indian_places_data)} famous Indian locations to the database...")
    count = 0
    for place_data in indian_places_data:
        # Check if place already exists
        existing = await db.tourist_places.find_one({"name": place_data["name"]})
        if existing:
            continue
            
        # Get or Create Destination
        dest = await db.destinations.find_one({"name": place_data["city"]})
        if dest:
            dest_id = str(dest["_id"])
        else:
            new_dest = DestinationInDB(
                name=place_data["city"],
                state=place_data["state"],
                country="India",
                description=f"A beautiful city in {place_data['state']}.",
                cover_image="https://images.unsplash.com/photo-1524492412937-b28074a5d7da",
                popularity_score=random.uniform(6.0, 9.0),
                lat=place_data["lat"],
                lng=place_data["lng"]
            )
            res = await db.destinations.insert_one(new_dest.dict())
            dest_id = str(res.inserted_id)
            
        new_place = TouristPlaceInDB(
            destination_id=dest_id,
            name=place_data["name"],
            category_id=random.choice(cat_ids),
            description=f"One of the most famous and culturally rich landmarks in {place_data['city']}, {place_data['state']}. Highly recommended for all travelers.",
            location=GeoJSONPoint(coordinates=[place_data["lng"], place_data["lat"]]),
            images=["https://images.unsplash.com/photo-1514222134-b57cbb8ce073", "https://images.unsplash.com/photo-1506461883276-594a12b11cf3"],
            rating=random.uniform(4.5, 5.0),
            price_level=random.randint(1, 4),
            visit_duration_minutes=random.choice([60, 120, 180, 240]),
            feature_scores=FeatureScores(
                history=random.uniform(5.0, 10.0),
                nature=random.uniform(1.0, 10.0),
                culture=random.uniform(6.0, 10.0),
                adventure=random.uniform(1.0, 8.0),
                food=random.uniform(2.0, 7.0),
                shopping=random.uniform(2.0, 7.0),
                architecture=random.uniform(6.0, 10.0)
            )
        )
        await db.tourist_places.insert_one(new_place.dict())
        count += 1
        
    print(f"Successfully added {count} new locations across India!")

if __name__ == "__main__":
    asyncio.run(seed_more_india())
