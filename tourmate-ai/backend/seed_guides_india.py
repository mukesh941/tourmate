import asyncio
import random
from app.core.database import get_db
from app.models.guide import GuideInDB

cities = [
    "New Delhi", "Mumbai", "Bangalore", "Chennai", "Kolkata", 
    "Hyderabad", "Pune", "Ahmedabad", "Jaipur", "Goa", 
    "Agra", "Varanasi", "Amritsar", "Chandigarh", "Srinagar",
    "Leh", "Khajuraho", "Gwalior", "Puri", "Guwahati",
    "Manali", "Nainital", "Aurangabad", "Port Blair", "Rishikesh",
    "Kochi", "Mysuru", "Udaipur", "Jodhpur", "Jaisalmer"
]

first_names = [
    "Aarav", "Vihaan", "Aditya", "Arjun", "Sai", "Rahul", "Amit", "Vikram", "Raj", "Ravi",
    "Diya", "Aanya", "Priya", "Neha", "Pooja", "Anjali", "Sneha", "Kavya", "Riya", "Meera",
    "Mohammed", "Ali", "Hassan", "Fatima", "Aisha", "Zoya", "Ibrahim", "Tariq", "Omar", "Sara",
    "Gurpreet", "Manpreet", "Harpreet", "Amandeep", "Sandeep", "Navdeep"
]

last_names = [
    "Sharma", "Patel", "Kumar", "Singh", "Das", "Bose", "Chatterjee", "Sengupta", "Nair", 
    "Menon", "Reddy", "Rao", "Gowda", "Iyer", "Khan", "Ahmed", "Syed", "Sheikh",
    "Kaur", "Gill", "Sandhu", "Joshi", "Desai", "Mehta", "Chauhan", "Rajput"
]

languages_pool = ["English", "Hindi", "Marathi", "Gujarati", "Tamil", "Telugu", "Kannada", "Malayalam", "Bengali", "Punjabi", "French", "Spanish", "German", "Japanese"]

bios = [
    "Certified local historian with a passion for uncovering hidden gems.",
    "Food lover and culture enthusiast. I will take you to the best culinary spots!",
    "Expert in nature and wildlife. Let's explore the beautiful outdoors together.",
    "Specializes in ancient architecture and heritage walks.",
    "Professional photographer who knows all the most photogenic locations.",
    "Born and raised here, I know the streets like the back of my hand.",
    "Adventurer at heart, I lead exciting and off-the-beaten-path tours.",
    "Friendly and accommodating, perfect for families and senior travelers.",
    "Fluent in multiple languages to make you feel right at home.",
    "Art and museum expert. Prepare to dive deep into local history."
]

portraits = [
    "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d",
    "https://images.unsplash.com/photo-1534528741775-53994a69daeb",
    "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d",
    "https://images.unsplash.com/photo-1494790108377-be9c29b29330",
    "https://images.unsplash.com/photo-1539571696357-5a69c17a67c6",
    "https://images.unsplash.com/photo-1517841905240-472988babdf9",
    "https://images.unsplash.com/photo-1500648767791-00dcc994a43e",
    "https://images.unsplash.com/photo-1544005313-94ddf0286df2",
    "https://images.unsplash.com/photo-1521119989659-a83eee488004",
    "https://images.unsplash.com/photo-1531427186611-ecfd6d936c79",
    "https://images.unsplash.com/photo-1524504388940-b1c1722653e1",
    "https://images.unsplash.com/photo-1501196354995-cbb51c65aaea",
    "https://images.unsplash.com/photo-1488161628813-04466f872507",
    "https://images.unsplash.com/photo-1529626455594-4ff0802cfb7e",
    "https://images.unsplash.com/photo-1531123897727-8f129e1688ce"
]

async def seed_guides():
    db = get_db()
    
    print("Clearing existing guides...")
    await db.guides.delete_many({})
    
    guides_to_add = []
    
    # Generate exactly 1 guide per city
    for city in cities:
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        
        # Everyone speaks English, plus 1-2 local languages
        langs = ["English"]
        extra_langs = random.sample(languages_pool[1:], random.randint(1, 2))
        langs.extend(extra_langs)
        
        guide = {
            "name": name,
            "languages": list(set(langs)),
            "rating": round(random.uniform(4.5, 5.0), 1),
            "reviews_count": random.randint(50, 500),
            "hourly_rate": round(random.uniform(500.0, 3000.0), 0),
            "bio": random.choice(bios),
            "verified": True, # All verified
            "image_url": random.choice(portraits),
            "location": f"{city}, India"
        }
        guides_to_add.append(GuideInDB(**guide).dict())
            
    print(f"Adding {len(guides_to_add)} guides across India to the database...")
    
    if guides_to_add:
        await db.guides.insert_many(guides_to_add)
        
    print("Successfully seeded guides!")

if __name__ == "__main__":
    asyncio.run(seed_guides())
