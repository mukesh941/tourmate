import asyncio
from app.core.database import get_db
from app.models.category import CategoryInDB
from app.models.destination import DestinationInDB
from app.models.place import TouristPlaceInDB, GeoJSONPoint, FeatureScores

async def seed():
    db = get_db()
    
    # 1. Clear existing
    print("Clearing existing data...")
    await db.categories.delete_many({})
    await db.destinations.delete_many({})
    await db.tourist_places.delete_many({})
    
    # 2. Add Categories
    print("Adding Categories...")
    cats = [
        {"name": "History", "icon": "🏛️", "description": "Historical landmarks and museums."},
        {"name": "Nature", "icon": "🌳", "description": "Parks, mountains, and natural wonders."},
        {"name": "Culture", "icon": "🎭", "description": "Cultural experiences and art."},
        {"name": "Adventure", "icon": "🧗", "description": "Thrilling activities and sports."},
        {"name": "Food", "icon": "🍽️", "description": "Culinary delights and restaurants."},
        {"name": "Shopping", "icon": "🛍️", "description": "Markets and malls."},
        {"name": "Architecture", "icon": "🏙️", "description": "Modern and classical architecture."}
    ]
    
    cat_ids = {}
    for c in cats:
        res = await db.categories.insert_one(CategoryInDB(**c).dict())
        cat_ids[c["name"]] = str(res.inserted_id)

    # 3. Add Destinations
    print("Adding Destinations...")
    dests = [
        {"name": "Paris", "country": "France", "description": "The city of light.", "image_url": "https://images.unsplash.com/photo-1502602898657-3e91760cbb34", "lat": 48.8566, "lng": 2.3522},
        {"name": "New York", "country": "USA", "description": "The big apple.", "image_url": "https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9", "lat": 40.7128, "lng": -74.0060},
        {"name": "Tokyo", "country": "Japan", "description": "A bustling metropolis.", "image_url": "https://images.unsplash.com/photo-1536098561742-ca998e48cbcc", "lat": 35.6762, "lng": 139.6503},
        {"name": "New Delhi", "country": "India", "description": "The capital city of India.", "image_url": "https://images.unsplash.com/photo-1587474260584-136574528ed5", "lat": 28.6139, "lng": 77.2090},
        {"name": "Agra", "country": "India", "description": "Home to the iconic Taj Mahal.", "image_url": "https://images.unsplash.com/photo-1564507592333-c60657eea523", "lat": 27.1767, "lng": 78.0081},
        {"name": "Kathmandu", "country": "Nepal", "description": "The city of temples in the Himalayas.", "image_url": "https://images.unsplash.com/photo-1572099606223-6e29045d7de3", "lat": 27.7172, "lng": 85.3240},
        {"name": "London", "country": "UK", "description": "The historic capital of England.", "image_url": "https://images.unsplash.com/photo-1513635269975-59693e0cd8ce", "lat": 51.5074, "lng": -0.1278},
        {"name": "Rome", "country": "Italy", "description": "The Eternal City.", "image_url": "https://images.unsplash.com/photo-1552832230-c0197dd311b5", "lat": 41.9028, "lng": 12.4964},
        {"name": "Sydney", "country": "Australia", "description": "The Harbour City.", "image_url": "https://images.unsplash.com/photo-1506973035872-a4ec16b8e8d9", "lat": -33.8688, "lng": 151.2093},
        {"name": "Rio de Janeiro", "country": "Brazil", "description": "The Marvelous City.", "image_url": "https://images.unsplash.com/photo-1483729558449-99ef09a8c325", "lat": -22.9068, "lng": -43.1729},
        {"name": "Cairo", "country": "Egypt", "description": "The city of a thousand minarets.", "image_url": "https://images.unsplash.com/photo-1539650116574-8efeb43e2750", "lat": 30.0444, "lng": 31.2357},
    ]
    
    dest_ids = {}
    for d in dests:
        res = await db.destinations.insert_one(DestinationInDB(
            name=d["name"], country=d["country"], description=d["description"],
            location=GeoJSONPoint(coordinates=[d["lng"], d["lat"]]), images=[d["image_url"]]
        ).dict())
        dest_ids[d["name"]] = str(res.inserted_id)

    # 4. Add Places
    print("Adding Tourist Places...")
    places = [
        # Paris Places
        {
            "dest": "Paris", "cat": "Architecture", "name": "Eiffel Tower",
            "desc": "Iconic iron lattice tower on the Champ de Mars.",
            "hist": "Built for the 1889 World's Fair.", "cult": "Symbol of France globally.",
            "lat": 48.8584, "lng": 2.2945, "img": "https://images.unsplash.com/photo-1511739001486-6bfe10ce785f",
            "rating": 4.8, "price": 3, "dur": 120,
            "fs": {"history": 6.0, "nature": 1.0, "culture": 8.0, "adventure": 2.0, "food": 3.0, "shopping": 2.0, "architecture": 10.0}
        },
        {
            "dest": "Paris", "cat": "History", "name": "Louvre Museum",
            "desc": "World's largest art museum and a historic monument.",
            "hist": "Originally a fortress built in the late 12th to 13th century.", "cult": "Home to the Mona Lisa and Venus de Milo.",
            "lat": 48.8606, "lng": 2.3376, "img": "https://images.unsplash.com/photo-1499856871958-5b9627545d1a",
            "rating": 4.9, "price": 3, "dur": 240,
            "fs": {"history": 10.0, "nature": 0.0, "culture": 10.0, "adventure": 0.0, "food": 1.0, "shopping": 3.0, "architecture": 8.0}
        },
        # New York Places
        {
            "dest": "New York", "cat": "Nature", "name": "Central Park",
            "desc": "Urban park in Manhattan.",
            "hist": "Established in 1857.", "cult": "The most visited urban park in the United States.",
            "lat": 40.7812, "lng": -73.9665, "img": "https://images.unsplash.com/photo-1568283094548-26162d3a95ce",
            "rating": 4.7, "price": 1, "dur": 180,
            "fs": {"history": 4.0, "nature": 10.0, "culture": 5.0, "adventure": 3.0, "food": 2.0, "shopping": 0.0, "architecture": 2.0}
        },
        {
            "dest": "New York", "cat": "Culture", "name": "Broadway",
            "desc": "Theatrical performances presented in the 41 professional theatres.",
            "hist": "Developed rapidly in the late 19th century.", "cult": "Represents the highest level of commercial theatre in the English-speaking world.",
            "lat": 40.7590, "lng": -73.9845, "img": "https://images.unsplash.com/photo-1549429402-4fc99b70b466",
            "rating": 4.8, "price": 4, "dur": 180,
            "fs": {"history": 5.0, "nature": 0.0, "culture": 10.0, "adventure": 0.0, "food": 4.0, "shopping": 6.0, "architecture": 5.0}
        },
        # Tokyo Places
        {
            "dest": "Tokyo", "cat": "History", "name": "Senso-ji Temple",
            "desc": "Ancient Buddhist temple located in Asakusa.",
            "hist": "Founded in 628.", "cult": "Tokyo's oldest temple, and one of its most significant.",
            "lat": 35.7148, "lng": 139.7967, "img": "https://images.unsplash.com/photo-1536098561742-ca998e48cbcc",
            "rating": 4.7, "price": 1, "dur": 90,
            "fs": {"history": 10.0, "nature": 2.0, "culture": 10.0, "adventure": 0.0, "food": 5.0, "shopping": 7.0, "architecture": 8.0}
        },
        {
            "dest": "Tokyo", "cat": "Shopping", "name": "Akihabara",
            "desc": "Shopping hub famous for electronics and otaku culture.",
            "hist": "Evolved post-WWII as a black market.", "cult": "Center of Japanese otaku culture.",
            "lat": 35.6983, "lng": 139.7731, "img": "https://images.unsplash.com/photo-1542051812871-700940331006",
            "rating": 4.6, "price": 3, "dur": 240,
            "fs": {"history": 3.0, "nature": 0.0, "culture": 8.0, "adventure": 0.0, "food": 5.0, "shopping": 10.0, "architecture": 4.0}
        },
        # India Places
        {
            "dest": "Agra", "cat": "Architecture", "name": "Taj Mahal",
            "desc": "An ivory-white marble mausoleum on the right bank of the river Yamuna.",
            "hist": "Commissioned in 1631 by the Mughal emperor Shah Jahan.", "cult": "A universally admired masterpiece of the world's heritage.",
            "lat": 27.1751, "lng": 78.0421, "img": "https://images.unsplash.com/photo-1564507592333-c60657eea523",
            "rating": 4.9, "price": 2, "dur": 180,
            "fs": {"history": 9.0, "nature": 1.0, "culture": 10.0, "adventure": 0.0, "food": 2.0, "shopping": 3.0, "architecture": 10.0}
        },
        {
            "dest": "Agra", "cat": "History", "name": "Agra Fort",
            "desc": "Historical fort in the city of Agra.",
            "hist": "Main residence of the emperors of the Mughal Dynasty.", "cult": "A UNESCO World Heritage site.",
            "lat": 27.1795, "lng": 78.0211, "img": "https://images.unsplash.com/photo-1574182991051-789a69176313",
            "rating": 4.7, "price": 1, "dur": 120,
            "fs": {"history": 10.0, "nature": 2.0, "culture": 7.0, "adventure": 0.0, "food": 2.0, "shopping": 2.0, "architecture": 9.0}
        },
        {
            "dest": "New Delhi", "cat": "History", "name": "Red Fort",
            "desc": "Historic fort in the city of Delhi.",
            "hist": "Constructed in 1639 by the fifth Mughal Emperor Shah Jahan.", "cult": "Represents the zenith of Mughal creativity.",
            "lat": 28.6562, "lng": 77.2410, "img": "https://images.unsplash.com/photo-1587474260584-136574528ed5",
            "rating": 4.6, "price": 1, "dur": 120,
            "fs": {"history": 10.0, "nature": 2.0, "culture": 8.0, "adventure": 0.0, "food": 3.0, "shopping": 4.0, "architecture": 9.0}
        },
        {
            "dest": "New Delhi", "cat": "History", "name": "India Gate",
            "desc": "War memorial located astride the Rajpath.",
            "hist": "Dedicated to the troops of British India who died in wars.", "cult": "An important monument for the country.",
            "lat": 28.6129, "lng": 77.2295, "img": "https://images.unsplash.com/photo-1585135118556-9b0d62a694a9",
            "rating": 4.8, "price": 1, "dur": 60,
            "fs": {"history": 9.0, "nature": 3.0, "culture": 6.0, "adventure": 0.0, "food": 3.0, "shopping": 2.0, "architecture": 8.0}
        },
        {
            "dest": "New Delhi", "cat": "Architecture", "name": "Lotus Temple",
            "desc": "Bahá'í House of Worship notable for its flowerlike shape.",
            "hist": "Dedicated in December 1986.", "cult": "Open to all, regardless of religion or any other qualification.",
            "lat": 28.5535, "lng": 77.2588, "img": "https://images.unsplash.com/photo-1570125866173-19bd9422df5b",
            "rating": 4.7, "price": 1, "dur": 60,
            "fs": {"history": 3.0, "nature": 5.0, "culture": 7.0, "adventure": 0.0, "food": 1.0, "shopping": 1.0, "architecture": 10.0}
        },
        # Nepal Places
        {
            "dest": "Kathmandu", "cat": "Culture", "name": "Swayambhunath Stupa",
            "desc": "An ancient religious architecture atop a hill in the Kathmandu Valley.",
            "hist": "Founded by the great-grandfather of King Mānadeva.", "cult": "Also known as the Monkey Temple, highly revered by Buddhists.",
            "lat": 27.7149, "lng": 85.2899, "img": "https://images.unsplash.com/photo-1572099606223-6e29045d7de3",
            "rating": 4.7, "price": 1, "dur": 120,
            "fs": {"history": 9.0, "nature": 4.0, "culture": 10.0, "adventure": 1.0, "food": 2.0, "shopping": 2.0, "architecture": 8.0}
        },
        {
            "dest": "Kathmandu", "cat": "History", "name": "Pashupatinath Temple",
            "desc": "A famous and sacred Hindu temple complex.",
            "hist": "One of the oldest Hindu temples of Kathmandu.", "cult": "A major pilgrimage site for Hindus.",
            "lat": 27.7104, "lng": 85.3487, "img": "https://images.unsplash.com/photo-1544735716-392fe2489ffa",
            "rating": 4.8, "price": 1, "dur": 150,
            "fs": {"history": 10.0, "nature": 3.0, "culture": 10.0, "adventure": 0.0, "food": 1.0, "shopping": 2.0, "architecture": 9.0}
        },
        {
            "dest": "Kathmandu", "cat": "Culture", "name": "Boudhanath Stupa",
            "desc": "One of the largest spherical stupas in Nepal.",
            "hist": "Built around the 14th century.", "cult": "Center of Tibetan Buddhism in Nepal.",
            "lat": 27.7215, "lng": 85.3620, "img": "https://images.unsplash.com/photo-1578330776510-752495d033e0",
            "rating": 4.7, "price": 1, "dur": 90,
            "fs": {"history": 8.0, "nature": 2.0, "culture": 10.0, "adventure": 0.0, "food": 3.0, "shopping": 4.0, "architecture": 8.0}
        },
        {
            "dest": "Kathmandu", "cat": "History", "name": "Kathmandu Durbar Square",
            "desc": "One of three Durbar Squares in the Kathmandu Valley.",
            "hist": "Held the palaces of the Malla and Shah kings.", "cult": "Surrounded with spectacular architecture and showcases the skills of the Newar artists.",
            "lat": 27.7042, "lng": 85.3065, "img": "https://images.unsplash.com/photo-1582239611277-2ccba4f3d1b6",
            "rating": 4.6, "price": 1, "dur": 180,
            "fs": {"history": 10.0, "nature": 1.0, "culture": 9.0, "adventure": 0.0, "food": 4.0, "shopping": 6.0, "architecture": 10.0}
        },
        # London Places
        {
            "dest": "London", "cat": "Architecture", "name": "Big Ben",
            "desc": "The Great Bell of the striking clock at the north end of the Palace of Westminster.",
            "hist": "Completed in 1859.", "cult": "A British cultural icon.",
            "lat": 51.5007, "lng": -0.1246, "img": "https://images.unsplash.com/photo-1529655683823-dc58689736f4",
            "rating": 4.7, "price": 1, "dur": 60,
            "fs": {"history": 9.0, "nature": 1.0, "culture": 8.0, "adventure": 0.0, "food": 2.0, "shopping": 3.0, "architecture": 10.0}
        },
        {
            "dest": "London", "cat": "Culture", "name": "The British Museum",
            "desc": "A public institution dedicated to human history, art and culture.",
            "hist": "Established in 1753.", "cult": "Houses a permanent collection of some 8 million works.",
            "lat": 51.5194, "lng": -0.1269, "img": "https://images.unsplash.com/photo-1588615419957-c331168d1976",
            "rating": 4.8, "price": 1, "dur": 240,
            "fs": {"history": 10.0, "nature": 0.0, "culture": 10.0, "adventure": 0.0, "food": 2.0, "shopping": 4.0, "architecture": 8.0}
        },
        # Rome Places
        {
            "dest": "Rome", "cat": "History", "name": "Colosseum",
            "desc": "An oval amphitheatre in the centre of the city of Rome.",
            "hist": "Built in 70-80 AD.", "cult": "The largest ancient amphitheatre ever built.",
            "lat": 41.8902, "lng": 12.4922, "img": "https://images.unsplash.com/photo-1552832230-c0197dd311b5",
            "rating": 4.9, "price": 3, "dur": 180,
            "fs": {"history": 10.0, "nature": 1.0, "culture": 9.0, "adventure": 0.0, "food": 3.0, "shopping": 2.0, "architecture": 10.0}
        },
        {
            "dest": "Rome", "cat": "Culture", "name": "Vatican Museums",
            "desc": "The public museums of the Vatican City.",
            "hist": "Founded in the early 16th century.", "cult": "Contains masterpieces of painting, sculpture and other works of art.",
            "lat": 41.9065, "lng": 12.4536, "img": "https://images.unsplash.com/photo-1563219436-e82eb0b4b232",
            "rating": 4.8, "price": 4, "dur": 240,
            "fs": {"history": 9.0, "nature": 0.0, "culture": 10.0, "adventure": 0.0, "food": 1.0, "shopping": 3.0, "architecture": 9.0}
        },
        # Sydney Places
        {
            "dest": "Sydney", "cat": "Architecture", "name": "Sydney Opera House",
            "desc": "A multi-venue performing arts centre in Sydney.",
            "hist": "Opened in 1973.", "cult": "One of the 20th century's most famous and distinctive buildings.",
            "lat": -33.8568, "lng": 151.2153, "img": "https://images.unsplash.com/photo-1506973035872-a4ec16b8e8d9",
            "rating": 4.8, "price": 3, "dur": 120,
            "fs": {"history": 6.0, "nature": 5.0, "culture": 10.0, "adventure": 0.0, "food": 4.0, "shopping": 2.0, "architecture": 10.0}
        },
        {
            "dest": "Sydney", "cat": "Nature", "name": "Bondi Beach",
            "desc": "A popular beach and the name of the surrounding suburb in Sydney.",
            "hist": "Has a long history as a popular swimming spot.", "cult": "Iconic for Australian surf culture.",
            "lat": -33.8915, "lng": 151.2767, "img": "https://images.unsplash.com/photo-1522026116805-728876a3e146",
            "rating": 4.7, "price": 1, "dur": 240,
            "fs": {"history": 2.0, "nature": 10.0, "culture": 6.0, "adventure": 7.0, "food": 5.0, "shopping": 4.0, "architecture": 2.0}
        },
        # Rio Places
        {
            "dest": "Rio de Janeiro", "cat": "Architecture", "name": "Christ the Redeemer",
            "desc": "An Art Deco statue of Jesus Christ in Rio de Janeiro.",
            "hist": "Completed in 1931.", "cult": "A cultural icon of both Rio de Janeiro and Brazil.",
            "lat": -22.9519, "lng": -43.2105, "img": "https://images.unsplash.com/photo-1483729558449-99ef09a8c325",
            "rating": 4.8, "price": 2, "dur": 120,
            "fs": {"history": 7.0, "nature": 8.0, "culture": 10.0, "adventure": 4.0, "food": 1.0, "shopping": 1.0, "architecture": 9.0}
        },
        # Cairo Places
        {
            "dest": "Cairo", "cat": "History", "name": "Giza Necropolis",
            "desc": "Archaeological site on the Giza Plateau.",
            "hist": "Constructed during the Fourth Dynasty of the Old Kingdom.", "cult": "The oldest of the Seven Wonders of the Ancient World.",
            "lat": 29.9792, "lng": 31.1342, "img": "https://images.unsplash.com/photo-1539650116574-8efeb43e2750",
            "rating": 4.9, "price": 2, "dur": 240,
            "fs": {"history": 10.0, "nature": 4.0, "culture": 10.0, "adventure": 6.0, "food": 1.0, "shopping": 3.0, "architecture": 10.0}
        }
    ]

    for p in places:
        await db.tourist_places.insert_one(TouristPlaceInDB(
            destination_id=dest_ids[p["dest"]],
            name=p["name"],
            category_id=cat_ids[p["cat"]],
            description=p["desc"],
            history=p["hist"],
            cultural_significance=p["cult"],
            location=GeoJSONPoint(coordinates=[p["lng"], p["lat"]]),
            images=[p["img"]],
            rating=p["rating"],
            price_level=p["price"],
            visit_duration_minutes=p["dur"],
            feature_scores=FeatureScores(**p["fs"])
        ).dict())
        
    print("Done seeding!")

if __name__ == "__main__":
    asyncio.run(seed())
