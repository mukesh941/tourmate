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
        {"name": "Mumbai", "country": "India", "description": "The City of Dreams.", "image_url": "https://images.unsplash.com/photo-1570168007204-dfb528c6958f", "lat": 19.0760, "lng": 72.8777},
        {"name": "Jaipur", "country": "India", "description": "The Pink City, rich in history.", "image_url": "https://images.unsplash.com/photo-1477587458883-47145ed94245", "lat": 26.9124, "lng": 75.7873},
        {"name": "Goa", "country": "India", "description": "Famous for its stunning beaches and nightlife.", "image_url": "https://images.unsplash.com/photo-1512343879784-a960bf40e7f2", "lat": 15.2993, "lng": 74.1240},
        {"name": "Kerala", "country": "India", "description": "God's Own Country, known for backwaters.", "image_url": "https://images.unsplash.com/photo-1602216056096-3b40cc0c9944", "lat": 10.8505, "lng": 76.2711},
        {"name": "Varanasi", "country": "India", "description": "The spiritual heart of India on the banks of the Ganges.", "image_url": "https://images.unsplash.com/photo-1561361513-2d000a50f0dc", "lat": 25.3176, "lng": 82.9739},
        {"name": "Rishikesh", "country": "India", "description": "The Yoga Capital of the World and adventure sports hub.", "image_url": "https://images.unsplash.com/photo-1609766857541-4c27a8f6f3a5", "lat": 30.0869, "lng": 78.2676},
        {"name": "Manali", "country": "India", "description": "Snow-capped peaks and thrilling Himalayan adventures.", "image_url": "https://images.unsplash.com/photo-1626016555577-74b24a14b50d", "lat": 32.2396, "lng": 77.1887},
        {"name": "Amritsar", "country": "India", "description": "City of the Golden Temple and legendary Punjabi cuisine.", "image_url": "https://images.unsplash.com/photo-1588083949404-c4f1ed1323b3", "lat": 31.6340, "lng": 74.8723},
        {"name": "Kolkata", "country": "India", "description": "The cultural capital of India, famous for its street food.", "image_url": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64", "lat": 22.5726, "lng": 88.3639},
        {"name": "Hyderabad", "country": "India", "description": "Home of the world-famous Hyderabadi Biryani.", "image_url": "https://images.unsplash.com/photo-1562679299-6c5d8b8b0e76", "lat": 17.3850, "lng": 78.4867},
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
        },
        # Mumbai Places
        {
            "dest": "Mumbai", "cat": "Architecture", "name": "Gateway of India",
            "desc": "An arch-monument built in the early 20th century.",
            "hist": "Erected to commemorate the landing in India of King George V.", "cult": "Mumbai's most famous monument.",
            "lat": 18.9220, "lng": 72.8347, "img": "https://images.unsplash.com/photo-1570168007204-dfb528c6958f",
            "rating": 4.6, "price": 1, "dur": 60,
            "fs": {"history": 9.0, "nature": 2.0, "culture": 8.0, "adventure": 0.0, "food": 4.0, "shopping": 3.0, "architecture": 9.0}
        },
        {
            "dest": "Mumbai", "cat": "Nature", "name": "Marine Drive",
            "desc": "A 3.6-kilometre-long Promenade along the Netaji Subhash Chandra Bose Road.",
            "hist": "Constructed by late philanthropist Bhagojisheth Keer & Pallonji Mistry.", "cult": "Known as the Queen's Necklace.",
            "lat": 18.9440, "lng": 72.8228, "img": "https://images.unsplash.com/photo-1566552881560-0be862a7c445",
            "rating": 4.8, "price": 1, "dur": 120,
            "fs": {"history": 4.0, "nature": 8.0, "culture": 7.0, "adventure": 0.0, "food": 6.0, "shopping": 3.0, "architecture": 6.0}
        },
        # Jaipur Places
        {
            "dest": "Jaipur", "cat": "Architecture", "name": "Hawa Mahal",
            "desc": "A palace built from red and pink sandstone.",
            "hist": "Built in 1799 by Maharaja Sawai Pratap Singh.", "cult": "An iconic symbol of Rajput architecture.",
            "lat": 26.9239, "lng": 75.8267, "img": "https://images.unsplash.com/photo-1477587458883-47145ed94245",
            "rating": 4.7, "price": 2, "dur": 90,
            "fs": {"history": 9.0, "nature": 1.0, "culture": 9.0, "adventure": 0.0, "food": 3.0, "shopping": 6.0, "architecture": 10.0}
        },
        {
            "dest": "Jaipur", "cat": "History", "name": "Amer Fort",
            "desc": "A fort located in Amer, Rajasthan.",
            "hist": "Built by Raja Man Singh I.", "cult": "Known for its artistic style elements.",
            "lat": 26.9855, "lng": 75.8513, "img": "https://images.unsplash.com/photo-1599661046289-e31897846e41",
            "rating": 4.8, "price": 2, "dur": 180,
            "fs": {"history": 10.0, "nature": 4.0, "culture": 9.0, "adventure": 3.0, "food": 2.0, "shopping": 4.0, "architecture": 9.0}
        },
        # Goa Places
        {
            "dest": "Goa", "cat": "Nature", "name": "Baga Beach",
            "desc": "A popular beach and tourist destination in North Goa.",
            "hist": "Became popular in the 1960s.", "cult": "Famous for its vibrant nightlife and water sports.",
            "lat": 15.5553, "lng": 73.7517, "img": "https://images.unsplash.com/photo-1512343879784-a960bf40e7f2",
            "rating": 4.5, "price": 2, "dur": 240,
            "fs": {"history": 2.0, "nature": 9.0, "culture": 6.0, "adventure": 8.0, "food": 8.0, "shopping": 6.0, "architecture": 2.0}
        },
        {
            "dest": "Goa", "cat": "Nature", "name": "Dudhsagar Waterfalls",
            "desc": "A four-tiered waterfall located on the Mandovi River.",
            "hist": "Legend involves a princess and milk, giving it the name 'Sea of Milk'.", "cult": "One of India's tallest waterfalls.",
            "lat": 15.3144, "lng": 74.3143, "img": "https://images.unsplash.com/photo-1605649487212-47bdab064df7",
            "rating": 4.7, "price": 2, "dur": 180,
            "fs": {"history": 1.0, "nature": 10.0, "culture": 3.0, "adventure": 7.0, "food": 1.0, "shopping": 1.0, "architecture": 1.0}
        },
        # Kerala Places
        {
            "dest": "Kerala", "cat": "Nature", "name": "Munnar Tea Gardens",
            "desc": "Extensive rolling hills covered with tea plantations.",
            "hist": "Developed by Scottish planters in the late 19th century.", "cult": "The heart of Kerala's tea production.",
            "lat": 10.0889, "lng": 77.0595, "img": "https://images.unsplash.com/photo-1602216056096-3b40cc0c9944",
            "rating": 4.9, "price": 1, "dur": 180,
            "fs": {"history": 4.0, "nature": 10.0, "culture": 5.0, "adventure": 4.0, "food": 2.0, "shopping": 3.0, "architecture": 2.0}
        },
        {
            "dest": "Kerala", "cat": "Nature", "name": "Alleppey Backwaters",
            "desc": "A network of interconnected canals, rivers, lakes, and inlets.",
            "hist": "Historically used for transportation and agriculture.", "cult": "Famous for houseboat cruises.",
            "lat": 9.4981, "lng": 76.3388, "img": "https://images.unsplash.com/photo-1593693397690-362bc17887e1",
            "rating": 4.8, "price": 4, "dur": 300,
            "fs": {"history": 3.0, "nature": 10.0, "culture": 7.0, "adventure": 2.0, "food": 5.0, "shopping": 2.0, "architecture": 3.0}
        },
        # Varanasi Places
        {
            "dest": "Varanasi", "cat": "Culture", "name": "Kashi Vishwanath Temple",
            "desc": "One of the most famous Hindu temples dedicated to Lord Shiva.",
            "hist": "Destroyed and rebuilt a number of times in its history.", "cult": "Stands on the western bank of the holy river Ganga.",
            "lat": 25.3109, "lng": 83.0107, "img": "https://images.unsplash.com/photo-1571536802807-30451e3955d8",
            "rating": 4.9, "price": 1, "dur": 120,
            "fs": {"history": 9.0, "nature": 1.0, "culture": 10.0, "adventure": 0.0, "food": 3.0, "shopping": 2.0, "architecture": 8.0}
        },
        {
            "dest": "Varanasi", "cat": "Culture", "name": "Dashashwamedh Ghat",
            "desc": "The main ghat in Varanasi on the Ganga River.",
            "hist": "Created by Lord Brahma to welcome Lord Shiva.", "cult": "Famous for the spectacular Ganga Aarti performed daily.",
            "lat": 25.3068, "lng": 83.0106, "img": "https://images.unsplash.com/photo-1561361513-2d000a50f0dc",
            "rating": 4.8, "price": 1, "dur": 180,
            "fs": {"history": 8.0, "nature": 4.0, "culture": 10.0, "adventure": 1.0, "food": 4.0, "shopping": 3.0, "architecture": 6.0}
        },
        # Rishikesh Adventure Places
        {
            "dest": "Rishikesh", "cat": "Adventure", "name": "White Water Rafting on Ganga",
            "desc": "Experience thrilling white-water rafting on the mighty Ganges river through spectacular gorges.",
            "hist": "Rishikesh became a premier rafting destination in the 1980s.", "cult": "One of India's most iconic adventure experiences.",
            "lat": 30.1022, "lng": 78.3091, "img": "https://images.unsplash.com/photo-1531722569936-825d4ebd4500",
            "rating": 4.9, "price": 3, "dur": 240,
            "fs": {"history": 2.0, "nature": 9.0, "culture": 3.0, "adventure": 10.0, "food": 3.0, "shopping": 1.0, "architecture": 1.0}
        },
        {
            "dest": "Rishikesh", "cat": "Adventure", "name": "Laxman Jhula Bungee Jump",
            "desc": "India's highest bungee jumping platform at 83 metres overlooking the jungle and the Ganges.",
            "hist": "Opened in 2010, making it a landmark for adrenaline seekers.", "cult": "The most popular bungee site in India.",
            "lat": 30.1293, "lng": 78.3282, "img": "https://images.unsplash.com/photo-1533692328991-08159ff19fca",
            "rating": 4.8, "price": 3, "dur": 120,
            "fs": {"history": 1.0, "nature": 7.0, "culture": 2.0, "adventure": 10.0, "food": 1.0, "shopping": 1.0, "architecture": 2.0}
        },
        {
            "dest": "Rishikesh", "cat": "Adventure", "name": "Neelkanth Mahadev Trek",
            "desc": "A challenging 13 km trek through dense forests leading to the Neelkanth Mahadev temple at 1675m.",
            "hist": "Ancient pilgrimage route in the Himalayan foothills.", "cult": "Combines spiritual significance with adventure.",
            "lat": 30.1768, "lng": 78.3879, "img": "https://images.unsplash.com/photo-1605649487212-47bdab064df7",
            "rating": 4.7, "price": 1, "dur": 360,
            "fs": {"history": 6.0, "nature": 10.0, "culture": 7.0, "adventure": 9.0, "food": 1.0, "shopping": 1.0, "architecture": 4.0}
        },
        # Manali Adventure Places
        {
            "dest": "Manali", "cat": "Adventure", "name": "Rohtang Pass",
            "desc": "A high mountain pass in the Himalayas at 3978 m, offering skiing and snowboarding in winter.",
            "hist": "Historically an important trading route.", "cult": "Gateway to Lahaul and Spiti valleys.",
            "lat": 32.3714, "lng": 77.2408, "img": "https://images.unsplash.com/photo-1626016555577-74b24a14b50d",
            "rating": 4.8, "price": 2, "dur": 300,
            "fs": {"history": 4.0, "nature": 10.0, "culture": 3.0, "adventure": 10.0, "food": 2.0, "shopping": 2.0, "architecture": 2.0}
        },
        {
            "dest": "Manali", "cat": "Adventure", "name": "Solang Valley",
            "desc": "A breathtaking valley famous for paragliding, skiing, and zorbing activities.",
            "hist": "Gained popularity as an adventure hub in the late 20th century.", "cult": "A top destination for winter sports in North India.",
            "lat": 32.3193, "lng": 77.1527, "img": "https://images.unsplash.com/photo-1596491327946-b5040b9b08b4",
            "rating": 4.7, "price": 2, "dur": 240,
            "fs": {"history": 1.0, "nature": 10.0, "culture": 2.0, "adventure": 10.0, "food": 3.0, "shopping": 3.0, "architecture": 1.0}
        },
        # Amritsar Food Places
        {
            "dest": "Amritsar", "cat": "Food", "name": "Kesar Da Dhaba",
            "desc": "One of the oldest and most iconic dhabas in Amritsar, famous for its legendary Dal Makhani and creamy Paneer.",
            "hist": "Established in 1916, this dhaba has been serving authentic Punjabi food for over a century.", "cult": "An institution of Punjabi food culture that every food lover must visit.",
            "lat": 31.6286, "lng": 74.8763, "img": "https://images.unsplash.com/photo-1585937421612-70a008356fbe",
            "rating": 4.8, "price": 1, "dur": 90,
            "fs": {"history": 7.0, "nature": 1.0, "culture": 8.0, "adventure": 0.0, "food": 10.0, "shopping": 2.0, "architecture": 2.0}
        },
        {
            "dest": "Amritsar", "cat": "Food", "name": "Golden Temple Langar",
            "desc": "The world's largest free kitchen, serving over 100,000 people daily with simple, soulful Punjabi meals.",
            "hist": "Tradition of langar (community kitchen) started by Guru Nanak Dev Ji in the 15th century.", "cult": "A living symbol of equality, selfless service, and community in Sikhism.",
            "lat": 31.6200, "lng": 74.8765, "img": "https://images.unsplash.com/photo-1588083949404-c4f1ed1323b3",
            "rating": 5.0, "price": 1, "dur": 120,
            "fs": {"history": 10.0, "nature": 2.0, "culture": 10.0, "adventure": 0.0, "food": 10.0, "shopping": 1.0, "architecture": 8.0}
        },
        # Kolkata Food Places
        {
            "dest": "Kolkata", "cat": "Food", "name": "Puchka Trail at Park Street",
            "desc": "Kolkata's iconic street food experience — tangy tamarind water in crispy hollow puris, unlike any other city's version.",
            "hist": "Puchka has been a staple of Kolkata street food for over 200 years.", "cult": "An inseparable part of Kolkata's identity and cultural fabric.",
            "lat": 22.5526, "lng": 88.3518, "img": "https://images.unsplash.com/photo-1606491956689-2ea866880c84",
            "rating": 4.7, "price": 1, "dur": 60,
            "fs": {"history": 5.0, "nature": 1.0, "culture": 9.0, "adventure": 1.0, "food": 10.0, "shopping": 4.0, "architecture": 2.0}
        },
        {
            "dest": "Kolkata", "cat": "Food", "name": "Flury's — The Swiss Confectionery",
            "desc": "A legendary Kolkata landmark since 1927, famous for its pastries, sandwiches and afternoon English tea.",
            "hist": "Founded by J. Flury, a Swiss confectioner, in 1927 on Park Street.", "cult": "A colonial-era treasure and an integral part of Kolkata's nostalgic charm.",
            "lat": 22.5532, "lng": 88.3520, "img": "https://images.unsplash.com/photo-1555396273-367ea4eb4db5",
            "rating": 4.6, "price": 3, "dur": 90,
            "fs": {"history": 9.0, "nature": 1.0, "culture": 8.0, "adventure": 0.0, "food": 10.0, "shopping": 3.0, "architecture": 7.0}
        },
        # Hyderabad Food Places
        {
            "dest": "Hyderabad", "cat": "Food", "name": "Paradise Biryani",
            "desc": "Home of the world-famous Hyderabadi Dum Biryani, a fragrant rice dish layered with marinated meat and slow-cooked to perfection.",
            "hist": "Paradise Restaurant established in 1953, bringing Nizam's royal biryani recipe to the masses.", "cult": "The most iconic biryani restaurant in India, a must-eat dish for any visitor.",
            "lat": 17.4375, "lng": 78.4482, "img": "https://images.unsplash.com/photo-1574653853027-5382a3d23a15",
            "rating": 4.8, "price": 2, "dur": 90,
            "fs": {"history": 7.0, "nature": 1.0, "culture": 9.0, "adventure": 0.0, "food": 10.0, "shopping": 2.0, "architecture": 4.0}
        },
        {
            "dest": "Hyderabad", "cat": "Food", "name": "Charminar Haleem Bazaar",
            "desc": "The bustling food market around Charminar, famous for slow-cooked Haleem and authentic Hyderabadi street snacks.",
            "hist": "The Charminar area has been a food hub since the Nizams era in the 17th century.", "cult": "One of the best places in India to experience authentic Nizami cuisine.",
            "lat": 17.3616, "lng": 78.4747, "img": "https://images.unsplash.com/photo-1504674900247-0877df9cc836",
            "rating": 4.7, "price": 1, "dur": 120,
            "fs": {"history": 8.0, "nature": 1.0, "culture": 10.0, "adventure": 0.0, "food": 10.0, "shopping": 7.0, "architecture": 8.0}
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
    # 5. Add Guides
    print("Adding Guides...")
    await db.guides.delete_many({})
    guides = [
        {
            "name": "Ravi Kumar",
            "languages": ["English", "Hindi"],
            "rating": 4.9,
            "reviews_count": 120,
            "hourly_rate": 15.0,
            "bio": "Certified historian with 10 years of experience guiding tours in Agra and New Delhi. Specializes in Mughal architecture.",
            "verified": True,
            "image_url": "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d",
            "location": "Agra, India"
        },
        {
            "name": "Priya Sharma",
            "languages": ["English", "Hindi", "French"],
            "rating": 4.8,
            "reviews_count": 85,
            "hourly_rate": 18.0,
            "bio": "Food and culture enthusiast. I will take you to the best hidden culinary spots in New Delhi!",
            "verified": True,
            "image_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb",
            "location": "New Delhi, India"
        },
        {
            "name": "Amit Patel",
            "languages": ["English", "Gujarati"],
            "rating": 4.6,
            "reviews_count": 45,
            "hourly_rate": 12.0,
            "bio": "Expert in nature and wildlife. Let's explore the hidden natural beauty of India.",
            "verified": False,
            "image_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d",
            "location": "Mumbai, India"
        }
    ]
    for g in guides:
        from app.models.guide import GuideInDB
        await db.guides.insert_one(GuideInDB(**g).dict())
        
    print("Done seeding!")

if __name__ == "__main__":
    asyncio.run(seed())
