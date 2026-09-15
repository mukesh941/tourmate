import asyncio
import random
from app.core.database import get_db
from app.models.category import CategoryInDB
from app.models.destination import DestinationInDB
from app.models.place import TouristPlaceInDB, GeoJSONPoint, FeatureScores
from app.schemas.hotel import HotelCreate, RoomType, GeoJSONPointSchema as HotelGeoJSON
from app.schemas.restaurant import RestaurantCreate, GeoJSONPointSchema as RestGeoJSON
from app.schemas.activity import ActivityCreate, GeoJSONPointSchema as ActGeoJSON

cities = [
    {"name": "New Delhi", "lat": 28.6139, "lng": 77.2090, "state": "Delhi", "desc": "The capital city of India, known for its rich history and vibrant culture.", "img": "https://images.unsplash.com/photo-1587474260584-136574528ed5"},
    {"name": "Mumbai", "lat": 19.0760, "lng": 72.8777, "state": "Maharashtra", "desc": "The City of Dreams, financial capital and home of Bollywood.", "img": "https://images.unsplash.com/photo-1570168007204-dfb528c6958f"},
    {"name": "Bangalore", "lat": 12.9716, "lng": 77.5946, "state": "Karnataka", "desc": "The Silicon Valley of India with a beautiful climate and parks.", "img": "https://images.unsplash.com/photo-1593693397690-362bc17887e1"},
    {"name": "Chennai", "lat": 13.0827, "lng": 80.2707, "state": "Tamil Nadu", "desc": "Gateway to South India, famous for its temples and Marina beach.", "img": "https://images.unsplash.com/photo-1582510003544-4d00b7f74220"},
    {"name": "Kolkata", "lat": 22.5726, "lng": 88.3639, "state": "West Bengal", "desc": "The City of Joy, known for its colonial architecture and culture.", "img": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64"},
    {"name": "Hyderabad", "lat": 17.3850, "lng": 78.4867, "state": "Telangana", "desc": "City of Pearls, famous for Charminar and Biryani.", "img": "https://images.unsplash.com/photo-1562679299-6c5d8b8b0e76"},
    {"name": "Pune", "lat": 18.5204, "lng": 73.8567, "state": "Maharashtra", "desc": "Oxford of the East, a vibrant city with a rich Maratha history.", "img": "https://images.unsplash.com/photo-1565345759164-94e803c72b22"},
    {"name": "Ahmedabad", "lat": 23.0225, "lng": 72.5714, "state": "Gujarat", "desc": "India's first UNESCO World Heritage City.", "img": "https://images.unsplash.com/photo-1605404179313-88f6f0c43118"},
    {"name": "Jaipur", "lat": 26.9124, "lng": 75.7873, "state": "Rajasthan", "desc": "The Pink City, rich in history, forts, and palaces.", "img": "https://images.unsplash.com/photo-1477587458883-47145ed94245"},
    {"name": "Goa", "lat": 15.2993, "lng": 74.1240, "state": "Goa", "desc": "Famous for its stunning beaches and nightlife.", "img": "https://images.unsplash.com/photo-1512343879784-a960bf40e7f2"},
    {"name": "Agra", "lat": 27.1767, "lng": 78.0081, "state": "Uttar Pradesh", "desc": "Home to the iconic Taj Mahal.", "img": "https://images.unsplash.com/photo-1564507592333-c60657eea523"},
    {"name": "Varanasi", "lat": 25.3176, "lng": 82.9739, "state": "Uttar Pradesh", "desc": "The spiritual heart of India on the banks of the Ganges.", "img": "https://images.unsplash.com/photo-1561361513-2d000a50f0dc"}
]

def get_offset():
    return random.uniform(-0.05, 0.05)

async def seed_india():
    db = get_db()
    
    print("Clearing collections...")
    await db.destinations.delete_many({})
    await db.tourist_places.delete_many({})
    await db.hotels.delete_many({})
    await db.restaurants.delete_many({})
    await db.activities.delete_many({})
    
    # 1. Fetch categories
    cats = await db.categories.find().to_list(100)
    cat_map = {c["name"]: str(c["_id"]) for c in cats}
    if not cat_map:
        print("Run seed_db.py first to create categories!")
        return
        
    for city in cities:
        # Create Destination
        dest = DestinationInDB(
            name=city["name"],
            state=city["state"],
            country="India",
            description=city["desc"],
            cover_image=city["img"],
            popularity_score=random.uniform(7.0, 10.0),
            lat=city["lat"],
            lng=city["lng"]
        )
        res = await db.destinations.insert_one(dest.dict())
        dest_id = str(res.inserted_id)
        
        print(f"Seeding data for {city['name']}...")
        
        # Create 3 Places
        for i in range(3):
            lat = city["lat"] + get_offset()
            lng = city["lng"] + get_offset()
            place = TouristPlaceInDB(
                destination_id=dest_id,
                name=f"{city['name']} Landmark {i+1}",
                category_id=list(cat_map.values())[random.randint(0, len(cat_map)-1)],
                description=f"A famous landmark in {city['name']}.",
                location=GeoJSONPoint(coordinates=[lng, lat]),
                images=[city["img"]],
                rating=random.uniform(4.0, 5.0),
                price_level=random.randint(1, 4),
                visit_duration_minutes=random.choice([60, 120, 180])
            )
            await db.tourist_places.insert_one(place.dict())
            
        # Create 3 Hotels
        real_hotels = {
            "New Delhi": ["The Taj Mahal Hotel", "The Leela Palace", "ITC Maurya"],
            "Mumbai": ["The Taj Mahal Palace", "The Oberoi", "Trident Nariman Point"],
            "Bangalore": ["The Leela Palace", "Taj West End", "ITC Gardenia"],
            "Chennai": ["ITC Grand Chola", "The Leela Palace", "Taj Coromandel"],
            "Kolkata": ["ITC Royal Bengal", "The Oberoi Grand", "Taj Bengal"],
            "Hyderabad": ["Taj Falaknuma Palace", "ITC Kakatiya", "The Park"],
            "Pune": ["JW Marriott Hotel", "The Ritz-Carlton", "Conrad Pune"],
            "Ahmedabad": ["ITC Narmada", "Taj Skyline", "Courtyard by Marriott"],
            "Jaipur": ["Rambagh Palace", "The Oberoi Rajvilas", "Fairmont Jaipur"],
            "Goa": ["Taj Exotica", "The Leela Goa", "W Goa"],
            "Agra": ["The Oberoi Amarvilas", "ITC Mughal", "Taj Hotel & Convention Centre"],
            "Varanasi": ["Taj Ganges", "BrijRama Palace", "Radisson Hotel"]
        }
        
        real_hotel_images = {
            "The Taj Mahal Palace": "https://upload.wikimedia.org/wikipedia/commons/2/2b/The_Taj_Mahal_Palace_Hotel.jpg",
            "The Taj Mahal Hotel": "https://upload.wikimedia.org/wikipedia/commons/2/2b/The_Taj_Mahal_Palace_Hotel.jpg",
            "Rambagh Palace": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d4/Rambagh_Palace_Jaipur.jpg/1280px-Rambagh_Palace_Jaipur.jpg",
            "Taj Falaknuma Palace": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Falaknuma_Palace_1.jpg/1280px-Falaknuma_Palace_1.jpg",
            "The Oberoi Amarvilas": "https://images.unsplash.com/photo-1542314831-c6a4d14ce8a1",
            "ITC Grand Chola": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/36/ITC_Grand_Chola_Chennai_Exterior.jpg/1280px-ITC_Grand_Chola_Chennai_Exterior.jpg",
            "Taj West End": "https://images.unsplash.com/photo-1566073771259-6a8506099945",
            "The Leela Palace": "https://upload.wikimedia.org/wikipedia/commons/4/4f/The_Leela_Palace_Chennai.jpg?utm_source=en.wikipedia.org&utm_campaign=api&utm_content=original",
            "ITC Royal Bengal": "https://upload.wikimedia.org/wikipedia/commons/5/5d/ITC_Royal_Bengal_in_April_2026.webp?utm_source=en.wikipedia.org&utm_campaign=api&utm_content=original",
            "Taj Bengal": "https://upload.wikimedia.org/wikipedia/commons/b/b3/Belvadere_Road_%27Taj_Bengal%27_%281%29.jpg?utm_source=en.wikipedia.org&utm_campaign=api&utm_content=original"
        }
        
        for j in range(3):
            lat = city["lat"] + get_offset()
            lng = city["lng"] + get_offset()
            hotel_names_for_city = real_hotels.get(city["name"], [f"{city['name']} Grand {i}" for i in range(1,4)])
            hotel_name = hotel_names_for_city[j]
            
            # Use specific image if available, else fallback to a nice generic luxury hotel
            hotel_img = real_hotel_images.get(hotel_name, random.choice([
                "https://images.unsplash.com/photo-1566073771259-6a8506099945",
                "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b",
                "https://images.unsplash.com/photo-1542314831-c6a4d14ce8a1",
                "https://images.unsplash.com/photo-1551882547-ff40c0d129fa",
                "https://images.unsplash.com/photo-1520250497591-112f2f40a3f4"
            ]))
            
            hotel = HotelCreate(
                name=hotel_name,
                description=f"Luxury stay in the heart of {city['name']}.",
                city=city["name"],
                address=f"Central Avenue, {city['name']}",
                destination_id=dest_id,
                location=HotelGeoJSON(coordinates=[lng, lat]),
                rating=random.uniform(4.0, 5.0),
                price_per_night_start=random.randint(5000, 30000),
                cover_image=hotel_img,
                hotel_type=random.choice(["Luxury", "Boutique", "Budget"]),
                rooms=[
                    RoomType(
                        id=f"room_{j}",
                        name="Deluxe Room",
                        price_per_night=8500.0,
                        capacity=2
                    ),
                    RoomType(
                        id=f"room_suite_{j}",
                        name="Executive Suite",
                        price_per_night=15000.0,
                        capacity=4
                    )
                ]
            )
            await db.hotels.insert_one(hotel.dict())
            
        # Create 3 Restaurants
        for i in range(3):
            lat = city["lat"] + get_offset()
            lng = city["lng"] + get_offset()
            restaurant = RestaurantCreate(
                name=f"{city['name']} Spice Kitchen {i+1}",
                description=f"Authentic local cuisine in {city['name']}.",
                cuisine_type=[random.choice(["Indian", "Continental", "Chinese", "Street Food"])],
                city=city["name"],
                address=f"Food Street, {city['name']}",
                destination_id=dest_id,
                location=RestGeoJSON(coordinates=[lng, lat]),
                rating=random.uniform(4.0, 5.0),
                price_level=random.randint(1, 4),
                cover_image="https://images.unsplash.com/photo-1555396273-367ea4eb4db5"
            )
            await db.restaurants.insert_one(restaurant.dict())
            
        # Create 3 Activities
        for i in range(3):
            lat = city["lat"] + get_offset()
            lng = city["lng"] + get_offset()
            activity = ActivityCreate(
                name=f"{city['name']} City Tour {i+1}",
                description=f"Explore the best parts of {city['name']}.",
                activity_type=random.choice(["Sightseeing", "Adventure", "Culture Walk", "Food Tour"]),
                city=city["name"],
                address=f"Tour Hub, {city['name']}",
                destination_id=dest_id,
                location=ActGeoJSON(coordinates=[lng, lat]),
                rating=random.uniform(4.0, 5.0),
                price=random.uniform(10, 100),
                cover_image="https://images.unsplash.com/photo-1531722569936-825d4ebd4500"
            )
            await db.activities.insert_one(activity.dict())
            
    print("Seed complete for all India locations!")

if __name__ == "__main__":
    asyncio.run(seed_india())
