import asyncio
import random
import os
from dotenv import load_dotenv

# Load env variables before getting the db client so MONGO_URI is picked up
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from app.core.database import get_db
from app.models.guide import GuideInDB

cities = [
    "New Delhi", "Mumbai", "Bengaluru", "Chennai", "Kolkata", 
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

async def seed_guides():
    db = get_db()
    
    print("Fetching existing guides...")
    existing_guides = await db.guides.find({}).to_list(length=None)
    
    if len(existing_guides) == 0:
        print("No guides found. Please run the original seed script first.")
        return

    print(f"Found {len(existing_guides)} existing guides. Updating them...")
    
    # We need to guarantee exactly 197 guides if there are currently 197.
    # The existing guides already have 'name', 'city', 'location' etc.
    # We will update them with deterministic images and set is_lgbtq.
    
    for idx, guide in enumerate(existing_guides):
        i = idx + 1
        
        # Every 6th person is LGBTQ, ensuring a reasonable number
        is_lgbtq = (i % 6 == 0)
        
        image_path = f"/images/guides/guide-{i:03d}.webp"
        
        update_fields = {
            "image_url": image_path,
            "is_lgbtq": is_lgbtq
        }
        
        await db.guides.update_one(
            {"_id": guide["_id"]},
            {"$set": update_fields}
        )
            
    print(f"Successfully updated {len(existing_guides)} guides!")

if __name__ == "__main__":
    asyncio.run(seed_guides())
